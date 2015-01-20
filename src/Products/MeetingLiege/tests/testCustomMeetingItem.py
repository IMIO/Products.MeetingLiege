# -*- coding: utf-8 -*-
#
# File: testCustomMeetingItem.py
#
# Copyright (c) 2007-2012 by CommunesPlone.org
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

from Products.CMFCore.permissions import View

from Products.PloneMeeting.interfaces import IAnnexable
from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.setuphandlers import _configureCollegeCustomAdvisers
from Products.MeetingLiege.setuphandlers import _createFinanceGroups
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase


class testCustomMeetingItem(MeetingLiegeTestCase):
    """
        Tests the MeetingItem adapted methods
    """

    def test_InitFieldsWhenItemSentToCouncil(self):
        '''When an item is sent from College to Council, fields 'title' and 'privacy'
           are initialized from what is defined on the College item.'''
        # create a college item
        self.changeUser('pmManager')
        item = self.create('MeetingItem')
        item.setLabelForCouncil('<p>My label for council</p>')
        # default privacy is 'public', set 'secret' so we see that it is actually applied
        item.setPrivacyForCouncil('secret')
        # make item sendable to council
        item.setOtherMeetingConfigsClonableTo('meeting-config-council')
        # send the item to the council
        meeting = self.create('Meeting', date=DateTime('2014/01/01'))
        self.presentItem(item)
        self.closeMeeting(meeting)
        # the item has been sent, get it and test that relevant fields are correctly initialized
        newItem = item.getBRefs('ItemPredecessor')[0]
        self.assertTrue(newItem.getPredecessor().UID() == item.UID())
        self.assertTrue(newItem.getLabelForCouncil() == '<p>My label for council</p>')
        self.assertTrue(newItem.getPrivacy() == 'secret')

    def test_FinanceAdviceAskedDependingOnFinanceAdviceField(self):
        '''Finance advice is asked depending on MeetingItem.financeAdvice selected value.'''
        # create finance groups
        self.changeUser('admin')
        _createFinanceGroups(self.portal)
        _configureCollegeCustomAdvisers(self.portal)
        self.changeUser('pmManager')
        # create an item with relevant adviceFinance
        item = self.create('MeetingItem')
        # by default, no adviceFinance asked
        self.assertTrue(item.getFinanceAdvice() == '_none_')
        item.at_post_edit_script()
        self.assertTrue(item.adviceIndex == {})
        # ask finance advice
        item.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        item.at_post_edit_script()
        self.assertTrue(FINANCE_GROUP_IDS[0] in item.adviceIndex)
        self.assertTrue(len(item.adviceIndex) == 1)
        # now ask another advice finance
        item.setFinanceAdvice(FINANCE_GROUP_IDS[1])
        item.at_post_edit_script()
        self.assertTrue(FINANCE_GROUP_IDS[1] in item.adviceIndex)
        self.assertTrue(len(item.adviceIndex) == 1)

    def test_GroupsOfMatter(self):
        '''Once an item is 'validated' (and after in the WF), group selected on the used MeetingCategory as
           responsible of this category (groupsOfMatter) will get 'Reader' access to this item.'''
        # configure so we use categories, and adapt category 'development'
        # so we select a group in it's groupsOfMatter
        self.meetingConfig.setUseGroupsAsCategories(False)
        development = self.meetingConfig.categories.development
        development.setGroupsOfMatter(('vendors', ))
        # create an item for the 'developers' group
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        # select the right category
        item.setCategory(development.getId())
        item.at_post_edit_script()
        specialReaders = 'vendors_observers'
        # right category is selected by item must be at least validated
        self.assertTrue(not specialReaders in item.__ac_local_roles__)

        # validate the item
        self.validateItem(item)
        # now local_roles are correct
        self.assertTrue(item.__ac_local_roles__[specialReaders] == ['Reader', ])
        # going back to 'proposed' will remove given local roles
        self.backToState(item, self.WF_STATE_NAME_MAPPINGS['proposed'])
        self.assertTrue(not specialReaders in item.__ac_local_roles__)
        self.validateItem(item)
        self.assertTrue(item.__ac_local_roles__[specialReaders] == ['Reader', ])

        # functionnality is for validated items and for items in a meeting
        # so present the item and check that it still works
        self.changeUser('pmManager')
        self.create('Meeting', date='2015/01/01')
        self.presentItem(item)
        self.assertTrue(item.queryState() != 'validated')
        self.assertTrue(item.__ac_local_roles__[specialReaders] == ['Reader', ])

        # if we use another category, local roles are removed
        item.setCategory('projects')
        item.at_post_edit_script()
        self.assertTrue(not specialReaders in item.__ac_local_roles__)

    def test_AnnexesConfidentialityDependingOnMatter(self):
        '''Power observers may only access annexes of items they are in charge of.
           A single exception is made for annex type 'annexeCahier' that is viewable
           by every power observers.'''
        # configure so we use categories, and adapt category 'development'
        # so we select a group in it's groupsOfMatter
        self.meetingConfig.setUseGroupsAsCategories(False)
        # confidential annexes are hidden to restricted power observers
        self.meetingConfig.setAnnexConfidentialFor(('restricted_power_observers', ))
        self.meetingConfig.setUseGroupsAsCategories(False)
        development = self.meetingConfig.categories.development
        development.setGroupsOfMatter(('vendors', ))
        # create an item for the 'developers' group
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        annex1 = self.addAnnex(item)
        annex2 = self.addAnnex(item)
        # annex using type 'annexeCahier' or 'courrier-a-valider-par-le-college'
        # are viewable by every power observers
        annex3 = self.addAnnex(item, annexType='annexeCahier')
        annex4 = self.addAnnex(item, annexType='courrier-a-valider-par-le-college')
        annex2.setIsConfidential(True)
        annex3.setIsConfidential(True)
        annex4.setIsConfidential(True)
        # select the right category
        item.setCategory(development.getId())
        item.at_post_edit_script()
        self.validateItem(item)
        specialReaders = 'vendors_observers'

        # power observers may access items when it is 'presented'
        self.changeUser('pmManager')
        self.create('Meeting', date='2015/01/01')
        self.presentItem(item)
        self.changeUser('powerobserver1')
        # powerobservers1 is not member of 'vendors_observers' so he
        # will not be able to access the annexes of the item
        self.assertTrue(not specialReaders in self.member.getGroups())
        self.hasPermission(View, item)
        # no matter the annex is confidential or not, both are not viewable
        self.assertFalse(IAnnexable(item)._isViewableForCurrentUser(cfg=self.meetingConfig,
                                                                    isPowerObserver=True,
                                                                    isRestrictedPowerObserver=False,
                                                                    annexInfo=annex1.getAnnexInfo()))
        self.assertFalse(IAnnexable(item)._isViewableForCurrentUser(cfg=self.meetingConfig,
                                                                    isPowerObserver=True,
                                                                    isRestrictedPowerObserver=False,
                                                                    annexInfo=annex2.getAnnexInfo()))
        # an annex using "annexeCahier" or "courrier-a-valider-par-le-college" will be viewable by power observers
        self.assertTrue(IAnnexable(item)._isViewableForCurrentUser(cfg=self.meetingConfig,
                                                                   isPowerObserver=True,
                                                                   isRestrictedPowerObserver=False,
                                                                   annexInfo=annex3.getAnnexInfo()))
        self.assertTrue(IAnnexable(item)._isViewableForCurrentUser(cfg=self.meetingConfig,
                                                                   isPowerObserver=True,
                                                                   isRestrictedPowerObserver=False,
                                                                   annexInfo=annex4.getAnnexInfo()))
        # if we assign 'powerobserver1' to the 'vendors_observers' group
        # he will be able to view the annexes of item as he is in charge of
        self.portal.portal_groups.addPrincipalToGroup('powerobserver1', specialReaders)
        # log again as 'powerobserver1' so getGroups is refreshed
        self.changeUser('powerobserver1')
        self.assertTrue(IAnnexable(item)._isViewableForCurrentUser(cfg=self.meetingConfig,
                                                                   isPowerObserver=True,
                                                                   isRestrictedPowerObserver=False,
                                                                   annexInfo=annex1.getAnnexInfo()))
        self.assertTrue(IAnnexable(item)._isViewableForCurrentUser(cfg=self.meetingConfig,
                                                                   isPowerObserver=True,
                                                                   isRestrictedPowerObserver=False,
                                                                   annexInfo=annex2.getAnnexInfo()))
        self.assertTrue(IAnnexable(item)._isViewableForCurrentUser(cfg=self.meetingConfig,
                                                                   isPowerObserver=True,
                                                                   isRestrictedPowerObserver=False,
                                                                   annexInfo=annex3.getAnnexInfo()))
        self.assertTrue(IAnnexable(item)._isViewableForCurrentUser(cfg=self.meetingConfig,
                                                                   isPowerObserver=True,
                                                                   isRestrictedPowerObserver=False,
                                                                   annexInfo=annex4.getAnnexInfo()))
