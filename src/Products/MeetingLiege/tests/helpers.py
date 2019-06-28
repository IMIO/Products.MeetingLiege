# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 by Imio.be
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

from collective.contact.plonegroup.utils import select_org_for_function
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer
from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.config import PROJECTNAME
from Products.MeetingLiege.profiles.liege.import_data import dfcompta
from Products.MeetingLiege.profiles.liege.import_data import dfcontrol
from Products.MeetingLiege.profiles.liege.import_data import dftresor
from Products.MeetingLiege.setuphandlers import _configureCollegeCustomAdvisers
from Products.PloneMeeting.exportimport.content import ToolInitializer
from Products.PloneMeeting.tests.helpers import PloneMeetingTestingHelpers


class MeetingLiegeTestingHelpers(PloneMeetingTestingHelpers):
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
    TRANSITIONS_FOR_ACCEPTING_ITEMS_MEETING_1 = ('freeze', 'decide', )
    TRANSITIONS_FOR_ACCEPTING_ITEMS_MEETING_2 = ('freeze', 'decide', )

    TRANSITIONS_FOR_PUBLISHING_MEETING_1 = TRANSITIONS_FOR_PUBLISHING_MEETING_2 = ('freeze', 'publish', )
    TRANSITIONS_FOR_FREEZING_MEETING_1 = TRANSITIONS_FOR_FREEZING_MEETING_2 = ('freeze', )
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

    WF_ITEM_STATE_NAME_MAPPINGS_1 = {'itemcreated': 'itemcreated',
                                     'proposed': 'proposed_to_director',
                                     'validated': 'validated',
                                     'presented': 'presented',
                                     'itemfrozen': 'itemfrozen'}
    WF_ITEM_STATE_NAME_MAPPING_2 = WF_ITEM_STATE_NAME_MAPPINGS_1

    # in which state an item must be after an particular meeting transition?
    ITEM_WF_STATE_AFTER_MEETING_TRANSITION = {'publish_decisions': 'accepted',
                                              'close': 'accepted'}

    def _setupFinanceGroups(self):
        '''Configure finance groups.'''
        # add pmFinController, pmFinReviewer and pmFinManager to advisers and to their respective finance group
        financial_group_uids = self.tool.financialGroupUids()
        self._addPrincipalToGroup('pmFinController', '{0}_advisers'.format(financial_group_uids[0]))
        self._addPrincipalToGroup('pmFinReviewer', '{0}_advisers'.format(financial_group_uids[0]))
        self._addPrincipalToGroup('pmFinManager', '{0}_advisers'.format(financial_group_uids[0]))
        self._addPrincipalToGroup('pmFinController', '{0}_financialcontrollers'.format(financial_group_uids[0]))
        self._addPrincipalToGroup('pmFinReviewer', '{0}_financialreviewers'.format(financial_group_uids[0]))
        self._addPrincipalToGroup('pmFinManager', '{0}_financialmanagers'.format(financial_group_uids[0]))

    def _giveFinanceAdvice(self, item, adviser_group_id):
        """Given an p_item in state 'proposed_to_finance', give the p_adviser_group_id advice on it."""
        originalUserId = self.member.getId()
        self.changeUser('pmFinController')
        changeCompleteness = item.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()
        advice = createContentInContainer(item,
                                          'meetingadvicefinances',
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

    def _setupCollegeItemWithFinanceAdvice(self, ):
        """Setup, create a College item and give finance advice on it."""
        self.changeUser('admin')
        # add finance groups
        self._createFinanceGroups()
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # first 'return' an item and test
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='An item with finance advice')
        # ask finance advice and give it
        financial_group_uids = self.tool.financialGroupUids()
        item.setFinanceAdvice(financial_group_uids[0])
        item._update_after_edit()
        self.proposeItem(item)
        self.do(item, 'proposeToFinance')
        # make item completeness complete and add advice
        self.changeUser('pmFinController')
        changeCompleteness = item.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()
        advice = createContentInContainer(item,
                                          'meetingadvicefinances',
                                          **{'advice_group': financial_group_uids[0],
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
        return item, advice

    def _setUpGroupsInCharge(self, item, groups=[]):
        """Override from PloneMeeting, define groupsOfMatter on category used by p_item."""
        if not groups:
            groups = [self.vendors_uid]

        cfg = self.meetingConfig
        cfg.setUseGroupsAsCategories(False)
        cat = cfg.categories.development
        cat.setGroupsOfMatter(groups)
        item.setCategory('development')
        item.updateLocalRoles()

    def _tearDownGroupsInCharge(self, item):
        """As group in charge is an adaptable method, it may be setup differently."""
        cfg = self.meetingConfig
        cat = cfg.categories.development
        cat.setGroupsOfMatter(())

    def _createFinanceGroups(self):
        """
           Create the finance groups.
        """
        context = self.portal.portal_setup._getImportContext('Products.MeetingLiege:testing')
        initializer = ToolInitializer(context, PROJECTNAME)
        org_descriptors = (dfcompta, dfcontrol, dftresor)
        orgs, active_orgs, savedOrgsData = initializer.addOrgs(org_descriptors, defer_data=False)
        for org in orgs:
            org_uid = org.UID()
            self._select_organization(org_uid)
            if org.getId() in FINANCE_GROUP_IDS:
                select_org_for_function(org_uid, 'financialcontrollers')
                select_org_for_function(org_uid, 'financialmanagers')
                select_org_for_function(org_uid, 'financialreviewers')
