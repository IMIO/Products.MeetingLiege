# -*- coding: utf-8 -*-

from imio.history.utils import add_event_to_history
from OFS.ObjectManager import BeforeDeleteException
from plone import api
from Products.MeetingLiege.config import FINANCE_ADVICE_HISTORIZE_COMMENTS
from Products.MeetingLiege.config import ITEM_MAIN_INFOS_HISTORY
from Products.PloneMeeting.browser.itemchangeorder import _is_integer
from Products.PloneMeeting.config import NOT_GIVEN_ADVICE_VALUE
from Products.PloneMeeting.config import PloneMeetingError
from Products.PloneMeeting.utils import _storedItemNumber_to_itemNumber
from Products.PloneMeeting.utils import main_item_data


__author__ = """Gauthier BASTIEN <gauthier.bastien@imio.be>"""
__docformat__ = 'plaintext'


def _everyAdvicesAreGivenFor(item):
    '''Every advices are considered given on an item if no more
       hidden_during_redaction and created.'''
    tool = api.portal.get_tool('portal_plonemeeting')
    finance_group_uids = tool.finance_group_uids()
    for adviceUid, adviceInfos in item.adviceIndex.items():
        if adviceUid not in finance_group_uids and \
           adviceInfos['type'] in (NOT_GIVEN_ADVICE_VALUE, 'asked_again') or \
           adviceInfos['hidden_during_redaction'] is True:
            return False
    return True


def _sendWaitingAdvicesItemBackInWFIfNecessary(item):
    '''Check if we need to send the item backToItemCreated
       or backToProposedToInternalReviewer.'''
    itemState = item.query_state()
    if itemState in ['itemcreated_waiting_advices',
                     'proposed_to_internal_reviewer_waiting_advices',
                     # MeetingItemBourgmestre
                     'proposed_to_director_waiting_advices'] and \
       _everyAdvicesAreGivenFor(item):
        if itemState == 'itemcreated_waiting_advices':
            transition = 'backTo_itemcreated_from_waiting_advices'
        elif itemState == 'proposed_to_internal_reviewer_waiting_advices':
            transition = 'backTo_proposed_to_internal_reviewer_from_waiting_advices'
        else:
            transition = 'backTo_proposed_to_director_from_waiting_advices'
        item.REQUEST.set('everyAdvicesAreGiven', True)
        # use actionspanel so we are redirected to viewable url
        actionsPanel = item.restrictedTraverse('@@actions_panel')
        redirectTo = actionsPanel.triggerTransition(transition=transition,
                                                    comment='item_wf_changed_every_advices_given',
                                                    redirect=True)
        item.REQUEST.set('everyAdvicesAreGiven', False)
        if redirectTo:
            return item.REQUEST.RESPONSE.redirect(redirectTo)


def onItemLocalRolesUpdated(item, event):
    """Called after localRoles have been updated on the item.
       Update local_roles regarding :
       - access of finance advisers;
       - finance advisers able to add decision annexes on decided items."""

    # warning, it is necessary that updateFinanceAdvisersAccess is called last!
    item.adapted().updateFinanceAdvisersAccess(old_local_roles=event.old_local_roles)

    # give ability to finance adviser to add decision annexes
    tool = api.portal.get_tool('portal_plonemeeting')
    cfg = tool.getMeetingConfig(item)
    org_uid = item.adapted().getFinanceGroupUIDForItem()
    if org_uid and item.query_state() in cfg.getItemDecidedStates():
        adviserGroupId = '%s_advisers' % org_uid
        # if item is decided, we give the _advisers, the 'Contributor'
        # role on the item so he is able to add decision annexes
        item.manage_addLocalRoles(adviserGroupId, ('Contributor', ))


def onAdviceAdded(advice, event):
    '''Called when a meetingadvice is added.'''
    item = advice.getParentNode()
    _sendWaitingAdvicesItemBackInWFIfNecessary(item)


def onAdviceModified(advice, event):
    '''Called when a meetingadvice is edited.'''
    item = advice.getParentNode()
    _sendWaitingAdvicesItemBackInWFIfNecessary(item)


