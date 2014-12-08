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

from Products.CMFCore.utils import getToolByName
from Products.PloneMeeting.config import READER_USECASES
from Products.PloneMeeting.utils import getLastEvent
from Products.MeetingLiege.config import FINANCE_GROUP_IDS


def onAdviceTransition(advice, event):
    '''Called whenever a transition has been fired on an advice.'''
    # pass if we are pasting items as advices are not kept
    if advice != event.object or advice.REQUEST.get('currentlyPastingItems', False):
        return

    # manage finance workflow, just consider relevant transitions
    # if it is not a finance wf transition, return
    if not advice.advice_group in FINANCE_GROUP_IDS:
        return

    # when the finance advice state change, we have to reinitialize
    # item.takenOverBy to nothing...
    item = advice.getParentNode()
    item.setTakenOverBy('')
    item.reindexObject(idxs=['getTakenOverBy', ])

    # onAdviceTransition is called before onAdviceAdded...
    # so the advice_row_id is still not set wich is very bad because
    # when we updateAdvices, it does not find the advice_row_id and adviceIndex is wrong
    # so we call it here...
    if not advice.advice_row_id:
        advice._updateAdviceRowId()

    wfTool = getToolByName(advice, 'portal_workflow')
    oldStateId = event.old_state.id
    newStateId = event.new_state.id

    # initial_state or going back from 'advice_given', we set automatically the state
    # to 'proposed_to_financial_controller', advice can never be in 'advice_under_edit'
    if not event.transition or \
       newStateId == 'advice_under_edit' and oldStateId == 'advice_given':
        # activate transition, check guard_expr
        advice.REQUEST.set('mayProposeToFinancialController', True)
        wfTool.doActionFor(advice, 'proposeToFinancialController')
        # hide the advice
        advice.advice_hide_during_redaction = True
        advice.REQUEST.set('mayProposeToFinancialController', False)
        return

    adviserGroupId = '%s_advisers' % advice.advice_group
    stateToGroupSuffixMappings = {'proposed_to_financial_controller': 'financialcontrollers',
                                  'proposed_to_financial_reviewer': 'financialreviewers',
                                  'proposed_to_financial_manager': 'financialmanagers', }

    if newStateId == 'financial_advice_signed':
        # final state of the wf, make sure advice is not more hidden during redaction
        advice.advice_hide_during_redaction = False
        # if item was still in state 'proposed_to_finance', it is automatically validated
        # and a specific message is added to the wf history regarding this
        # validate or send the item back to director depending on advice_type
        if item.queryState() == 'proposed_to_finance':
            if advice.advice_type in ('positive_finance', 'not_required_finance'):
                item.REQUEST.set('mayValidate', True)
                wfTool.doActionFor(item, 'validate', comment='item_wf_changed_finance_advice_positive')
                item.REQUEST.set('mayValidate', False)
            else:
                # if advice is negative, we automatically send the item back to the director
                item.REQUEST.set('mayBackToProposedToDirector', True)
                wfTool.doActionFor(item, 'backToProposedToDirector', comment='item_wf_changed_finance_advice_negative')
                item.REQUEST.set('mayBackToProposedToDirector', False)
        else:
            # we need to updateAdvices so change to
            # 'advice_hide_during_redaction' is taken into account
            item.updateAdvices()

    # when going to a end state, aka a state where advice can not be edited anymore, we
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
    # but if we are in a 'updateAdvices', do not updateAdvices again...
    if not newStateId in stateToGroupSuffixMappings:
        if not item.REQUEST.get('currentlyUpdatingAdvice', False):
            item.updateAdvices()
        return

    # give 'Reader' role to every members of the _advisers and
    # give 'MeetingFinanceEditor' role to the relevant finance sub-group depending on new advice state
    # we use a specific 'MeetingFinanceEditor' role because the 'Editor' role is given to entire
    # _advisers group by default in PloneMeeting and it is used for non finance advices
    # finally remove 'MeetingFinanceEditor' given in previous state
    advice.manage_delLocalRoles((adviserGroupId, ))
    advice.manage_addLocalRoles(adviserGroupId, ('Reader', ))
    advice.manage_addLocalRoles('%s_%s' % (advice.advice_group, stateToGroupSuffixMappings[newStateId]),
                                ('MeetingFinanceEditor', ))
    if oldStateId in stateToGroupSuffixMappings:
        localRoledGroupId = '%s_%s' % (advice.advice_group,
                                       stateToGroupSuffixMappings[oldStateId])
        advice.manage_delLocalRoles((localRoledGroupId, ))
    item.updateAdvices()


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
        if adviceInfo['delay_infos']['delay_status'] == 'timed_out' and not \
           event.old_adviceIndex[groupId]['delay_infos']['delay_status'] == 'timed_out':
            if item.queryState() == 'proposed_to_finance':
                wfTool = getToolByName(item, 'portal_workflow')
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
           title and privacy from what was defined on the college item.'''
        newItem = event.newItem
        if original.portal_type == 'MeetingItemCollege' and newItem.portal_type == 'MeetingItemCouncil':
            # we just sent an item from college to council
            newItem.setPrivacy(original.getPrivacyForCouncil())
