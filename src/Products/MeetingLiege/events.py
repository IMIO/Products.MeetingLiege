# -*- coding: utf-8 -*-
#
# File: events.py
#
# Copyright (c) 2014 by Imio.be
#
# GNU General Public License (GPL)
#

__author__ = """Gauthier BASTIEN <gauthier.bastien@imio.be>"""
__docformat__ = 'plaintext'

from OFS.ObjectManager import BeforeDeleteException
from plone import api
from imio.actionspanel.interfaces import IContentDeletable
from imio.helpers.cache import cleanVocabularyCacheFor
from Products.PloneMeeting import PloneMeetingError
from Products.PloneMeeting.browser.itemchangeorder import _is_integer
from Products.PloneMeeting.config import NOT_GIVEN_ADVICE_VALUE
from Products.PloneMeeting.config import READER_USECASES
from Products.PloneMeeting.interfaces import IAnnexable
from Products.PloneMeeting.utils import getLastEvent
from Products.PloneMeeting.utils import _storedItemNumber_to_itemNumber
from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.config import FINANCE_ADVICE_HISTORIZE_COMMENTS


def _everyAdvicesAreGivenFor(item):
    '''Every advices are considered given on an item if no more
       hidden_during_redaction and created.'''
    for adviceId, adviceInfos in item.adviceIndex.items():
        if not adviceId in FINANCE_GROUP_IDS and \
           adviceInfos['type'] in (NOT_GIVEN_ADVICE_VALUE, 'asked_again') or \
           adviceInfos['hidden_during_redaction'] is True:
            return False
    return True