def onAdviceAfterTransition(advice, event):
    '''Called whenever a transition has been fired on an advice.'''
    # pass if we are pasting items as advices are not kept
    if advice != event.object or advice.REQUEST.get('currentlyPastingItems', False):
        return

    # manage finance workflow, just consider relevant transitions
    # if it is not a finance wf transition, return
    tool = api.portal.get_tool('portal_plonemeeting')
    finance_group_uids = tool.finance_group_uids()
    if advice.advice_group not in finance_group_uids:
        return

    item = advice.getParentNode()
    itemState = item.query_state()
    tool = api.portal.get_tool('portal_plonemeeting')
    cfg = tool.getMeetingConfig(item)

    # when the finance advice state change, we have to reinitialize
    # item.takenOverBy to nothing if advice is not at the finance controller state
    if event.new_state.id not in ['proposed_to_financial_controller']:
        # we do not use the mutator setTakenOverBy because it
        # clean takenOverByInfos and we need it to be kept if
        # advice come back to controler
        item.getField('takenOverBy').set(item, '', **{})
    else:
        # if advice review_state is back to financial controller
        # set historized taker for item state
        wf_state = "%s__wfstate__%s" % (cfg.getItemWorkflow(), itemState)
        item.setHistorizedTakenOverBy(wf_state)
    item.reindexObject(idxs=['getTakenOverBy', ])

    wfTool = api.portal.get_tool('portal_workflow')
    oldStateId = event.old_state.id
    newStateId = event.new_state.id

    # initial_state or going back from 'advice_given', we set automatically
    # advice_hide_during_redaction to True
    # we do not use MeetingConfig.defaultAdviceHiddenDuringRedaction because
    # when advice is "asked_again", it is hidden which is not useable
    # see https://support.imio.be/browse/PM-3883
    if not event.transition or \
       (newStateId == 'proposed_to_financial_controller' and oldStateId == 'advice_given'):
        advice.advice_hide_during_redaction = True

    if newStateId == 'financial_advice_signed':
        # historize given advice
        advice.historize_if_relevant(FINANCE_ADVICE_HISTORIZE_COMMENTS)

        # final state of the wf, make sure advice is no more hidden during redaction
        # XXX managed by ToolPloneMeeting.advisersConfig.show_advice_on_final_wf_transition
        # advice.advice_hide_during_redaction = False
        # if item was still in state 'proposed_to_finance_waiting_advices', it is automatically validated
        # and a specific message is added to the wf history regarding this
        # validate or send the item back to internal reviewer depending on advice_type
        if itemState == 'proposed_to_finance_waiting_advices':
            if advice.advice_type in ('positive_finance',
                                      'positive_with_remarks_finance',
                                      'not_required_finance'):
                item.REQUEST.set('mayValidate', True)
                wfTool.doActionFor(
                    item, 'validate', comment='item_wf_changed_finance_advice_positive')
                item.REQUEST.set('mayValidate', False)
            else:
                # if advice is negative, we automatically send the item back to the internal reviewer
                wfTool.doActionFor(
                    item,
                    'backTo_proposed_to_internal_reviewer_from_waiting_advices',
                    comment='item_wf_changed_finance_advice_negative')


def onAdvicesUpdated(item, event):
    '''
      When advices have been updated, we need to check that finance advice marked as 'advice_editable' = True
      are really editable, this could not be the case if the advice is signed.
      In a second step, if item is 'backTo_proposed_to_internal_reviewer_from_waiting_advices',
      we need to reinitialize finance advice delay.
    '''
    for org_uid, adviceInfo in item.adviceIndex.items():
        # special behaviour for finance advice
        if not org_uid == item.adapted().getFinanceGroupUIDForItem():
            continue

        # when a finance has accessed an item, he will always be able to access it after
        # if not adviceInfo['item_viewable_by_advisers'] and \
        #    getLastWFAction(item, 'wait_advices_from_proposed_to_director'):
        #     # give access to the item to the finance group
        #     item.manage_addLocalRoles('%s_advisers' % org_uid, (READER_USECASES['advices'],))
        #     item.adviceIndex[org_uid]['item_viewable_by_advisers'] = True
        # the advice delay is really started when item completeness is 'complete' or 'evaluation_not_required'
        # until then, we do not let the delay start
        if not item.getCompleteness() in ('completeness_complete', 'completeness_evaluation_not_required'):
            adviceInfo['delay_started_on'] = None
            adviceInfo['advice_addable'] = False
            adviceInfo['advice_editable'] = False
            adviceInfo['delay_infos'] = item.getDelayInfosForAdvice(org_uid)

        # when a finance advice is just timed out, we will validate the item
        # so MeetingManagers receive the item and do what necessary
        if adviceInfo['delay_infos']['delay_status'] == 'timed_out' and \
           'delay_infos' in event.old_adviceIndex[org_uid] and not \
           event.old_adviceIndex[org_uid]['delay_infos']['delay_status'] == 'timed_out':
            if item.query_state() == 'proposed_to_finance_waiting_advices':
                wfTool = api.portal.get_tool('portal_workflow')
                item.REQUEST.set('mayValidate', True)
                wfTool.doActionFor(item, 'validate', comment='item_wf_changed_finance_advice_timed_out')
                item.REQUEST.set('mayValidate', False)

    # when item is 'backTo_proposed_to_internal_reviewer_from_waiting_advices',
    # reinitialize advice delay
    if event.triggered_by_transition == 'backTo_proposed_to_internal_reviewer_from_waiting_advices':
        financeGroupId = item.adapted().getFinanceGroupUIDForItem()
        if financeGroupId in item.adviceIndex:
            adviceInfo = item.adviceIndex[financeGroupId]
            adviceInfo['delay_started_on'] = None
            adviceInfo['advice_addable'] = False
            adviceInfo['delay_infos'] = item.getDelayInfosForAdvice(financeGroupId)


