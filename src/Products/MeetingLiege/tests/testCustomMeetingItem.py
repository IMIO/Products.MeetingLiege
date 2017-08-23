# -*- coding: utf-8 -*-
#
# File: testCustomMeetingItem.py
#
# Copyright (c) 2007-2015 by Imio.be
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

from datetime import datetime
from DateTime import DateTime
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

from collective.iconifiedcategory.utils import get_categorized_elements
from imio.helpers.cache import cleanRamCacheFor
from plone import api
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer

from Products.CMFCore.permissions import View
from Products.PloneMeeting.utils import get_annexes
from Products.MeetingLiege.config import COUNCILITEM_DECISIONEND_SENTENCE
from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.config import FINANCE_ADVICE_LEGAL_TEXT_PRE
from Products.MeetingLiege.config import FINANCE_ADVICE_LEGAL_TEXT
from Products.MeetingLiege.config import FINANCE_ADVICE_LEGAL_TEXT_NOT_GIVEN
from Products.MeetingLiege.profiles.liege import import_data as ml_import_data
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
        # before we used field 'privacyForCouncil' to init privacy on Council item
        # now use the field MeetingItem.otherMeetingConfigsClonableToPrivacy
        item.setOtherMeetingConfigsClonableToPrivacy((self.meetingConfig2.getId(), ))
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
        cfg = self.meetingConfig
        cfg.setUseGroupsAsCategories(False)
        development = cfg.categories.development
        development.setGroupsOfMatter(('vendors', ))
        # create an item for the 'developers' group
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        # select the right category
        item.setCategory(development.getId())
        item.at_post_edit_script()
        specialReaders = 'vendors_observers'
        # right category is selected by item must be at least validated
        self.assertTrue(specialReaders not in item.__ac_local_roles__)

        # validate the item
        self.validateItem(item)
        # now local_roles are correct
        self.assertTrue(item.__ac_local_roles__[specialReaders] == ['Reader', ])
        # going back to 'proposed' will remove given local roles
        self.backToState(item, self.WF_STATE_NAME_MAPPINGS['proposed'])
        self.assertTrue(specialReaders not in item.__ac_local_roles__)
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
        self.assertTrue(specialReaders not in item.__ac_local_roles__)

    def test_AnnexesConfidentialityDependingOnMatter(self):
        '''Power observers may only access annexes of items they are in charge of.
           A single exception is made for annex type 'annexeCahier' that is viewable
           by every power observers.
           Decision annexes are visible by power observers no matter... matter nor confidentiality.'''
        # configure so we use categories, and adapt category 'development'
        # so we select a group in it's groupsOfMatter
        self.changeUser('siteadmin')
        cfg = self.meetingConfig
        cfg.setUseGroupsAsCategories(False)
        cfg.setItemPowerObserversStates((u'itemcreated', u'presented', u'accepted', u'delayed', u'refused'))
        cfg.setItemRestrictedPowerObserversStates((u'itemcreated', u'presented', u'accepted', u'delayed', u'refused'))
        development = cfg.categories.development
        development.setGroupsOfMatter(('vendors', ))
        # confidential annexes are hidden to restricted power observers
        cfg.annexes_types.item_annexes.confidentiality_activated = True
        cfg.annexes_types.item_decision_annexes.confidentiality_activated = True
        cfg.setItemAnnexConfidentialVisibleFor(ml_import_data.collegeMeeting.itemAnnexConfidentialVisibleFor)
        # add special annexTypes 'annexeCahier' and 'courrier-a-valider-par-le-college'
        self.addAnnexType(id='annexeCahier')
        self.addAnnexType(id='courrier-a-valider-par-le-college')
        # create an item for the 'developers' group
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        # not confidential annex
        annex1 = self.addAnnex(item)
        self.assertFalse(annex1.confidential)
        annex2 = self.addAnnex(item)
        # annex using type 'annexeCahier' or 'courrier-a-valider-par-le-college'
        # are viewable by every power observers
        annex3 = self.addAnnex(item, annexType='annexeCahier')
        annex4 = self.addAnnex(item, annexType='courrier-a-valider-par-le-college')
        annex_decision1 = self.addAnnex(item, relatedTo='item_decision')
        self.assertFalse(annex_decision1.confidential)
        annex_decision2 = self.addAnnex(item, relatedTo='item_decision')
        annex2.confidential = True
        notify(ObjectModifiedEvent(annex2))
        annex3.confidential = True
        notify(ObjectModifiedEvent(annex3))
        annex4.confidential = True
        notify(ObjectModifiedEvent(annex4))
        annex_decision2.confidential = True
        notify(ObjectModifiedEvent(annex_decision2))
        # select the right category
        item.setCategory(development.getId())
        item.at_post_edit_script()
        self.validateItem(item)

        # power observers may access items when it is 'presented'
        self.changeUser('pmManager')
        self.create('Meeting', date='2015/01/01')
        self.presentItem(item)
        self.changeUser('powerobserver1')
        cleanRamCacheFor('Products.PloneMeeting.adapters._user_groups')
        # powerobservers1 is not member of 'vendors_observers' so he
        # will not be able to access the annexes of the item
        vendors_observers = 'vendors_observers'
        self.assertTrue(vendors_observers not in self.member.getGroups())
        self.hasPermission(View, item)
        # not confidential annex is viewable, but not annexes that are confidential
        categorized_uids = [elt['UID'] for elt in get_categorized_elements(item)]
        # annex1 and annex2 do not use annexTypes viewable to power_observers
        self.assertFalse(annex1.confidential)
        self.assertFalse(annex1.UID() in categorized_uids)
        self.assertTrue(annex2.confidential)
        self.assertFalse(annex2.UID() in categorized_uids)
        # an annex using "annexeCahier" or "courrier-a-valider-par-le-college" will be viewable by power observers
        self.assertTrue(annex3.UID() in categorized_uids)
        self.assertTrue(annex4.UID() in categorized_uids)
        # every decision annexes are viewable by power observers
        self.assertTrue(annex_decision1.UID() in categorized_uids)
        self.assertTrue(annex_decision2.UID() in categorized_uids)
        # if we assign 'powerobserver1' to the 'vendors_observers' group
        # he will be able to view the annexes of item as he is in charge of
        self.portal.portal_groups.addPrincipalToGroup('powerobserver1', vendors_observers)
        # log again as 'powerobserver1' so getGroups is refreshed
        self.changeUser('powerobserver1')
        cleanRamCacheFor('Products.PloneMeeting.adapters._user_groups')
        categorized_uids = [elt['UID'] for elt in get_categorized_elements(item)]
        self.assertTrue(annex1.UID() in categorized_uids)
        self.assertTrue(annex2.UID() in categorized_uids)
        self.assertTrue(annex3.UID() in categorized_uids)
        self.assertTrue(annex4.UID() in categorized_uids)
        # every decision annexes are viewable by power observers
        self.assertTrue(annex_decision1.UID() in categorized_uids)
        self.assertTrue(annex_decision2.UID() in categorized_uids)

        # restricted power observers may only access not confidential annexes
        self.changeUser('restrictedpowerobserver1')
        cleanRamCacheFor('Products.PloneMeeting.adapters._user_groups')
        categorized_uids = [elt['UID'] for elt in get_categorized_elements(item)]
        self.assertTrue(annex1.UID() in categorized_uids)
        self.assertFalse(annex2.UID() in categorized_uids)
        self.assertFalse(annex3.UID() in categorized_uids)
        self.assertFalse(annex4.UID() in categorized_uids)
        # only not confidential decision annexes are viewable by restricted power observers
        self.assertTrue(annex_decision1.UID() in categorized_uids)
        self.assertFalse(annex_decision2.UID() in categorized_uids)

    def test_ItemReference(self):
        '''Test item reference generation. It uses CustomMeeting.getItemNumsForActe.'''
        # use categories
        self.changeUser('siteadmin')
        cfg = self.meetingConfig
        self.create('MeetingCategory', id='maintenance', title='Maintenance', categoryId='maintenance')
        cfg.setUseGroupsAsCategories(False)
        cfg.setInsertingMethodsOnAddItem((
            {'insertingMethod': 'on_list_type', 'reverse': '0'},
            {'insertingMethod': 'on_categories', 'reverse': '0'}))
        cfg.setItemReferenceFormat('python: here.adapted().getItemRefForActe()')
        self.changeUser('pmManager')
        # remove recurring items
        self._removeConfigObjectsFor(cfg)
        # create 5 items using different categories and insert it in a meeting
        resItem1 = self.create('MeetingItem')
        resItem1.setCategory('research')
        resItem2 = self.create('MeetingItem')
        resItem2.setCategory('research')
        # use proposingGroup 'vendors' so it is not viewable by 'pmCreator1'
        devItem1 = self.create('MeetingItem', proposingGroup='vendors')
        devItem1.setCategory('development')
        devItem2 = self.create('MeetingItem')
        devItem2.setCategory('development')
        maintItem1 = self.create('MeetingItem')
        maintItem1.setCategory('maintenance')
        meeting = self.create('Meeting', date='2015/01/01')
        self.presentItem(resItem1)
        self.presentItem(resItem2)
        self.presentItem(devItem1)
        self.presentItem(devItem2)
        self.presentItem(maintItem1)
        # no itemReference until meeting is frozen
        self.assertEquals([item.getItemReference() for item in meeting.getItems(ordered=True)],
                          ['', '', '', '', ''])
        self.freezeMeeting(meeting)
        # check that item references are correct
        self.assertEquals([item.getItemReference() for item in meeting.getItems(ordered=True)],
                          ['development1', 'development2', 'research1', 'research2', 'maintenance1'])
        self.assertEquals([item.getId() for item in meeting.getItems(ordered=True)],
                          ['o3', 'o4', 'o1', 'o2', 'o5'])
        # change position of items 1 and 2, itemReference is changed too
        changeOrder = resItem1.restrictedTraverse('@@change-item-order')
        changeOrder(moveType='down')
        self.assertEquals([item.getItemReference() for item in meeting.getItems(ordered=True)],
                          ['development1', 'development2', 'research1', 'research2', 'maintenance1'])
        self.assertEquals([item.getId() for item in meeting.getItems(ordered=True)],
                          ['o3', 'o4', 'o2', 'o1', 'o5'])
        # move depItem2 to last position
        changeOrder = resItem2.restrictedTraverse('@@change-item-order')
        changeOrder('number', '5')
        # now depItem1 reference is back to 'deployment1' and depItem2 in last position
        self.assertEquals([item.getItemReference() for item in meeting.getItems(ordered=True)],
                          ['development1', 'development2', 'research1', 'maintenance1', 'research2'])
        self.assertEquals([item.getId() for item in meeting.getItems(ordered=True)],
                          ['o3', 'o4', 'o1', 'o5', 'o2'])

        # if we insert a new item, references are updated
        newItem = self.create('MeetingItem')
        newItem.setCategory('development')
        self.presentItem(newItem)
        # item is inserted at the end
        self.assertEquals([item.getItemReference() for item in meeting.getItems(ordered=True)],
                          ['development1', 'development2', 'development3', 'research1', 'maintenance1', 'research2'])
        self.assertEquals([item.getId() for item in meeting.getItems(ordered=True)],
                          ['o3', 'o4', 'o7', 'o1', 'o5', 'o2'])

        # now if we remove an item from the meeting, reference are still correct
        # remove item with ref 'research1', the first item, the item that had 'research2' will get 'research1'
        self.backToState(resItem1, 'validated')
        self.assertEquals([item.getItemReference() for item in meeting.getItems(ordered=True)],
                          ['development1', 'development2', 'development3', 'maintenance1', 'research1'])
        self.assertEquals([item.getId() for item in meeting.getItems(ordered=True)],
                          ['o3', 'o4', 'o7', 'o5', 'o2'])

        # delete item having reference 'development2'
        # only Manager may delete an item
        self.changeUser('admin')
        self.deleteAsManager(devItem2.UID())
        self.assertEquals([item.getItemReference() for item in meeting.getItems(ordered=True)],
                          ['development1', 'development2', 'maintenance1', 'research1'])
        self.assertEquals([item.getId() for item in meeting.getItems(ordered=True)],
                          ['o3', 'o7', 'o5', 'o2'])

        # if we change the category used for an item, reference are updated accordingly
        # change category for resItem1 from 'research' to 'development'
        resItem2.setCategory('development')
        resItem2.at_post_edit_script()
        self.assertEquals([item.getItemReference() for item in meeting.getItems(ordered=True)],
                          ['development1', 'development2', 'maintenance1', 'development3'])
        self.assertEquals([item.getId() for item in meeting.getItems(ordered=True)],
                          ['o3', 'o7', 'o5', 'o2'])

        # test late items, reference is HOJ.1, HOJ.2, ...
        self.changeUser('pmManager')
        lateItem1 = self.create('MeetingItem')
        lateItem1.setCategory('development')
        lateItem1.setPreferredMeeting(meeting.UID())
        lateItem2 = self.create('MeetingItem')
        lateItem2.setCategory('research')
        lateItem2.setPreferredMeeting(meeting.UID())
        self.presentItem(lateItem1)
        self.presentItem(lateItem2)
        self.assertEquals(lateItem1.getItemReference(), 'HOJ.1')
        self.assertEquals(lateItem2.getItemReference(), 'HOJ.2')

        # right now test if the getItemNumsForActe has to be generated by a user
        # that only have access to some items of the meeting.  Indeed, let's say
        # a MeetingManager is on an item and removes it from the meeting, getItemNumsForActe
        # is not recomputed as not called on the item view, if another user access an
        # item or the meeting, this time it will be recomputed
        self.assertEquals(lateItem1.getItemReference(), 'HOJ.1')
        self.assertEquals(newItem.getItemReference(), 'development2')
        self.backToState(lateItem1, 'validated')
        self.backToState(newItem, 'validated')
        self.changeUser('pmCreator1')
        # no more reference for lateItem1 and depItem2
        self.assertEquals(lateItem1.getItemReference(), '')
        self.assertEquals(newItem.getItemReference(), '')
        # pmCreator1 is not able to access every items of the meeting
        self.assertFalse(self.hasPermission(View, devItem1))
        # if we get the reference of other items, it is correct,
        # getItemNumsForActe have been recomputed
        self.assertEquals([item.getItemReference() for item in meeting.getItems(ordered=True,
                                                                                unrestricted=True)],
                          ['development1', 'maintenance1', 'development2', 'HOJ.1'])
        self.assertEquals(devItem1.getItemReference(), 'development1')
        # no more in the meeting
        self.assertEquals(resItem1.getItemReference(), '')
        self.assertEquals(resItem2.getItemReference(), 'development2')
        self.assertEquals(lateItem2.getItemReference(), 'HOJ.1')

    def test_InsertingMethodOnDecisionFirstWord(self):
        '''
          Test our custom inserting method 'on_decision_first_word'.
        '''
        cfg = self.meetingConfig
        self.changeUser('pmManager')
        self._removeConfigObjectsFor(cfg)
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
        self.assertTrue(item1_order < item3_order < item2_order ==
                        item5_order < item7_order < item4_order < item6_order)
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
        cfg.setInsertingMethodsOnAddItem(insertingMethods)
        meeting = self.create('Meeting', date='2015/01/01')
        for item in item1, item2, item3, item4, item5, item6, item7:
            self.presentItem(item)
        # items should have been added respecting following order item3, item2, item5, item4, item6, item1
        self.assertTrue([item.getId() for item in meeting.getItems(ordered=True)] ==
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
        cfg = self.meetingConfig
        cfg2 = self.meetingConfig2
        cfg2Id = cfg2.getId()
        cfg.setItemAutoSentToOtherMCStates(cfg.getItemAutoSentToOtherMCStates() + ('itemfrozen', ))

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
                                 'meetingadvicefinances',
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
        # finance group get automatically access to the duplicatedItem as it is linked manually
        self.assertTrue(duplicatedItem.__ac_local_roles__[financeGroupAdvisersId] == ['Reader'])

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
        self.assertTrue(financeGroupAdvisersId not in clonedDelayedItem.__ac_local_roles__)

        # now correct item and 'accept and return' it
        # this time, the original item is considered the finance advice holder
        self.do(item, 'backToItemFrozen')
        self.do(item, 'return')
        # find the new item created by the clone as item is already the predecessor of 'duplicatedItem'
        clonedReturnedItem = [newItem for newItem in item.getBRefs('ItemPredecessor')
                              if newItem not in (duplicatedItem, clonedDelayedItem)][0]
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

        # send the clonedReturnedItem to Council and check with the council item
        clonedReturnedItem.setOtherMeetingConfigsClonableTo('meeting-config-council')
        self.presentItem(clonedReturnedItem)
        self.assertEquals(clonedReturnedItem.queryState(), 'itemfrozen')
        # still right, including sent item
        self.assertEquals(clonedReturnedItem.adapted().getItemWithFinanceAdvice(), item)
        self.assertEquals(
            clonedReturnedItem.getItemClonedToOtherMC(cfg2Id).adapted().getItemWithFinanceAdvice(),
            item)
        # now test if setting an optional finance advice does not break getItemWithFinanceAdvice
        clonedReturnedItem.setOptionalAdvisers((FINANCE_GROUP_IDS[0], ))
        clonedReturnedItem.updateLocalRoles()
        self.assertTrue(FINANCE_GROUP_IDS[0] in clonedReturnedItem.adviceIndex)
        self.assertEquals(clonedReturnedItem.adapted().getItemWithFinanceAdvice(), item)
        self.assertEquals(
            clonedReturnedItem.getItemClonedToOtherMC(cfg2Id).adapted().getItemWithFinanceAdvice(),
            item)

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
        self.assertEquals(itemInCouncil1.getFinanceAdvice(), FINANCE_GROUP_IDS[0])
        self.assertTrue(itemInCouncil1.adapted().getItemWithFinanceAdvice() == itemToCouncil1)
        # finance group gets automatically access to the itemInCouncil1
        self.assertTrue(itemInCouncil1.__ac_local_roles__[financeGroupAdvisersId] == ['Reader'])
        # accept_and_return itemToCouncil2 and check
        self.do(itemToCouncil2, 'accept_and_return')
        itemInCouncil2 = itemToCouncil2.getItemClonedToOtherMC('meeting-config-council')
        self.assertEquals(itemInCouncil2.getFinanceAdvice(), FINANCE_GROUP_IDS[0])
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

        # duplicate and keep link an 'accepted_and_return' college item,
        # the financeAdvice will not follow
        duplicatedItemUrl = itemToCouncil2.onDuplicateAndKeepLink()
        duplicatedItemId = duplicatedItemUrl.split('/')[-1]
        duplicatedItem2 = getattr(itemToCouncil2.getParentNode(), duplicatedItemId)
        self.assertEquals(duplicatedItem2.adapted().getItemWithFinanceAdvice(), duplicatedItem2)

    def test_GetLegalTextForFDAdvice(self):
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
        item1a = self.create('MeetingItem', title='Item with positive with remarks advice')
        item1a.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        item2 = self.create('MeetingItem', title='Item with negative advice')
        item2.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        item3 = self.create('MeetingItem', title='Item with no advice')
        item3.setFinanceAdvice(FINANCE_GROUP_IDS[0])

        self.proposeItem(item1)
        self.proposeItem(item1a)
        self.proposeItem(item2)
        self.proposeItem(item3)
        self.do(item1, 'proposeToFinance')
        item1.setCompleteness('completeness_complete')
        self.do(item1a, 'proposeToFinance')
        item1a.setCompleteness('completeness_complete')
        self.do(item2, 'proposeToFinance')
        item2.setCompleteness('completeness_complete')
        self.do(item3, 'proposeToFinance')
        item3.setCompleteness('completeness_complete')
        item3.updateLocalRoles()
        item3.adviceIndex[item3.getFinanceAdvice()]['delay_started_on'] = datetime(2012, 1, 1)
        item3.updateLocalRoles()

        self.changeUser('pmFinManager')
        advice1 = createContentInContainer(
            item1,
            'meetingadvicefinances',
            **{'advice_group': FINANCE_GROUP_IDS[0],
               'advice_type': 'positive_finance',
               'advice_comment': RichTextValue(u'My good comment finance')})
        advice1a = createContentInContainer(
            item1a,
            'meetingadvicefinances',
            **{'advice_group': FINANCE_GROUP_IDS[0],
               'advice_type': 'positive_with_remarks_finance',
               'advice_comment': RichTextValue(u'My good with remarks comment finance')})
        advice2 = createContentInContainer(
            item2,
            'meetingadvicefinances',
            **{'advice_group': FINANCE_GROUP_IDS[0],
               'advice_type': 'negative_finance',
               'advice_comment': RichTextValue(u'My bad comment finance')})

        # send to financial reviewer
        self.changeUser('pmFinController')
        self.do(advice1, 'proposeToFinancialReviewer')
        self.do(advice1a, 'proposeToFinancialReviewer')
        self.do(advice2, 'proposeToFinancialReviewer')
        # send to finance manager
        self.do(advice1, 'proposeToFinancialManager')
        self.do(advice1a, 'proposeToFinancialManager')
        self.do(advice2, 'proposeToFinancialManager')
        # sign the advice
        self.do(advice1, 'signFinancialAdvice')
        self.do(advice1a, 'signFinancialAdvice')
        self.do(advice2, 'signFinancialAdvice')

        financialStuff1 = item1.adapted().getFinancialAdviceStuff()
        financialStuff1a = item1a.adapted().getFinancialAdviceStuff()
        # positive_with_remarks 'advice_type' is printed like 'positive'
        self.assertEquals(financialStuff1['advice_type'], financialStuff1a['advice_type'])
        financialStuff2 = item2.adapted().getFinancialAdviceStuff()
        advice1 = item1.getAdviceDataFor(item1, item1.getFinanceAdvice())
        advice1a = item1a.getAdviceDataFor(item1a, item1a.getFinanceAdvice())
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
        self.assertTrue(item1a.adapted().getLegalTextForFDAdvice() == res1)
        self.assertTrue(item2.adapted().getLegalTextForFDAdvice() == res2)
        self.assertTrue(item3.adapted().getLegalTextForFDAdvice() == res3)

        self.assertTrue(item1.adapted().getLegalTextForFDAdvice(isMeeting=True) == res4)
        self.assertTrue(item1a.adapted().getLegalTextForFDAdvice(isMeeting=True) == res4)
        self.assertTrue(item2.adapted().getLegalTextForFDAdvice(isMeeting=True) == res5)
        self.assertTrue(item3.adapted().getLegalTextForFDAdvice(isMeeting=True) == res6)

    def test_MayGenerateFDAdvice(self):
        '''An advice can be generated when:
            -at least one advice is asked.
            -the advice is not hidden OR the user is in
                the right FD group OR the advice is no
                longer editable
        '''
        self.changeUser('admin')
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # add finance groups
        _createFinanceGroups(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        self.changeUser('pmManager')
        item1 = self.create('MeetingItem', title='Item with advice')
        # if no advice is asked, mayGenerate returns False.
        self.assertFalse(item1.adapted().mayGenerateFDAdvice())

        item1.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        self.proposeItem(item1)
        self.do(item1, 'proposeToFinance')
        item1.setCompleteness('completeness_complete')

        self.changeUser('pmFinManager')
        advice1 = createContentInContainer(item1,
                                           'meetingadvicefinances',
                                           **{'advice_group': FINANCE_GROUP_IDS[0],
                                              'advice_type': 'positive_finance',
                                              'advice_comment': RichTextValue(u'My comment finance')})
        # if advice is hidden, it can only be seen by advisers of the finance group.
        advice1.advice_hide_during_redaction = True
        self.changeUser('pmManager')
        self.assertFalse(item1.adapted().mayGenerateFDAdvice())

        self.changeUser('pmFinController')
        self.assertTrue(item1.adapted().mayGenerateFDAdvice())
        self.do(advice1, 'proposeToFinancialReviewer')

        self.changeUser('pmFinReviewer')
        self.assertTrue(item1.adapted().mayGenerateFDAdvice())
        self.do(advice1, 'proposeToFinancialManager')

        self.assertTrue(item1.adapted().mayGenerateFDAdvice())

        self.changeUser('pmCreator1')
        self.assertFalse(item1.adapted().mayGenerateFDAdvice())

        item1.adviceIndex[item1.getFinanceAdvice()]['delay_started_on'] = datetime(2012, 1, 1)
        item1.updateLocalRoles()

        self.assertTrue(item1.adapted().mayGenerateFDAdvice())

    def test_DecisionAnnexesNotKeptOnDuplicated(self):
        """When an item is duplicated using the 'duplicate and keep link',
           we do not keep the decision annexes."""
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        self.addAnnex(item)
        self.addAnnex(item, relatedTo='item_decision')
        self.assertTrue(get_annexes(item, portal_types=['annex']))
        self.assertTrue(get_annexes(item, portal_types=['annexDecision']))
        # cloned and link not kept, decison annexes are removed
        clonedItem = item.clone()
        self.assertTrue(get_annexes(clonedItem, portal_types=['annex']))
        self.assertFalse(get_annexes(clonedItem, portal_types=['annexDecision']))
        # cloned but link kept, decison annexes are also removed
        clonedItemWithLink = item.clone(setCurrentAsPredecessor=True)
        self.assertTrue(get_annexes(clonedItemWithLink, portal_types=['annex']))
        self.assertFalse(get_annexes(clonedItemWithLink, portal_types=['annexDecision']))

    def test_GetOfficeManager(self):
        self.changeUser('pmManager')

        # simple item following the workflow until it is validated.
        itemValidated = self.create('MeetingItem')
        self.do(itemValidated, 'proposeToAdministrativeReviewer')
        self.do(itemValidated, 'proposeToInternalReviewer')
        self.do(itemValidated, 'proposeToDirector')
        self.do(itemValidated, 'validate')
        # item directly validated from the created state. This one has no
        # informations about office manager because he didn't go through
        # the state "proposedToDirector"
        itemDirectlyValidated = self.create('MeetingItem')
        self.do(itemDirectlyValidated, 'validate')

        # Item that gonna be postponed and directly presented to another meeting
        itemToReturn = self.create('MeetingItem')
        self.do(itemToReturn, 'proposeToAdministrativeReviewer')
        self.do(itemToReturn, 'proposeToInternalReviewer')
        self.do(itemToReturn, 'proposeToDirector')
        self.do(itemToReturn, 'validate')

        # Item that gonna be postponed, presented to another meeting and then
        # postponed and presented a second time.
        itemToReturnTwice = self.create('MeetingItem')
        self.do(itemToReturnTwice, 'proposeToAdministrativeReviewer')
        self.do(itemToReturnTwice, 'proposeToInternalReviewer')
        self.do(itemToReturnTwice, 'proposeToDirector')
        self.do(itemToReturnTwice, 'validate')

        # Creates a meeting, presents and postpones the items.
        meeting = self.create('Meeting', date='2014/01/01 09:00:00')
        self.presentItem(itemToReturn)
        self.presentItem(itemToReturnTwice)
        self.decideMeeting(meeting)
        self.do(itemToReturn, 'return')
        self.do(itemToReturnTwice, 'return')

        # Gets the items which have been duplicated when postponed.
        itemReturned = itemToReturn.getBRefs('ItemPredecessor')[0]
        itemReturnedOnce = itemToReturnTwice.getBRefs('ItemPredecessor')[0]

        # Put back the meeting in creation to add the duplicated item into it.
        # Presents and postpones again.
        self.backToState(meeting, 'created')
        self.presentItem(itemReturnedOnce)
        self.decideMeeting(meeting)
        self.do(itemReturnedOnce, 'return')
        itemReturnedTwice = itemReturnedOnce.getBRefs('ItemPredecessor')[0]

        # Checks if we have the infos of the office manager when we are supposed
        # to have it.
        pmManagerObj = self.portal.portal_membership.getMemberById('pmManager')
        pmManagerObj.setProperties(description='0497/696969     brol')

        self.assertEqual(itemValidated.adapted().getOfficeManager()['fullname'], 'M. PMManager')
        self.assertEqual(itemValidated.adapted().getOfficeManager()['phone'], '0497/696969')
        self.assertEqual(itemValidated.adapted().getOfficeManager()['email'], 'pmmanager@plonemeeting.org')

        self.assertEqual(itemDirectlyValidated.adapted().getOfficeManager(), '')

        self.assertEqual(itemReturned.adapted().getOfficeManager()['fullname'], 'M. PMManager')
        self.assertEqual(itemReturned.adapted().getOfficeManager()['phone'], '0497/696969')
        self.assertEqual(itemReturned.adapted().getOfficeManager()['email'], 'pmmanager@plonemeeting.org')

        self.assertEqual(itemReturnedTwice.adapted().getOfficeManager()['fullname'], 'M. PMManager')
        self.assertEqual(itemReturnedTwice.adapted().getOfficeManager()['phone'], '0497/696969')
        self.assertEqual(itemReturnedTwice.adapted().getOfficeManager()['email'], 'pmmanager@plonemeeting.org')

    def test_ItemSignableSooner(self):
        """itemIsSigned can be changed when item is 'presented' or 'itemfrozen'."""
        self.changeUser('pmManager')
        item = self.create('MeetingItem')
        meeting = self.create('Meeting', date='2015/05/05')
        self.assertFalse(item.adapted().maySignItem())
        self.validateItem(item)
        self.assertFalse(item.adapted().maySignItem())
        # ok, now present the item, it will be signable
        self.presentItem(item)
        self.assertEquals(item.queryState(), 'presented')
        self.assertTrue(item.maySignItem())
        self.freezeMeeting(meeting)
        self.assertEquals(item.queryState(), 'itemfrozen')
        self.assertTrue(item.maySignItem())
        self.closeMeeting(meeting)
        self.assertEquals(item.queryState(), 'accepted')
        self.assertTrue(item.maySignItem())

    def test_ItemSetToAddendum(self):
        """When an item is set to/from 'addendum', it's itemNumber
           is automatically adapted accordingly.  An 'addendum' item
           will use a subnumber."""
        self.setMeetingConfig(self.meetingConfig2.getId())
        self.changeUser('pmManager')
        item = self.create('MeetingItem')
        meeting = self.create('Meeting', date=DateTime())
        self.presentItem(item)
        self.freezeMeeting(meeting)

        # not possible to set item to 'addendum' as it is the only item in the meeting
        # and subcall to "change item number" breaks and listType is not changed
        view = item.restrictedTraverse('@@change-item-listtype')
        view('addendum')
        self.assertEquals(item.getListType(), 'normal')
        item2 = self.create('MeetingItem')
        self.presentItem(item2)
        # first item of the meeting may not be set to 'addendum'
        self.assertEquals(item.getItemNumber(), 100)
        view('addendum')
        self.assertEquals(item.getListType(), 'normal')

        # set second item to 'addendum'
        view = item2.restrictedTraverse('@@change-item-listtype')
        view('addendum')
        # now it is addendum and itemNumber as been set to a subnumber
        self.assertEquals(item2.getListType(), 'addendum')
        self.assertEquals(item2.getItemNumber(), 101)
        # back to 'normal', itemNumber is set back to an integer
        view('normal')
        self.assertEquals(item2.getItemNumber(), 200)

    def test_SentenceAppendedToCouncilItemDecisionEndWhenPresented(self):
        """When a council item is presented, it's decisionEnd field is adapted,
           a particular sentence is added at the end of the field."""
        cfg2 = self.meetingConfig2
        cfg2Id = cfg2.getId()
        self.changeUser('pmManager')
        self.setMeetingConfig(cfg2Id)
        self.create('Meeting', date=DateTime('2015/11/11'))
        FIRST_SENTENCE = '<p>A first sentence.</p>'
        item = self.create('MeetingItem')
        item.setDecisionEnd(FIRST_SENTENCE)
        self.assertEquals(item.getDecisionEnd(), FIRST_SENTENCE)
        # present item, special sentence will be appended
        self.presentItem(item)
        self.assertEquals(item.getDecisionEnd(),
                          FIRST_SENTENCE + COUNCILITEM_DECISIONEND_SENTENCE)
        # not appended twice, create an item that already ends with sentence
        # more over add an extra empty <p></p> at the end
        item2 = self.create('MeetingItem')
        item2.setDecisionEnd(FIRST_SENTENCE + COUNCILITEM_DECISIONEND_SENTENCE + '<p>&nbsp;</p>')
        self.assertEquals(item2.getDecisionEnd(),
                          FIRST_SENTENCE + COUNCILITEM_DECISIONEND_SENTENCE + '<p>&nbsp;</p>')
        self.presentItem(item2)
        self.assertEquals(item2.getDecisionEnd(),
                          FIRST_SENTENCE + COUNCILITEM_DECISIONEND_SENTENCE + '<p>&nbsp;</p>')

    def test_PrintFDStats(self):

        self.changeUser('admin')
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # add finance groups
        _createFinanceGroups(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # Create item 1 with an advice asked to df-contrale.
        self.changeUser('pmManager')
        item1 = self.create('MeetingItem', title='Item1 with advice')

        item1.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        self.proposeItem(item1)
        self.do(item1, 'proposeToFinance')
        self.changeUser('pmFinController')
        # Set completeness to complete.
        changeCompleteness = item1.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()

        # Add a negative advice.
        self.changeUser('pmFinManager')
        advice1 = createContentInContainer(item1,
                                           'meetingadvicefinances',
                                           **{'advice_group': FINANCE_GROUP_IDS[0],
                                              'advice_type': 'negative_finance',
                                              'advice_comment': RichTextValue(u'My bad comment finance')})
        self.changeUser('pmFinController')
        self.do(advice1, 'proposeToFinancialReviewer')

        self.changeUser('pmFinReviewer')
        self.do(advice1, 'proposeToFinancialManager')

        # Sign the advice which is sent back to director.
        self.changeUser('pmFinManager')
        self.do(advice1, 'signFinancialAdvice')

        # Propose to finance for the second time
        self.changeUser('pmManager')
        self.do(item1, 'proposeToFinance')
        self.changeUser('pmFinController')
        # Set the completeness to incomplete with a comment.
        changeCompleteness = item1.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_incomplete')
        self.request['comment'] = 'You are not complete'
        self.request.form['form.submitted'] = True
        changeCompleteness()

        # Send the item back to internal reviewer due to his incompleteness.
        self.changeUser('pmManager')
        self.do(item1,
                'backToProposedToInternalReviewer',
                comment="Go back to the abyss"
                )
        self.do(item1, 'proposeToDirector')
        self.do(item1, 'proposeToFinance')
        self.changeUser('pmFinController')
        # Let assume that the item is now complete. So set the completeness.
        changeCompleteness = item1.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()

        # Give a positive advice
        advice1.advice_type = 'positive_finance'
        # Erase the comment
        advice1.advice_comment = RichTextValue('')
        notify(ObjectModifiedEvent(advice1))

        self.changeUser('pmFinController')
        self.do(advice1, 'proposeToFinancialReviewer')

        self.changeUser('pmFinReviewer')
        self.do(advice1, 'proposeToFinancialManager')

        # Sign the advice so the item is validated.
        self.changeUser('pmFinManager')
        self.do(advice1, 'signFinancialAdvice')

        # Setup needed because we will now try with an advice from
        # df-comptabilita-c-et-audit-financier. Since the finance users don't
        # have basically the right to handle that sort of advice, we give them
        # the right here.
        groupsTool = api.portal.get_tool('portal_groups')
        # add pmFinController, pmFinReviewer and pmFinManager to advisers and to their respective finance group
        groupsTool.addPrincipalToGroup('pmFinController', '%s_advisers' % FINANCE_GROUP_IDS[1])
        groupsTool.addPrincipalToGroup('pmFinReviewer', '%s_advisers' % FINANCE_GROUP_IDS[1])
        groupsTool.addPrincipalToGroup('pmFinManager', '%s_advisers' % FINANCE_GROUP_IDS[1])
        groupsTool.addPrincipalToGroup('pmFinController', '%s_financialcontrollers' % FINANCE_GROUP_IDS[1])
        groupsTool.addPrincipalToGroup('pmFinReviewer', '%s_financialreviewers' % FINANCE_GROUP_IDS[1])
        groupsTool.addPrincipalToGroup('pmFinManager', '%s_financialmanagers' % FINANCE_GROUP_IDS[1])

        # Create the second item with advice.
        self.changeUser('pmManager')
        item2 = self.create('MeetingItem', title='Item2 with advice')
        item2.setFinanceAdvice(FINANCE_GROUP_IDS[1])
        self.proposeItem(item2)
        self.do(item2, 'proposeToFinance')
        self.changeUser('pmFinController')
        # The item is complete.
        changeCompleteness = item2.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()

        # Give positive advice.
        self.changeUser('pmFinManager')
        advice2 = createContentInContainer(item2,
                                           'meetingadvicefinances',
                                           **{'advice_group': FINANCE_GROUP_IDS[1],
                                              'advice_type': 'positive_finance'})

        self.changeUser('pmFinController')
        self.do(advice2, 'proposeToFinancialReviewer')

        self.changeUser('pmFinReviewer')
        self.do(advice2, 'proposeToFinancialManager')

        # Sign the advice, item is now validated.
        self.changeUser('pmFinManager')
        self.do(advice2, 'signFinancialAdvice')

        # Present this item to a meeting.
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date='2019/09/19')
        # Delete recurring items.
        self.deleteAsManager(meeting.getItems()[0].UID())
        self.deleteAsManager(meeting.getItems()[0].UID())
        self.presentItem(item2)

        # Create the third item with advice which gonna be timed out..
        self.changeUser('pmManager')
        item3 = self.create('MeetingItem', title='Item3 with advice timed out')
        item3.setFinanceAdvice(FINANCE_GROUP_IDS[1])
        self.proposeItem(item3)
        self.do(item3, 'proposeToFinance')
        self.changeUser('pmFinController')
        # The item is complete.
        changeCompleteness = item3.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()

        # Give negative advice.
        self.changeUser('pmFinManager')
        advice3 = createContentInContainer(item3,
                                           'meetingadvicefinances',
                                           **{'advice_group': FINANCE_GROUP_IDS[1],
                                              'advice_type': 'negative_finance'})

        self.changeUser('pmFinController')
        self.do(advice3, 'proposeToFinancialReviewer')

        self.changeUser('pmFinReviewer')
        self.do(advice3, 'proposeToFinancialManager')

        # Sign the advice so the item is returned to director.
        self.changeUser('pmFinManager')
        self.do(advice3, 'signFinancialAdvice')

        # Propose to finance a second time.
        self.changeUser('pmManager')
        self.do(item3, 'proposeToFinance')
        self.changeUser('pmFinController')
        # Item is still complete.
        changeCompleteness = item3.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()

        # Now, finance will forget this item and make it expire.
        item3.adviceIndex[FINANCE_GROUP_IDS[1]]['delay_started_on'] = datetime(2016, 1, 1)
        item3.updateLocalRoles()

        # Create the fourth item without advice, but timed out too.
        self.changeUser('pmManager')
        item4 = self.create('MeetingItem', title='Item4 timed out without advice')
        item4.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        self.proposeItem(item4)
        self.do(item4, 'proposeToFinance')
        self.changeUser('pmFinController')
        # The item is complete.
        changeCompleteness = item4.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()

        # Now, finance will forget this item and make it expire.
        item4.adviceIndex[FINANCE_GROUP_IDS[0]]['delay_started_on'] = datetime(2016, 1, 1)
        item4.updateLocalRoles()

        # Create the fifth item with a bad advice and then remove financial impact.
        self.changeUser('pmManager')
        item5 = self.create('MeetingItem', title='Item5 with advice')

        item5.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        self.proposeItem(item5)
        self.do(item5, 'proposeToFinance')
        self.changeUser('pmFinController')
        # Set completeness to complete.
        changeCompleteness = item5.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()

        # Add a negative advice.
        self.changeUser('pmFinManager')
        advice5 = createContentInContainer(item5,
                                           'meetingadvicefinances',
                                           **{'advice_group': FINANCE_GROUP_IDS[0],
                                              'advice_type': 'negative_finance',
                                              'advice_comment': RichTextValue(u'Bad comment finance')})
        self.changeUser('pmFinController')
        self.do(advice5, 'proposeToFinancialReviewer')

        self.changeUser('pmFinReviewer')
        self.do(advice5, 'proposeToFinancialManager')

        # Sign the advice which is sent back to director.
        self.changeUser('pmFinManager')
        self.do(advice5, 'signFinancialAdvice')

        # Remove the financial impact.
        item5.setFinanceAdvice('_none_')

        # Create the sixth item with positive advice with remarks.
        self.changeUser('pmManager')
        item6 = self.create('MeetingItem', title='Item6 with positive advice with remarks')
        item6.setFinanceAdvice(FINANCE_GROUP_IDS[1])
        self.proposeItem(item6)
        self.do(item6, 'proposeToFinance')
        self.changeUser('pmFinController')
        # The item is complete.
        changeCompleteness = item6.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()

        # Give positive advice.
        self.changeUser('pmFinManager')
        advice6 = createContentInContainer(item6,
                                           'meetingadvicefinances',
                                           **{'advice_group': FINANCE_GROUP_IDS[1],
                                              'advice_type': 'positive_with_remarks_finance',
                                              'advice_comment': RichTextValue(u'A remark')})

        self.changeUser('pmFinController')
        self.do(advice6, 'proposeToFinancialReviewer')

        self.changeUser('pmFinReviewer')
        self.do(advice6, 'proposeToFinancialManager')

        # Sign the advice, item is now validated.
        self.changeUser('pmFinManager')
        self.do(advice6, 'signFinancialAdvice')

        # Needed to make believe that the finance advice are checked in the
        # dashboard.
        self.changeUser('pmCreator1')
        item1.REQUEST.set('facetedQuery',
                          '{"c7":["delay_real_group_id__unique_id_002",\
                                  "delay_real_group_id__unique_id_003",\
                                  "delay_real_group_id__unique_id_004",\
                                  "delay_real_group_id__unique_id_005",\
                                  "delay_real_group_id__unique_id_006",\
                                  "delay_real_group_id__unique_id_007"]}')
        # Get a folder which is needed to call the view on it.
        folder = self.tool.getPloneMeetingFolder('meeting-config-college', 'pmCreator1').searches_items
        view = folder.restrictedTraverse('document_generation_helper_view')
        catalog = api.portal.get_tool('portal_catalog')
        results = view.printFDStats(catalog(portal_type='MeetingItemCollege', sort_on='id'))

        self.assertEquals(results[0]['title'], "Item1 with advice")
        self.assertEquals(results[0]['meeting_date'], "")
        self.assertEquals(results[0]['group'], "Developers")
        self.assertEquals(results[0]['end_advice'], "OUI")
        self.assertEquals(results[0]['comments'], "")
        self.assertEquals(results[0]['adviser'], u'DF - Contr\xf4le')
        self.assertEquals(results[0]['advice_type'], "Avis finance favorable")

        self.assertEquals(results[1]['title'], "Item1 with advice")
        self.assertEquals(results[1]['meeting_date'], "")
        self.assertEquals(results[1]['group'], "Developers")
        self.assertEquals(results[1]['end_advice'], "")
        self.assertEquals(results[1]['comments'], "Go back to the abyssYou are not complete")
        self.assertEquals(results[1]['adviser'], u'DF - Contr\xf4le')
        self.assertEquals(results[1]['advice_type'], 'Renvoy\xc3\xa9 au validateur interne pour incompl\xc3\xa9tude')

        self.assertEquals(results[2]['title'], "Item1 with advice")
        self.assertEquals(results[2]['meeting_date'], "")
        self.assertEquals(results[2]['group'], "Developers")
        self.assertEquals(results[2]['end_advice'], "NON")
        self.assertEquals(results[2]['comments'], "My bad comment finance")
        self.assertEquals(results[2]['adviser'], u'DF - Contr\xf4le')
        self.assertEquals(results[2]['advice_type'], 'Avis finance d\xc3\xa9favorable')

        self.assertEquals(results[3]['title'], "Item1 with advice")
        self.assertEquals(results[3]['meeting_date'], "")
        self.assertEquals(results[3]['group'], "Developers")
        self.assertEquals(results[3]['end_advice'], "")
        self.assertEquals(results[3]['comments'], "")
        self.assertEquals(results[3]['adviser'], u'DF - Contr\xf4le')
        self.assertEquals(results[3]['advice_type'], 'Compl\xc3\xa9tude')

        self.assertEquals(results[4]['title'], "Item2 with advice")
        self.assertEquals(results[4]['meeting_date'], "19/09/2019")
        self.assertEquals(results[4]['group'], "Developers")
        self.assertEquals(results[4]['end_advice'], "OUI")
        self.assertEquals(results[4]['comments'], "")
        self.assertEquals(results[4]['adviser'], u'DF - Comptabilit\xe9 et Audit financier')
        self.assertEquals(results[4]['advice_type'], "Avis finance favorable")

        self.assertEquals(results[5]['title'], "Item2 with advice")
        self.assertEquals(results[5]['meeting_date'], "19/09/2019")
        self.assertEquals(results[5]['group'], "Developers")
        self.assertEquals(results[5]['end_advice'], "")
        self.assertEquals(results[5]['comments'], "")
        self.assertEquals(results[5]['adviser'], u'DF - Comptabilit\xe9 et Audit financier')
        self.assertEquals(results[5]['advice_type'], 'Compl\xc3\xa9tude')

        self.assertEquals(results[6]['title'], "Item3 with advice timed out")
        self.assertEquals(results[6]['meeting_date'], "")
        self.assertEquals(results[6]['group'], "Developers")
        self.assertEquals(results[6]['end_advice'], "OUI")
        self.assertEquals(results[6]['comments'], "")
        self.assertEquals(results[6]['adviser'], u'DF - Comptabilit\xe9 et Audit financier')
        self.assertEquals(results[6]['advice_type'], 'Avis finance expir\xc3\xa9')

        self.assertEquals(results[7]['title'], "Item3 with advice timed out")
        self.assertEquals(results[7]['meeting_date'], "")
        self.assertEquals(results[7]['group'], "Developers")
        self.assertEquals(results[7]['end_advice'], "NON")
        self.assertEquals(results[7]['comments'], "")
        self.assertEquals(results[7]['adviser'], u'DF - Comptabilit\xe9 et Audit financier')
        self.assertEquals(results[7]['advice_type'], 'Avis finance d\xc3\xa9favorable')

        self.assertEquals(results[8]['title'], "Item3 with advice timed out")
        self.assertEquals(results[8]['meeting_date'], "")
        self.assertEquals(results[8]['group'], "Developers")
        self.assertEquals(results[8]['end_advice'], "")
        self.assertEquals(results[8]['comments'], "")
        self.assertEquals(results[8]['adviser'], u'DF - Comptabilit\xe9 et Audit financier')
        self.assertEquals(results[8]['advice_type'], 'Compl\xc3\xa9tude')

        self.assertEquals(results[9]['title'], "Item4 timed out without advice")
        self.assertEquals(results[9]['meeting_date'], "")
        self.assertEquals(results[9]['group'], "Developers")
        self.assertEquals(results[9]['end_advice'], "")
        self.assertEquals(results[9]['comments'], "")
        self.assertEquals(results[9]['adviser'], u'DF - Contr\xf4le')
        self.assertEquals(results[9]['advice_type'], 'Avis finance expir\xc3\xa9')

        self.assertEquals(results[10]['title'], "Item4 timed out without advice")
        self.assertEquals(results[10]['meeting_date'], "")
        self.assertEquals(results[10]['group'], "Developers")
        self.assertEquals(results[10]['end_advice'], "")
        self.assertEquals(results[10]['comments'], "")
        self.assertEquals(results[10]['adviser'], u'DF - Contr\xf4le')
        self.assertEquals(results[10]['advice_type'], 'Compl\xc3\xa9tude')

        self.assertEquals(results[11]['title'], "Item5 with advice")
        self.assertEquals(results[11]['meeting_date'], "")
        self.assertEquals(results[11]['group'], "Developers")
        self.assertEquals(results[11]['end_advice'], "OUI")
        self.assertEquals(results[11]['comments'], "Bad comment finance")
        self.assertEquals(results[11]['adviser'], u'DF - Contr\xf4le')
        self.assertEquals(results[11]['advice_type'], 'Avis finance d\xc3\xa9favorable')

        self.assertEquals(results[12]['title'], "Item5 with advice")
        self.assertEquals(results[12]['meeting_date'], "")
        self.assertEquals(results[12]['group'], "Developers")
        self.assertEquals(results[12]['end_advice'], "")
        self.assertEquals(results[12]['comments'], "")
        self.assertEquals(results[12]['adviser'], u'DF - Contr\xf4le')
        self.assertEquals(results[12]['advice_type'], 'Compl\xc3\xa9tude')

        self.assertEquals(results[13]['title'], "Item6 with positive advice with remarks")
        self.assertEquals(results[13]['meeting_date'], "")
        self.assertEquals(results[13]['group'], "Developers")
        self.assertEquals(results[13]['end_advice'], "OUI")
        self.assertEquals(results[13]['comments'], "A remark")
        self.assertEquals(results[13]['adviser'], u'DF - Comptabilit\xe9 et Audit financier')
        self.assertEquals(results[13]['advice_type'], 'Avis finance favorable avec remarques')

        self.assertEquals(results[14]['title'], "Item6 with positive advice with remarks")
        self.assertEquals(results[14]['meeting_date'], "")
        self.assertEquals(results[14]['group'], "Developers")
        self.assertEquals(results[14]['end_advice'], "")
        self.assertEquals(results[14]['comments'], "")
        self.assertEquals(results[14]['adviser'], u'DF - Comptabilit\xe9 et Audit financier')
        self.assertEquals(results[14]['advice_type'], 'Compl\xc3\xa9tude')

    def test_ShowOtherMeetingConfigsClonableToEmergency(self):
        """Condition method to restrict use of field
          MeetingItem.otherMeetingConfigsClonableToEmergency to MeetingManagers.
          Or if it was checked by a MeetingManager, then it appears to normal user,
          so if the normal user uncheck 'clone to', emergency is unchecked as well."""
        cfg = self.meetingConfig
        self.changeUser('siteadmin')
        if 'otherMeetingConfigsClonableToEmergency' not in cfg.getUsedItemAttributes():
            cfg.setUsedItemAttributes(cfg.getUsedItemAttributes() +
                                      ('otherMeetingConfigsClonableToEmergency', ))
        # as notmal user, not viewable
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        item.setOtherMeetingConfigsClonableTo((self.meetingConfig2.getId(), ))
        self.assertFalse(item.adapted().showOtherMeetingConfigsClonableToEmergency())
        # viewable as Manager
        self.changeUser('pmManager')
        self.assertTrue(item.adapted().showOtherMeetingConfigsClonableToEmergency())
        # if set, it will be viewable by common editor
        item.setOtherMeetingConfigsClonableToEmergency((self.meetingConfig2.getId(), ))
        self.changeUser('pmCreator1')
        self.assertTrue(item.adapted().showOtherMeetingConfigsClonableToEmergency())
