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
from Products.MeetingLiege.config import FINANCE_ADVICE_LEGAL_TEXT_PRE
from Products.MeetingLiege.config import FINANCE_ADVICE_LEGAL_TEXT
from Products.MeetingLiege.config import FINANCE_ADVICE_LEGAL_TEXT_NOT_GIVEN
from Products.MeetingLiege.setuphandlers import _configureCollegeCustomAdvisers
from Products.MeetingLiege.setuphandlers import _createFinanceGroups
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase

from datetime import datetime

from plone.app.textfield.value import RichTextValue

from plone.dexterity.utils import createContentInContainer


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

        # editing item keeps correct local roles
        self.changeUser('pmManager')
        item.at_post_edit_script()
        self.assertTrue(item.__ac_local_roles__[specialReaders] == ['Reader', ])

        # functionnality is for validated items and for items in a meeting
        # so present the item and check that it still works
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
        self.assertTrue(item1_order < item3_order < item2_order == item5_order
                        < item7_order < item4_order < item6_order)
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

    def test_GetItemWithFinanceAdvice(self):
        '''Test the custom getItemWithFinanceAdvice method.
           This will return the item an advice was given on in case the item
           is the result of a 'return college' item or if it is a council item and
           item in the college had the finance advice.
           Moreover, when an advice holder is linked to another item, the finance group
           gets automatically red access to the new item.
        '''
        self.changeUser('admin')
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # add finance groups
        _createFinanceGroups(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        self.changeUser('pmManager')
        item = self.create('MeetingItem')
        item.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        item.at_post_edit_script()
        self.assertTrue(FINANCE_GROUP_IDS[0] in item.adviceIndex)
        self.assertTrue(item.adapted().getItemWithFinanceAdvice() == item)
        # give advice
        self.proposeItem(item)
        self.do(item, 'proposeToFinance')
        self.changeUser('pmFinManager')
        item.setCompleteness('completeness_complete')
        item.setEmergency('emergency_accepted')
        createContentInContainer(item,
                                 'meetingadvice',
                                 **{'advice_group': FINANCE_GROUP_IDS[0],
                                    'advice_type': 'positive_finance',
                                    'advice_comment': RichTextValue(u'My positive comment finance')})
        # finance group has read access to the item
        financeGroupAdvisersId = "{0}_advisers".format(item.getFinanceAdvice())
        self.assertTrue(item.__ac_local_roles__[financeGroupAdvisersId] == ['Reader'])

        self.changeUser('pmManager')
        # duplicate and keep link will not consider original finance advice
        # as advice for the duplicated item
        item.onDuplicateAndKeepLink()
        duplicatedItem = item.getBRefs()[0]
        # the duplicatedItem advice referent is the duplicatedItem...
        self.assertTrue(duplicatedItem.adapted().getItemWithFinanceAdvice() == duplicatedItem)
        # the finance advice is asked on the duplicatedItem
        self.assertTrue(duplicatedItem.getFinanceAdvice() == FINANCE_GROUP_IDS[0])
        self.assertTrue(FINANCE_GROUP_IDS[0] in duplicatedItem.adviceIndex)
        # finance group did not get automatically access to the duplicatedItem
        self.assertTrue(financeGroupAdvisersId not in duplicatedItem.__ac_local_roles__)

        # delaying an item will not make original item the item holder
        # the finance advice is asked on the delayed item too
        meeting = self.create('Meeting', date='2015/01/01')
        self.presentItem(item)
        self.decideMeeting(meeting)
        self.do(item, 'delay')
        # find the new item created by the clone as item is already the predecessor of 'duplicatedItem'
        clonedDelayedItem = [newItem for newItem in item.getBRefs('ItemPredecessor')
                             if not newItem == duplicatedItem][0]
        self.assertTrue(clonedDelayedItem.adapted().getItemWithFinanceAdvice() == clonedDelayedItem)
        # the finance advice is asked on the clonedDelayedItem
        self.assertTrue(clonedDelayedItem.getFinanceAdvice() == FINANCE_GROUP_IDS[0])
        self.assertTrue(FINANCE_GROUP_IDS[0] in clonedDelayedItem.adviceIndex)
        # finance group did not get automatically access to the clonedDelayedItem
        self.assertTrue(financeGroupAdvisersId not in duplicatedItem.__ac_local_roles__)

        # now correct item and 'accept and return' it
        # this time, the original item is considered the finance advice holder
        self.do(item, 'backToItemFrozen')
        self.do(item, 'return')
        # find the new item created by the clone as item is already the predecessor of 'duplicatedItem'
        clonedReturnedItem = [newItem for newItem in item.getBRefs('ItemPredecessor')
                              if not newItem in (duplicatedItem, clonedDelayedItem)][0]
        # this time, the item with finance advice is the 'returned' item
        itemWithFinanceAdvice = clonedReturnedItem.adapted().getItemWithFinanceAdvice()
        self.assertTrue(itemWithFinanceAdvice == item)
        self.assertTrue(itemWithFinanceAdvice.queryState() == 'returned')
        # the info is kept in the financeAdvice attribute
        # nevertheless, the advice is not asked automatically anymore
        self.assertTrue(clonedReturnedItem.getFinanceAdvice() == FINANCE_GROUP_IDS[0])
        self.assertTrue(not FINANCE_GROUP_IDS[0] in clonedReturnedItem.adviceIndex)
        # finance group gets automatically access to the clonedReturnedItem
        self.assertTrue(clonedReturnedItem.__ac_local_roles__[financeGroupAdvisersId] == ['Reader'])

        # now test when the item is in the council
        # the right college item should be found too
        # use 2 items, one that will be classicaly accepted and one that will 'accepted_and_returned'
        itemToCouncil1 = self.create('MeetingItem')
        itemToCouncil1.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        itemToCouncil1.setOtherMeetingConfigsClonableTo('meeting-config-council')
        itemToCouncil2 = self.create('MeetingItem')
        itemToCouncil2.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        itemToCouncil2.setOtherMeetingConfigsClonableTo('meeting-config-council')
        # ask emergency so finance step is passed
        itemToCouncil1.setEmergency('emergency_asked')
        itemToCouncil2.setEmergency('emergency_asked')
        itemToCouncil1.at_post_edit_script()
        itemToCouncil2.at_post_edit_script()
        self.assertTrue(FINANCE_GROUP_IDS[0] in itemToCouncil1.adviceIndex)
        self.assertTrue(FINANCE_GROUP_IDS[0] in itemToCouncil2.adviceIndex)
        self.presentItem(itemToCouncil1)
        self.presentItem(itemToCouncil2)
        # accept itemToCouncil1 and check
        self.do(itemToCouncil1, 'accept')
        itemInCouncil1 = itemToCouncil1.getItemClonedToOtherMC('meeting-config-council')
        self.assertTrue(itemInCouncil1.adapted().getItemWithFinanceAdvice() == itemToCouncil1)
        # finance group gets automatically access to the itemInCouncil1
        self.assertTrue(itemInCouncil1.__ac_local_roles__[financeGroupAdvisersId] == ['Reader'])
        # accept_and_return itemToCouncil2 and check
        self.do(itemToCouncil2, 'accept_and_return')
        itemInCouncil2 = itemToCouncil2.getItemClonedToOtherMC('meeting-config-council')
        self.assertTrue(itemInCouncil2.adapted().getItemWithFinanceAdvice() == itemToCouncil2)
        # when college item was accepted_and_returned, it was cloned, the finance advice
        # is also found for this cloned item
        clonedAcceptedAndReturnedItem = [newItem for newItem in itemToCouncil2.getBRefs('ItemPredecessor')
                                         if newItem.portal_type == 'MeetingItemCollege'][0]
        self.assertTrue(clonedAcceptedAndReturnedItem.adapted().getItemWithFinanceAdvice() == itemToCouncil2)
        # finance group gets automatically access to the itemInCouncil2
        self.assertTrue(itemInCouncil2.__ac_local_roles__[financeGroupAdvisersId] == ['Reader'])
        # roles are kept after edit or transition
        itemInCouncil2.at_post_edit_script()
        self.assertTrue(itemInCouncil2.__ac_local_roles__[financeGroupAdvisersId] == ['Reader'])
        # only available transition is 'present', so create a meeting in council to test...
        self.setMeetingConfig(self.meetingConfig2.getId())
        self.meetingConfig2.setUseGroupsAsCategories(True)
        self.meetingConfig2.setInsertingMethodsOnAddItem(({'insertingMethod': 'on_proposing_groups', 'reverse': '0'},))
        self.create('Meeting', date='2015/01/01')
        self.do(itemInCouncil2, 'present')
        self.assertTrue(itemInCouncil2.queryState() == 'presented')
        self.assertTrue(itemInCouncil2.__ac_local_roles__[financeGroupAdvisersId] == ['Reader'])

    def test_getLegalTextForFDAdvice(self):
        self.changeUser('admin')
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # add finance groups
        _createFinanceGroups(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        self.changeUser('pmManager')
        item1 = self.create('MeetingItem', title='Item with positive advice')
        item1.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        item2 = self.create('MeetingItem', title='Item with negative advice')
        item2.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        item3 = self.create('MeetingItem', title='Item with no advice')
        item3.setFinanceAdvice(FINANCE_GROUP_IDS[0])

        self.proposeItem(item1)
        self.proposeItem(item2)
        self.proposeItem(item3)
        self.do(item1, 'proposeToFinance')
        item1.setCompleteness('completeness_complete')
        self.do(item2, 'proposeToFinance')
        item2.setCompleteness('completeness_complete')
        self.do(item3, 'proposeToFinance')
        item3.setCompleteness('completeness_complete')
        item3.updateAdvices()
        item3.adviceIndex[item3.getFinanceAdvice()]['delay_started_on'] = datetime(2012, 1, 1)
        item3.updateAdvices()

        self.changeUser('pmFinManager')
        advice1 = createContentInContainer(item1,
                                           'meetingadvice',
                                           **{'advice_group': FINANCE_GROUP_IDS[0],
                                              'advice_type': 'positive_finance',
                                              'advice_comment': RichTextValue(u'My good comment finance')})
        advice2 = createContentInContainer(item2,
                                           'meetingadvice',
                                           **{'advice_group': FINANCE_GROUP_IDS[0],
                                              'advice_type': 'negative_finance',
                                              'advice_comment': RichTextValue(u'My bad comment finance')})

        # send to financial reviewer
        self.changeUser('pmFinController')
        self.do(advice1, 'proposeToFinancialReviewer')
        self.do(advice2, 'proposeToFinancialReviewer')
        # send to finance manager
        self.do(advice1, 'proposeToFinancialManager')
        self.do(advice2, 'proposeToFinancialManager')
        # sign the advice
        self.do(advice1, 'signFinancialAdvice')
        self.do(advice2, 'signFinancialAdvice')

        financialStuff1 = item1.adapted().getFinancialAdviceStuff()
        financialStuff2 = item2.adapted().getFinancialAdviceStuff()
        advice1 = item1.getAdviceDataFor(item1, item1.getFinanceAdvice())
        advice2 = item2.getAdviceDataFor(item2, item2.getFinanceAdvice())
        advice3 = item3.getAdviceDataFor(item3, item3.getFinanceAdvice())
        delayStartedOn1 = advice1['delay_infos']['delay_started_on_localized']
        delayStartedOn2 = advice2['delay_infos']['delay_started_on_localized']
        delayStartedOn3 = advice3['delay_infos']['delay_started_on_localized']
        outOfFinancialdptLocalized1 = financialStuff1['out_of_financial_dpt_localized']
        outOfFinancialdptLocalized2 = financialStuff2['out_of_financial_dpt_localized']
        comment2 = financialStuff2['comment']
        limitDateLocalized3 = advice3['delay_infos']['limit_date_localized']

        res1 = FINANCE_ADVICE_LEGAL_TEXT_PRE.format(delayStartedOn1)
        res1 = res1 + FINANCE_ADVICE_LEGAL_TEXT.format('favorable',
                                                       outOfFinancialdptLocalized1)
        res2 = FINANCE_ADVICE_LEGAL_TEXT_PRE.format(delayStartedOn2)
        res2 = res2 + FINANCE_ADVICE_LEGAL_TEXT.format('défavorable',
                                                       outOfFinancialdptLocalized2)
        res2 = res2 + "<p>{0}</p>".format(comment2)

        res3 = FINANCE_ADVICE_LEGAL_TEXT_PRE.format(delayStartedOn3)
        res3 = res3 + FINANCE_ADVICE_LEGAL_TEXT_NOT_GIVEN

        res4 = '<p>Avis favorable du Directeur Financier du {0}</p>'.format(outOfFinancialdptLocalized1)

        res5 = '<p>Avis défavorable du Directeur Financier du {0}</p>'.format(outOfFinancialdptLocalized2)
        res5 = res5 + "<p>{0}</p>".format(comment2)

        res6 = "<p>Avis du Directeur financier expiré le {0}</p>".format(limitDateLocalized3)

        self.assertTrue(item1.adapted().getLegalTextForFDAdvice() == res1)
        self.assertTrue(item2.adapted().getLegalTextForFDAdvice() == res2)
        self.assertTrue(item3.adapted().getLegalTextForFDAdvice() == res3)

        self.assertTrue(item1.adapted().getLegalTextForFDAdvice(isMeeting=True) == res4)
        self.assertTrue(item2.adapted().getLegalTextForFDAdvice(isMeeting=True) == res5)
        self.assertTrue(item3.adapted().getLegalTextForFDAdvice(isMeeting=True) == res6)

    def test_DecisionAnnexesNotKeptOnDuplicated(self):
        """When an item is duplicated using the 'duplicate and keep link',
           we do not keep the decision annexes."""
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        annex = self.addAnnex(item)
        annexDecision = self.addAnnex(item, relatedTo='item_decision')
        self.assertTrue(IAnnexable(item).getAnnexes(relatedTo='item') == [annex, ])
        self.assertTrue(IAnnexable(item).getAnnexes(relatedTo='item_decision') == [annexDecision, ])
        # cloned and link not kept, decison annexes are removed
        clonedItem = item.clone()
        self.assertTrue(IAnnexable(clonedItem).getAnnexes(relatedTo='item'))
        self.assertFalse(IAnnexable(clonedItem).getAnnexes(relatedTo='item_decision'))
        # cloned but link kept, decison annexes are also kept
        clonedItem = item.clone(setCurrentAsPredecessor=True)
        self.assertTrue(IAnnexable(clonedItem).getAnnexes(relatedTo='item'))
        self.assertFalse(IAnnexable(clonedItem).getAnnexes(relatedTo='item_decision'))