def onItemDuplicated(original, event):
    '''When an item is sent to the Council, we need to initialize
       title and privacy from what was defined on the college item.
       More over we manage here the fact that in some cases, decision
       annexes are not kept.'''
    newItem = event.newItem

    # need to do this here because ItemLocalRolesUpdated event is called too soon...
    # warning, it is necessary that updateFinanceAdvisersAccess is called last!
    newItem.adapted().updateFinanceAdvisersAccess()

    if original.portal_type == 'MeetingItemCouncil' and \
       newItem.portal_type == 'MeetingItemCollege':
        # an item Council is sent back to College, enable the 'otherMeetingConfigsClonableTo'
        newItem.setOtherMeetingConfigsClonableTo(('meeting-config-council', ))
        # keep same privacy
        if original.getPrivacy() == 'secret':
            newItem.setOtherMeetingConfigsClonableToPrivacy(('meeting-config-council', ))
        # restore labelForCouncil in otherMeetingConfigsClonableToFieldLabelForCouncil
        newItem.setOtherMeetingConfigsClonableToFieldLabelForCouncil(original.getRawLabelForCouncil())


def onItemAfterTransition(item, event):
    '''Called after the transition event called by default in PloneMeeting.
       Here, we are sure that code done in the onItemTransition event is finished.'''

    # if it is an item Council in state 'returned', validate the issued College item
    if item.portal_type == 'MeetingItemCouncil' and event.new_state.id == 'returned':
        collegeItem = item.getItemClonedToOtherMC('meeting-config-college')
        wfTool = api.portal.get_tool('portal_workflow')
        item.REQUEST.set('mayValidate', True)
        wfTool.doActionFor(collegeItem, 'validate')
        item.REQUEST.set('mayValidate', False)

    # save base item informations in the ITEM_MAIN_INFOS_HISTORY
    # if new state is "proposed_to_cabinet_manager"
    if item.portal_type == 'MeetingItemBourgmestre' and \
       event.old_state.id == 'proposed_to_general_manager' and \
       event.new_state.id == 'proposed_to_cabinet_manager':
        data = main_item_data(item)
        add_event_to_history(
            item,
            ITEM_MAIN_INFOS_HISTORY,
            action='historize_main_infos',
            comments='historize_main_infos_comments',
            extra_infos={'historized_data': data})


def onItemListTypeChanged(item, event):
    '''Called when MeetingItem.listType is changed :
       - if going to 'addendum', adapt itemNumber if not already a subnumber;
       - if going back from 'addendum', adapt itemNumbe if not already an interger.'''
    # going to 'addendum'
    if item.getListType() == u'addendum' and _is_integer(item.getItemNumber()):
        view = item.restrictedTraverse('@@change-item-order')
        # we will set previous number + 1 so get previous item
        meeting = item.getMeeting()
        items = meeting.get_items(ordered=True, the_objects=False)
        itemUID = item.UID()
        previous = None
        for item in items:
            if item.UID == itemUID:
                break
            previous = item
        # first item of the meeting can not be set to 'addendum'
        if not previous:
            raise PloneMeetingError("First item of the meeting may not be set to 'Addendum' !")
        newNumber = _storedItemNumber_to_itemNumber(
            previous._unrestrictedGetObject().getItemNumber() + 1)
        view('number', newNumber)
    # going back from 'addendum'
    elif event.old_listType == u'addendum' and not _is_integer(item.getItemNumber()):
        view = item.restrictedTraverse('@@change-item-order')
        # we will use next integer
        nextInteger = (item.getItemNumber() + 100) / 100
        view('number', str(nextInteger))

    # add a value in the REQUEST to specify that update_item_references is needed
    item.REQUEST.set('need_Meeting_update_item_references', True)
