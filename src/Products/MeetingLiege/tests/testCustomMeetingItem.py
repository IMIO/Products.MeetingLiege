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

    def test_ItemReference(self):
        '''Test item reference generation.'''
        # use categories
        self.meetingConfig.setUseGroupsAsCategories(False)
        self.changeUser('pmManager')
        # remove recurring items
        self._removeConfigObjectsFor(self.meetingConfig)
        # create 5 items using different categories and insert it in a meeting
        depItem1 = self.create('MeetingItem')
        depItem1.setCategory('deployment')
        depItem2 = self.create('MeetingItem')
        depItem2.setCategory('deployment')
        devItem1 = self.create('MeetingItem')
        devItem1.setCategory('development')
        devItem2 = self.create('MeetingItem')
        devItem2.setCategory('development')
        resItem1 = self.create('MeetingItem')
        resItem1.setCategory('research')
        meeting = self.create('Meeting', date='2015/01/01')
        self.presentItem(depItem1)
        self.presentItem(depItem2)
        self.presentItem(devItem1)
        self.presentItem(devItem2)
        self.presentItem(resItem1)
        self.freezeMeeting(meeting)
        # check that item references are correct
        self.assertTrue([item.getItemReference() for item in meeting.getItemsInOrder()] ==
                        ['deployment1', 'deployment2', 'development1', 'development2', 'research1'])
        self.assertTrue([item.getId() for item in meeting.getItemsInOrder()] ==
                        ['o1', 'o2', 'o3', 'o4', 'o5'])
        # change position of items 1 and 2, itemReference is changed too
        changeOrder = depItem1.restrictedTraverse('@@change_item_order')
        changeOrder(moveType='down')
        self.assertTrue([item.getItemReference() for item in meeting.getItemsInOrder()] ==
                        ['deployment1', 'deployment2', 'development1', 'development2', 'research1'])
        self.assertTrue([item.getId() for item in meeting.getItemsInOrder()] ==
                        ['o2', 'o1', 'o3', 'o4', 'o5'])
        # move depItem2 to last position
        changeOrder = depItem2.restrictedTraverse('@@change_item_order')
        changeOrder(moveType='number', moveNumber=6)
        # now depItem1 reference is back to 'deployment1' and depItem2 in last position
        self.assertTrue([item.getItemReference() for item in meeting.getItemsInOrder()] ==
                        ['deployment1', 'development1', 'development2', 'research1', 'deployment2'])
        self.assertTrue([item.getId() for item in meeting.getItemsInOrder()] ==
                        ['o1', 'o3', 'o4', 'o5', 'o2'])

        # if we insert a new item, references are updated
        newItem = self.create('MeetingItem')
        newItem.setCategory('development')
        # force it to be inserted as a normal item
        self.request.form['itemInsertForceNormal'] = True
        self.presentItem(newItem)
        # item is inserted at the end
        self.assertTrue([item.getItemReference() for item in meeting.getItemsInOrder()] ==
                        ['deployment1', 'development1', 'development2', 'research1', 'deployment2', 'development3'])
        self.assertTrue([item.getId() for item in meeting.getItemsInOrder()] ==
                        ['o1', 'o3', 'o4', 'o5', 'o2', 'o7'])

        # now if we remove an item from the meeting, reference are still correct
        # remove item with ref 'deployment1', the first item, the item that had 'deployment2' will get 'deployment1'
        self.do(depItem1, 'backToPresented')
        self.do(depItem1, 'backToValidated')
        self.assertTrue([item.getItemReference() for item in meeting.getItemsInOrder()] ==
                        ['development1', 'development2', 'research1', 'deployment1', 'development3'])
        self.assertTrue([item.getId() for item in meeting.getItemsInOrder()] ==
                        ['o3', 'o4', 'o5', 'o2', 'o7'])

        # delete item having reference 'development2'
        # only Manager may delete an item
        self.changeUser('admin')
        meeting.restrictedTraverse('@@delete_givenuid')(devItem2.UID())
        self.assertTrue([item.getItemReference() for item in meeting.getItemsInOrder()] ==
                        ['development1', 'research1', 'deployment1', 'development2'])
        self.assertTrue([item.getId() for item in meeting.getItemsInOrder()] ==
                        ['o3', 'o5', 'o2', 'o7'])

        # if we change the category used for an item, reference are updated accordingly
        # change category for resItem1 from 'research' to 'development'
        resItem1.setCategory('development')
        resItem1.notifyModified()
        self.assertTrue([item.getItemReference() for item in meeting.getItemsInOrder()] ==
                        ['development1', 'development2', 'deployment1', 'development3'])
        self.assertTrue([item.getId() for item in meeting.getItemsInOrder()] ==
                        ['o3', 'o5', 'o2', 'o7'])

    def test_InsertingMethodOnDecisionFirstWord(self):
        '''
          Test our custom inserting method 'on_decision_first_word'.
        '''
        self.changeUser('pmManager')
        self._removeConfigObjectsFor(self.meetingConfig)
        insertingMethods = ({'insertingMethod': 'on_decision_first_word', 'reverse': '0'},)
        # no decision, it will get minimum possible index value
        item1 = self.create('MeetingItem')
        item1.setDecision('<p></p>')
        item1Id = item1.getId()
        item1_order = item1.getInsertOrder(insertingMethods)
        # decision < 6 chars
        item2 = self.create('MeetingItem')
        item2.setDecision('<p>EMET</p>')
        item2Id = item2.getId()
        item2_order = item2.getInsertOrder(insertingMethods)
        # beginning with 'A'
        item3 = self.create('MeetingItem')
        item3.setDecision('<p>ACCORDE un avis de ...</p>')
        item3Id = item3.getId()
        item3_order = item3.getInsertOrder(insertingMethods)
        # beginning with 'O'
        item4 = self.create('MeetingItem')
        item4.setDecision('<p>&nbsp;OCTROIE un avis de ...</p>')
        item4Id = item4.getId()
        item4_order = item4.getInsertOrder(insertingMethods)
        # begin with a space then EMET
        item5 = self.create('MeetingItem')
        item5.setDecision('<p>&nbsp;</p><p>EMET</p>')
        item5Id = item5.getId()
        item5_order = item5.getInsertOrder(insertingMethods)
        # use 'zzzzzz', it will get maximum possible index value
        item6 = self.create('MeetingItem')
        item6.setDecision('<p>zzzzzz</p>')
        item6Id = item6.getId()
        item6_order = item6.getInsertOrder(insertingMethods)
        # use same beginning of sentence as item2 and item5 but
        # with an extra letter that will be taken into account
        item7 = self.create('MeetingItem')
        item7.setDecision('<p>EMET un avis</p>')
        item7Id = item7.getId()
        item7_order = item7.getInsertOrder(insertingMethods)
        # result should be item1, item3, item2, item5 (equals to item2) then item4
        self.assertTrue(item1_order < item3_order < item2_order == item5_order < item7_order < item4_order < item6_order)
        # every items use proposingGroup 'developers' that is in position 1
        # if we use 'vendors' for item1, item1_order will become higher than item6_order
        insertingMethods = ({'insertingMethod': 'on_proposing_groups', 'reverse': '0'},
                            {'insertingMethod': 'on_decision_first_word', 'reverse': '0'},)
        for item in item1, item2, item3, item4, item5, item6, item7:
            self.assertTrue(item.getProposingGroup() == 'developers')
        self.assertTrue(item1._findOrderFor('on_proposing_groups') == 0)
        item1.setProposingGroup('vendors')
        self.assertTrue(item1._findOrderFor('on_proposing_groups') == 1)
        # now order of item1 is higher than order of item6
        self.assertTrue(item1.getInsertOrder(insertingMethods) > item6.getInsertOrder(insertingMethods))

        # now insert items in a meeting and compare
        self.meetingConfig.setInsertingMethodsOnAddItem(insertingMethods)
        meeting = self.create('Meeting', date='2015/01/01')
        for item in item1, item2, item3, item4, item5, item6, item7:
            self.presentItem(item)
        # items should have been added respecting following order item3, item2, item5, item4, item6, item1
        self.assertTrue([item.getId() for item in meeting.getItemsInOrder()] ==
                        [item3Id, item2Id, item5Id, item7Id, item4Id, item6Id, item1Id, ])
