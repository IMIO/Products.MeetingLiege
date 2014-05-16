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


def onAdviceTransition(advice, event):
    '''Called whenever a transition has been fired on an advice.'''
    if advice != event.object:
        return
    # initial_state
    if not event.transition and advice.advice_group in ['comptabilite', ]:
        wfTool = getToolByName(advice, 'portal_workflow')
        wfTool.doActionFor(advice, 'proposeToFinancialController')
        return

    # manage finance workflow, just consider relevant transitions
    # if it is not a finance wf transition, return
    if not advice.advice_group in ['comptabilite', ]:
        return

    newStateId = event.new_state.id
    if newStateId in ('advice_given', 'advice_under_edit'):
        # XXX remove given roles to finance members
        return

    # give 'Reader' role to every members of the _advisers and
    # give 'MeetingFinanceEditor' role to the relevant finance sub-group depending on new advice state
    # we use a specific 'MeetingFinanceEditor' role because the 'Editor' role is given to entire
    # _advisers group by default in PloneMeeting and it is used for non finance advices
    stateToGroupSuffixMappings = {'proposed_to_financial_controller': 'financialcontrollers',
                                  'proposed_to_financial_reviewer': 'financialreviewers',
                                  'proposed_to_financial_manager': 'financialmanagers', }
    adviserGroupId = '%s_advisers' % advice.advice_group
    advice.manage_addLocalRoles(adviserGroupId, ('Reader', ))
    advice.manage_addLocalRoles('%s_%s' % (advice.advice_group, stateToGroupSuffixMappings[newStateId]),
                                ('MeetingFinanceEditor', ))
