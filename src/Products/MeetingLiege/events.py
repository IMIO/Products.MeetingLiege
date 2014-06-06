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
from Products.MeetingLiege.config import FINANCE_GROUP_IDS


def onAdviceTransition(advice, event):
    '''Called whenever a transition has been fired on an advice.'''
    if advice != event.object:
        return

    # manage finance workflow, just consider relevant transitions
    # if it is not a finance wf transition, return
    if not advice.advice_group in FINANCE_GROUP_IDS:
        return

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
        advice.REQUEST.set('mayProposeToFinancialController', False)
        return

    adviserGroupId = '%s_advisers' % advice.advice_group
    stateToGroupSuffixMappings = {'proposed_to_financial_controller': 'financialcontrollers',
                                  'proposed_to_financial_reviewer': 'financialreviewers',
                                  'proposed_to_financial_manager': 'financialmanagers', }

    # manage specific transition action
    if newStateId == 'financial_advice_signed':
        # final state of the wf, make sure advice is not more hidden during redaction
        advice.advice_hide_during_redaction = False
        # if item was still in state 'proposed_to_finance', it is automatically validated
        # and a specific message is added to the wf history regarding this
        item = advice.getParentNode()
        # validate the item if not already the case
        if item.queryState() == 'proposed_to_finance':
            item.REQUEST.set('mayValidate', True)
            wfTool.doActionFor(item, 'validate', comment='item_wf_changed_finance_advice_positive')
            item.REQUEST.set('mayValidate', False)
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

    if not newStateId in stateToGroupSuffixMappings:
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


def onAdvicesUpdated(item, event):
    '''
      When advices have been updated, we need to check that finance advice marked as 'advice_editable' = True
      are really editable, this could not be the case if the advice is signed.
    '''
    for groupId, advice in item.adviceIndex.items():
        if groupId in FINANCE_GROUP_IDS and advice['advice_editable']:
            # double check if it is really editable...
            # to be editable, the advice has to be in an editable wf state
            advice = getattr(item, advice['advice_id'])
            if not advice.queryState() in ('proposed_to_financial_controller',
                                           'proposed_to_financial_reviewer',
                                           'proposed_to_financial_manager'):
                # advice is no more editable, adapt adviceIndex
                item.adviceIndex[groupId]['advice_editable'] = False