def _sendItemBackInWFIfNecessary(item):
    '''Check if we need to send the item backToItemCreated
       or backToProposedToInternalReviewer.'''
    itemState = item.queryState()
    if itemState in ['itemcreated_waiting_advices',
                     'proposed_to_internal_reviewer_waiting_advices'] and \
       _everyAdvicesAreGivenFor(item):
        if itemState == 'itemcreated_waiting_advices':
            transition = 'backToItemCreated'
        else:
            transition = 'backToProposedToInternalReviewer'
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
       - the matterOfGroups;
       - access of finance advisers."""
    item.adapted()._updateMatterOfGroupsLocalRoles()
    # warning, it is necessary that updateFinanceAdvisersAccess is called last!
    item.adapted().updateFinanceAdvisersAccess(old_local_roles=event.old_local_roles)


def onAdviceAdded(advice, event):
    '''Called when a meetingadvice is added.'''
    item = advice.getParentNode()
    _sendItemBackInWFIfNecessary(item)


def onAdviceModified(advice, event):
    '''Called when a meetingadvice is edited.'''
    item = advice.getParentNode()
    _sendItemBackInWFIfNecessary(item)


def onAdviceTransition(advice, event):
    '''Called whenever a transition has been fired on an advice.'''
    # pass if we are pasting items as advices are not kept
    if advice != event.object or advice.REQUEST.get('currentlyPastingItems', False):
        return

    # manage finance workflow, just consider relevant transitions
    # if it is not a finance wf transition, return
    if not advice.advice_group in FINANCE_GROUP_IDS:
        return

    item = advice.getParentNode()
    itemState = item.queryState()
    tool = api.portal.get_tool('portal_plonemeeting')
    cfg = tool.getMeetingConfig(item)
    adviserGroupId = '%s_advisers' % advice.advice_group
    stateToGroupSuffixMappings = {'proposed_to_financial_controller': 'financialcontrollers',
                                  'proposed_to_financial_reviewer': 'financialreviewers',
                                  'proposed_to_financial_manager': 'financialmanagers', }

    # when the finance advice state change, we have to reinitialize
    # item.takenOverBy to nothing if advice is not at the finance controller state
    if not event.new_state.id in ['advice_under_edit',
                                  'proposed_to_financial_controller']:
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

    # onAdviceTransition is called before onAdviceAdded...
    # so the advice_row_id is still not set wich is very bad because
    # when we updateAdvices, it does not find the advice_row_id and adviceIndex is wrong
    # so we call it here...
    if not advice.advice_row_id:
        advice._updateAdviceRowId()

    wfTool = api.portal.get_tool('portal_workflow')
    oldStateId = event.old_state.id
    newStateId = event.new_state.id

    if newStateId == 'financial_advice_signed':
        # historize given advice into a version
        advice.versionate_if_relevant(FINANCE_ADVICE_HISTORIZE_COMMENTS)

        # final state of the wf, make sure advice is no more hidden during redaction
        advice.advice_hide_during_redaction = False
        # if item was still in state 'proposed_to_finance', it is automatically validated
        # and a specific message is added to the wf history regarding this
        # validate or send the item back to director depending on advice_type
        if itemState == 'proposed_to_finance':
            if advice.advice_type in ('positive_finance', 'positive_with_remarks_finance', 'not_required_finance'):
                item.REQUEST.set('mayValidate', True)
                wfTool.doActionFor(item, 'validate', comment='item_wf_changed_finance_advice_positive')
                item.REQUEST.set('mayValidate', False)
            else:
                # if advice is negative, we automatically send the item back to the director
                item.REQUEST.set('mayBackToProposedToDirector', True)
                wfTool.doActionFor(item, 'backToProposedToDirector', comment='item_wf_changed_finance_advice_negative')
                item.REQUEST.set('mayBackToProposedToDirector', False)
        else:
            # we need to _updateAdvices so change to
            # 'advice_hide_during_redaction' is taken into account
            item.updateLocalRoles()

    # when going to an end state, aka a state where advice can not be edited anymore, we
    # give the 'MeetingFinanceEditor' to the _advisers finance group
    # so they have read access for the 'advice_substep_number' field, the workflow
    # will not give any permission to this role but we need the finance group to have this
    # role on the advice
    # nevertheless, we remove roles given to the localRoledGroupId
    if newStateId in ('advice_given', 'advice_under_edit', 'financial_advice_signed', ) and \
       not oldStateId in ('advice_given', 'advice_under_edit', 'financial_advice_signed', ):
        localRoledGroupId = '%s_%s' % (advice.advice_group,
                                       stateToGroupSuffixMappings[oldStateId])
        advice.manage_delLocalRoles((localRoledGroupId, adviserGroupId))
        if newStateId in ('advice_given', 'financial_advice_signed', ):
            advice.manage_addLocalRoles(adviserGroupId, ('MeetingFinanceEditor', 'Reader', ))
        return

    # in some corner case, we could be here and we are actually already updating advices,
    # this is the case if we validate an item and it triggers the fact that advice delay is exceeded
    # this should never be the case as advice delay should have been updated during nightly cron...
    # but if we are in a '_updateAdvices', do not _updateAdvices again...
    if not newStateId in stateToGroupSuffixMappings:
        if not item.REQUEST.get('currentlyUpdatingAdvice', False):
            item.updateLocalRoles()
        return

    # give 'Reader' role to every members of the _advisers and
    # give 'MeetingFinanceEditor' role to the relevant finance sub-group depending on new advice state
    # we use a specific 'MeetingFinanceEditor' role because the 'Editor' role is given to entire
    # _advisers group by default in PloneMeeting and it is used for non finance advices
    advice.manage_delLocalRoles((adviserGroupId, ))
    advice.manage_addLocalRoles(adviserGroupId, ('Reader', ))
    advice.manage_addLocalRoles('%s_%s' % (advice.advice_group, stateToGroupSuffixMappings[newStateId]),
                                ('MeetingFinanceEditor', ))
    # finally remove 'MeetingFinanceEditor' given in previous state except if it is initial_state
    if oldStateId in stateToGroupSuffixMappings and not oldStateId == newStateId:
        localRoledGroupId = '%s_%s' % (advice.advice_group,
                                       stateToGroupSuffixMappings[oldStateId])
        advice.manage_delLocalRoles((localRoledGroupId, ))

    # need to updateLocalRoles, and especially _updateAdvices to finish work :
    # timed_out advice is no more giveable
    item.updateLocalRoles()


def onAdvicesUpdated(item, event):
    '''
      When advices have been updated, we need to check that finance advice marked as 'advice_editable' = True
      are really editable, this could not be the case if the advice is signed.
      In a second step, if item is 'backToProposedToInternalReviewer', we need to reinitialize finance advice delay.
    '''
    for groupId, adviceInfo in item.adviceIndex.items():
        # special behaviour for finance advice
        if not groupId == item.adapted().getFinanceGroupIdsForItem():
            continue

        itemState = item.queryState()
        tool = api.portal.get_tool('portal_plonemeeting')
        cfg = tool.getMeetingConfig(item)
        adviserGroupId = '%s_advisers' % groupId

        # if item is decided, we need to give the _advisers, the 'MeetingFinanceEditor'
        # role on the item so he is able to add decision annexes
        if itemState in cfg.getItemDecidedStates():
            item.manage_addLocalRoles(adviserGroupId, ('MeetingFinanceEditor', ))
        else:
            localRoles = item.__ac_local_roles__.get(adviserGroupId, ())
            if 'MeetingFinanceEditor' in localRoles:
                localRoles.remove('MeetingFinanceEditor')
                item.__ac_local_roles__[adviserGroupId] = localRoles

        # double check if it is really editable...
        # to be editable, the advice has to be in an editable wf state
        if adviceInfo['advice_editable']:
            advice = getattr(item, adviceInfo['advice_id'])
            if not advice.queryState() in ('proposed_to_financial_controller',
                                           'proposed_to_financial_reviewer',
                                           'proposed_to_financial_manager'):
                # advice is no more editable, adapt adviceIndex
                item.adviceIndex[groupId]['advice_editable'] = False
        # when a finance has accessed an item, he will always be able to access it after
        if not adviceInfo['item_viewable_by_advisers'] and \
           getLastEvent(item, 'proposeToFinance'):
            # give access to the item to the finance group
            item.manage_addLocalRoles('%s_advisers' % groupId, (READER_USECASES['advices'],))
            item.adviceIndex[groupId]['item_viewable_by_advisers'] = True
        # the advice delay is really started when item completeness is 'complete' or 'evaluation_not_required'
        # until then, we do not let the delay start
        if not item.getCompleteness() in ('completeness_complete', 'completeness_evaluation_not_required'):
            adviceInfo['delay_started_on'] = None
            adviceInfo['advice_addable'] = False
            adviceInfo['advice_editable'] = False
            adviceInfo['delay_infos'] = item.getDelayInfosForAdvice(groupId)

        # when a finance advice is just timed out, we will validate the item
        # so MeetingManagers receive the item and do what necessary
        if adviceInfo['delay_infos']['delay_status'] == 'timed_out' and \
           'delay_infos' in event.old_adviceIndex[groupId] and not \
           event.old_adviceIndex[groupId]['delay_infos']['delay_status'] == 'timed_out':
            if item.queryState() == 'proposed_to_finance':
                wfTool = api.portal.get_tool('portal_workflow')
                item.REQUEST.set('mayValidate', True)
                wfTool.doActionFor(item, 'validate', comment='item_wf_changed_finance_advice_timed_out')
                item.REQUEST.set('mayValidate', False)

    # when item is 'backToProposedToInternalReviewer', reinitialize advice delay
    if event.triggered_by_transition == 'backToProposedToInternalReviewer':
        financeGroupId = item.adapted().getFinanceGroupIdsForItem()
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
    newItem.adapted()._updateMatterOfGroupsLocalRoles()
    newItem.adapted().updateFinanceAdvisersAccess()

    if original.portal_type == 'MeetingItemCollege' and newItem.portal_type == 'MeetingItemCouncil':
        # we just sent an item from college to council
        newItem.setPrivacy(original.getPrivacyForCouncil())

    if original.portal_type == 'MeetingItemCouncil' and newItem.portal_type == 'MeetingItemCollege':
        # an item Council is sent back to College, enable the 'otherMeetingConfigsClonableTo'
        newItem.setOtherMeetingConfigsClonableTo(('meeting-config-council', ))
        newItem.reindexObject(idxs=['sentToInfos'])

    # make sure we do not keep decision annexes
    decisionAnnexes = IAnnexable(newItem).getAnnexes(relatedTo='item_decision')
    # if item is sent to Council, user may not delete annexes...
    # in this case, we simply pass because it is supposed not possible to have that
    # kind of annex on an item that is sent to council, and moreover, the item in the council
    # is only editable by MeetingManagers
    if decisionAnnexes and IContentDeletable(newItem).mayDelete():
        toDelete = [annex.getId() for annex in decisionAnnexes]
        newItem.manage_delObjects(ids=toDelete)


def onItemAfterTransition(item, event):
    '''Called after the transition event called by default in PloneMeeting.
       Here, we are sure that code done in the onItemTransition event is finished.'''

    # if it is an item Council in state 'returned', validate the issued College item
    if item.portal_type == 'MeetingItemCouncil' and item.queryState() == 'returned':
        collegeItem = item.getItemClonedToOtherMC('meeting-config-college')
        wfTool = api.portal.get_tool('portal_workflow')
        item.REQUEST.set('mayValidate', True)
        wfTool.doActionFor(collegeItem, 'validate')
        item.REQUEST.set('mayValidate', False)


def onCategoryRemoved(category, event):
    '''Called when a MeetingCategory is removed.'''
    # clean cache for "Products.MeetingLiege.vocabularies.groupsofmattervocabulary"
    cleanVocabularyCacheFor("Products.MeetingLiege.vocabularies.groupsofmattervocabulary")


def onGroupWillBeRemoved(group, event):
    '''Checks if the current meetingGroup can be deleted:
      - it can not be used in MeetingConfig.archivingRefs;
      - it can not be used in MeetingCategory.groupsOfMatter.'''
    if event.object.meta_type == 'Plone Site' or group._at_creation_flag:
        return

    tool = api.portal.get_tool('portal_plonemeeting')
    groupId = group.getId()
    for mc in tool.objectValues('MeetingConfig'):
        # The meetingGroup can be used in archivingRefs.
        for archivinfRef in mc.getArchivingRefs():
            if groupId in archivinfRef['restrict_to_groups']:
                raise BeforeDeleteException("can_not_delete_meetinggroup_archivingrefs")

        # The meetingGroup can be used in a category.groupsOfMatter.
        for category in mc.categories.objectValues('MeetingCategory'):
            if groupId in category.getGroupsOfMatter():
                raise BeforeDeleteException("can_not_delete_meetinggroup_groupsofmatter")


def onItemListTypeChanged(item, event):
    '''Called when MeetingItem.listType is changed :
       - if going to 'addendum', adapt itemNumber if not already a subnumber;
       - if going back from 'addendum', adapt itemNumbe if not already an interger.'''
    # going to 'addendum'
    if item.getListType() == u'addendum' and _is_integer(item.getItemNumber()):
        view = item.restrictedTraverse('@@change-item-order')
        # we will set previous number + 1 so get previous item
        meeting = item.getMeeting()
        items = meeting.getItems(ordered=True, useCatalog=True)
        itemUID = item.UID()
        previous = None
        for item in items:
            if item.UID == itemUID:
                break
            previous = item
        # first item of the meeting can not be set to 'addendum'
        if not previous:
            raise PloneMeetingError("First item of the meeting may not be set to 'Addendum' !")
        newNumber = _storedItemNumber_to_itemNumber(previous.getItemNumber + 1)
        view('number', newNumber)
    # going back from 'addendum'
    elif event.old_listType == u'addendum' and not _is_integer(item.getItemNumber()):
        view = item.restrictedTraverse('@@change-item-order')
        # we will use next integer
        nextInteger = (item.getItemNumber() + 100) / 100
        view('number', str(nextInteger))
