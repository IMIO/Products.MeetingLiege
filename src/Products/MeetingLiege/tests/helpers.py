# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 by Imio.be
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

from DateTime import DateTime

from plone import api
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer

from Products.MeetingCommunes.tests.helpers import MeetingCommunesTestingHelpers
from Products.MeetingLiege.config import FINANCE_GROUP_IDS


class MeetingLiegeTestingHelpers(MeetingCommunesTestingHelpers):
    '''Override some values of PloneMeetingTestingHelpers.'''

    TRANSITIONS_FOR_PROPOSING_ITEM_1 = ('proposeToAdministrativeReviewer',
                                        'proposeToInternalReviewer',
                                        'proposeToDirector',)
    TRANSITIONS_FOR_PROPOSING_ITEM_2 = ('proposeToDirector', )
    TRANSITIONS_FOR_PREVALIDATING_ITEM_1 = TRANSITIONS_FOR_PREVALIDATING_ITEM_2 = ('proposeToAdministrativeReviewer',
                                                                                   'proposeToInternalReviewer',
                                                                                   'proposeToDirector')
    TRANSITIONS_FOR_VALIDATING_ITEM_1 = ('proposeToAdministrativeReviewer',
                                         'proposeToInternalReviewer',
                                         'proposeToDirector',
                                         'validate', )
    TRANSITIONS_FOR_VALIDATING_ITEM_2 = ('proposeToDirector',
                                         'validate', )
    TRANSITIONS_FOR_PRESENTING_ITEM_1 = ('proposeToAdministrativeReviewer',
                                         'proposeToInternalReviewer',
                                         'proposeToDirector',
                                         'validate',
                                         'present', )
    TRANSITIONS_FOR_PRESENTING_ITEM_2 = ('proposeToDirector',
                                         'validate',
                                         'present', )
    TRANSITIONS_FOR_ACCEPTING_ITEMS_1 = ('freeze', 'decide', )
    TRANSITIONS_FOR_ACCEPTING_ITEMS_2 = ('freeze', 'decide', )

    TRANSITIONS_FOR_DECIDING_MEETING_1 = ('freeze', 'decide', )
    TRANSITIONS_FOR_DECIDING_MEETING_2 = ('freeze', 'decide', )
    TRANSITIONS_FOR_CLOSING_MEETING_1 = ('freeze', 'decide', 'close', )
    TRANSITIONS_FOR_CLOSING_MEETING_2 = ('freeze', 'decide', 'close', )
    BACK_TO_WF_PATH_1 = {
        # Meeting
        'created': ('backToFrozen',
                    'backToCreated',),
        # MeetingItem
        'itemcreated': ('backToItemFrozen',
                        'backToPresented',
                        'backToValidated',
                        'backToProposedToDirector',
                        'backToProposedToInternalReviewer',
                        'backToProposedToAdministrativeReviewer',
                        'backToItemCreated', ),
        'proposed_to_director': ('backToItemFrozen',
                                 'backToPresented',
                                 'backToValidated',
                                 'backToProposedToDirector',
                                 'backToProposedToInternalReviewer',
                                 'backToProposedToAdministrativeReviewer', ),
        'validated': ('backToItemFrozen',
                      'backToPresented',
                      'backToValidated', )}
    BACK_TO_WF_PATH_2 = {
        'itemcreated': ('backToItemFrozen',
                        'backToPresented',
                        'backToValidated',
                        'backToProposedToDirector',
                        'backToItemCreated', ),
        'validated': ('backToItemFrozen',
                      'backToPresented',
                      'backToValidated', )}

    WF_STATE_NAME_MAPPINGS = {'itemcreated': 'itemcreated',
                              'proposed': 'proposed_to_director',
                              'validated': 'validated',
                              'presented': 'presented', }

    def _createMeetingWithItems(self, withItems=True, meetingDate=DateTime()):
        '''Create a meeting with a bunch of items.
           Overrided to do it as 'Manager' to be able
           to add recurring items.'''
        from plone.app.testing.helpers import setRoles
        currentMember = self.portal.portal_membership.getAuthenticatedMember()
        currentMemberRoles = currentMember.getRoles()
        setRoles(self.portal, currentMember.getId(), currentMemberRoles + ['Manager', ])
        meeting = MeetingCommunesTestingHelpers._createMeetingWithItems(self,
                                                                        withItems=withItems,
                                                                        meetingDate=meetingDate)
        setRoles(self.portal, currentMember.getId(), currentMemberRoles)
        return meeting

    def _setupFinanceGroups(self):
        '''Configure finance groups.'''
        groupsTool = api.portal.get_tool('portal_groups')
        # add pmFinController, pmFinReviewer and pmFinManager to advisers and to their respective finance group
        groupsTool.addPrincipalToGroup('pmFinController', '%s_advisers' % FINANCE_GROUP_IDS[0])
        groupsTool.addPrincipalToGroup('pmFinReviewer', '%s_advisers' % FINANCE_GROUP_IDS[0])
        groupsTool.addPrincipalToGroup('pmFinManager', '%s_advisers' % FINANCE_GROUP_IDS[0])
        groupsTool.addPrincipalToGroup('pmFinController', '%s_financialcontrollers' % FINANCE_GROUP_IDS[0])
        groupsTool.addPrincipalToGroup('pmFinReviewer', '%s_financialreviewers' % FINANCE_GROUP_IDS[0])
        groupsTool.addPrincipalToGroup('pmFinManager', '%s_financialmanagers' % FINANCE_GROUP_IDS[0])

    def _giveFinanceAdvice(self, item, adviser_group_id):
        """Given an p_item in state 'proposed_to_finance', give the p_adviser_group_id advice on it."""
        originalUserId = self.member.getId()
        self.changeUser('pmFinController')
        changeCompleteness = item.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()
        advice = createContentInContainer(item,
                                          'meetingadvice',
                                          **{'advice_group': adviser_group_id,
                                             'advice_type': u'positive_finance',
                                             'advice_comment': RichTextValue(u'<p>My comment finance</p>'),
                                             'advice_observations': RichTextValue(u'<p>My observation finance</p>')})
        self.do(advice, 'proposeToFinancialReviewer', comment='My financial controller comment')
        # as finance reviewer
        self.changeUser('pmFinReviewer')
        self.do(advice, 'proposeToFinancialManager', comment='My financial reviewer comment')
        # as finance manager
        self.changeUser('pmFinManager')
        self.do(advice, 'signFinancialAdvice', comment='My financial manager comment')
        self.changeUser(originalUserId)
        return advice
