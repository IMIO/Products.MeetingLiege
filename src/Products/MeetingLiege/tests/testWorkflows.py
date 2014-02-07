# -*- coding: utf-8 -*-
#
# File: testWorkflows.py
#
# Copyright (c) 2007-2010 by PloneGov
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

from AccessControl import Unauthorized
from DateTime import DateTime
from plone.app.testing.helpers import setRoles
from Products.MeetingLalouviere.tests.MeetingLalouviereTestCase import MeetingLalouviereTestCase
from Products.MeetingCommunes.tests.testWorkflows import testWorkflows as mctw


class testWorkflows(MeetingLalouviereTestCase, mctw):
    """Tests the default workflows implemented in MeetingLalouviere.

       WARNING:
       The Plone test system seems to be bugged: it does not seem to take into
       account the write_permission and read_permission tags that are defined
       on some attributes of the Archetypes model. So when we need to check
       that a user is not authorized to set the value of a field protected
       in this way, we do not try to use the accessor to trigger an exception
       (self.assertRaise). Instead, we check that the user has the permission
       to do so (getSecurityManager().checkPermission)."""

    def test_subproduct_call_WholeDecisionProcess(self):
        """
            This test covers the whole decision workflow. It begins with the
            creation of some items, and ends by closing a meeting.
            This call 2 sub tests for each process : college and council
        """
        self._testWholeDecisionProcessCollege()
        self.setMeetingConfig(self.meetingConfig2.getId())
        self._testWholeDecisionProcessCouncil()

    def _testWholeDecisionProcessCollege(self):
        '''This test covers the whole decision workflow. It begins with the
           creation of some items, and ends by closing a meeting.'''
        # pmCreator1 creates an item with 1 annex and proposes it
        self.changeUser('pmCreator1')
        item1 = self.create('MeetingItem', title='The first item')
        annex1 = self.addAnnex(item1)
        self.addAnnex(item1, decisionRelated=True)
        self.do(item1, 'proposeToServiceHead')
        self.assertRaises(Unauthorized, self.addAnnex, item1, decisionRelated=True)
        self.failIf(self.transitions(item1))  # He may trigger no more action
        self.failIf(self.hasPermission('PloneMeeting: Add annex', item1))
        # the ServiceHead validation level
        self.changeUser('pmServiceHead1')
        self.failUnless(self.hasPermission('Modify portal content', (item1, annex1)))
        self.do(item1, 'proposeToOfficeManager')
        self.assertRaises(Unauthorized, self.addAnnex, item1, decisionRelated=True)
        self.failIf(self.transitions(item1))  # He may trigger no more action
        self.failIf(self.hasPermission('PloneMeeting: Add annex', item1))
        # the OfficeManager validation level
        self.changeUser('pmOfficeManager1')
        self.failUnless(self.hasPermission('Modify portal content', (item1, annex1)))
        self.do(item1, 'proposeToDivisionHead')
        self.assertRaises(Unauthorized, self.addAnnex, item1, decisionRelated=True)
        self.failIf(self.transitions(item1))  # He may trigger no more action
        self.failIf(self.hasPermission('PloneMeeting: Add annex', item1))
        # the DivisionHead validation level
        self.changeUser('pmDivisionHead1')
        self.failUnless(self.hasPermission('Modify portal content', (item1, annex1)))
        self.do(item1, 'proposeToDirector')
        self.assertRaises(Unauthorized, self.addAnnex, item1, decisionRelated=True)
        self.failIf(self.transitions(item1))  # He may trigger no more action
        self.failIf(self.hasPermission('PloneMeeting: Add annex', item1))
        # the Director validation level
        self.changeUser('pmDirector1')
        self.failUnless(self.hasPermission('Modify portal content', (item1, annex1)))
        self.do(item1, 'validate')
        self.assertRaises(Unauthorized, self.addAnnex, item1, decisionRelated=True)
        self.failIf(self.transitions(item1))  # He may trigger no more action
        self.failIf(self.hasPermission('PloneMeeting: Add annex', item1))
        # pmManager creates a meeting
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date='2007/12/11 09:00:00')
        self.addAnnex(item1, decisionRelated=True)
        # pmCreator2 creates and proposes an item
        self.changeUser('pmCreator2')
        item2 = self.create('MeetingItem', title='The second item',
                            preferredMeeting=meeting.UID())
        self.do(item2, 'proposeToServiceHead')
        # pmReviewer1 can not validate the item has not in the same proposing group
        self.changeUser('pmReviewer1')
        self.failIf(self.hasPermission('Modify portal content', item2))
        # even pmManagercan not see/validate an item in the validation queue
        self.changeUser('pmManager')
        self.failIf(self.hasPermission('Modify portal content', item2))
        # do the complete validation
        self.changeUser('admin')
        self.do(item2, 'proposeToOfficeManager')
        self.do(item2, 'proposeToDivisionHead')
        self.do(item2, 'proposeToDirector')
        # pmManager inserts item1 into the meeting and publishes it
        self.changeUser('pmManager')
        managerAnnex = self.addAnnex(item1)
        self.portal.restrictedTraverse('@@delete_givenuid')(managerAnnex.UID())
        self.do(item1, 'present')
        # Now reviewers can't add annexes anymore
        self.changeUser('pmReviewer2')
        self.assertRaises(Unauthorized, self.addAnnex, item1)
        # freeze the meeting
        self.changeUser('pmManager')
        self.do(meeting, 'freeze')
        # validate item2 after meeting freeze
        self.changeUser('pmReviewer2')
        self.do(item2, 'validate')
        self.changeUser('pmManager')
        self.do(item2, 'present')
        self.addAnnex(item2)
        # So now we should have 1 normal item (no recurring items) and one late item in the meeting
        self.failUnless(len(meeting.getItems()) == 1)
        self.failUnless(len(meeting.getLateItems()) == 1)
        self.do(meeting, 'decide')
        self.do(item1, 'refuse')
        self.assertEquals(item1.queryState(), 'refused')
        self.assertEquals(item2.queryState(), 'itemfrozen')
        self.do(meeting, 'close')
        self.assertEquals(item1.queryState(), 'refused')
        # every items without a decision are automatically accepted
        self.assertEquals(item2.queryState(), 'accepted')

    def _testWholeDecisionProcessCouncil(self):
        """
            This test covers the whole decision workflow. It begins with the
            creation of some items, and ends by closing a meeting.
        """
        # add a recurring item that is inserted when the meeting is 'setInCouncil'
        self.changeUser('admin')
        self.create('RecurringMeetingItem', title='Rec item 1',
                    proposingGroup='developers',
                    category='deployment',
                    meetingTransitionInsertingMe='setInCouncil')
        # pmCreator1 creates an item with 1 annex and proposes it
        self.changeUser('pmCreator1')
        item1 = self.create('MeetingItem', title='The first item', autoAddCategory=False)
        self.addAnnex(item1)
        # The creator can add a decision annex on created item
        self.addAnnex(item1, decisionRelated=True)
        # the item is not proposable until it has a category
        self.failIf(self.transitions(item1))  # He may trigger no more action
        item1.setCategory('deployment')
        self.do(item1, 'proposeToDirector')
        self.failIf(self.hasPermission('Modify portal content', item1))
        # The creator cannot add a decision annex on proposed item
        self.assertRaises(Unauthorized, self.addAnnex, item1, decisionRelated=True)
        self.failIf(self.transitions(item1))  # He may trigger no more action
        self.changeUser('pmDirector1')
        self.addAnnex(item1, decisionRelated=True)
        self.do(item1, 'validate')
        self.failIf(self.hasPermission('Modify portal content', item1))
        # The reviewer cannot add a decision annex on validated item
        self.assertRaises(Unauthorized, self.addAnnex, item1, decisionRelated=True)
        # pmManager creates a meeting
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date='2007/12/11 09:00:00')
        # The meetingManager can add a decision annex
        self.addAnnex(item1, decisionRelated=True)
        # pmCreator2 creates and proposes an item
        self.changeUser('pmCreator2')
        item2 = self.create('MeetingItem', title='The second item',
                            preferredMeeting=meeting.UID())
        item2.setCategory('events')
        self.do(item2, 'proposeToDirector')
        # pmManager inserts item1 into the meeting and freezes it
        self.changeUser('pmManager')
        managerAnnex = self.addAnnex(item1)
        self.portal.restrictedTraverse('@@delete_givenuid')(managerAnnex.UID())
        self.do(item1, 'present')
        self.changeUser('pmCreator1')
        # The creator cannot add any kind of annex on presented item
        self.assertRaises(Unauthorized, self.addAnnex, item1, decisionRelated=True)
        self.assertRaises(Unauthorized, self.addAnnex, item1)
        self.changeUser('pmManager')
        self.do(meeting, 'setInCommittee')
        # pmReviewer2 validates item2
        self.changeUser('pmDirector2')
        self.do(item2, 'validate')
        # pmManager inserts item2 into the meeting, as late item, and adds an
        # annex to it
        self.changeUser('pmManager')
        self.do(item2, 'present')
        self.addAnnex(item2)
        # An item is freely addable to a meeting if the meeting is 'open'
        # so in states 'created', 'in_committee' and 'in_council'
        # the 'late items' functionnality is not used
        self.failIf(len(meeting.getItems()) != 2)
        self.failIf(len(meeting.getLateItems()) != 0)
        # remove the item, set the meeting in council and add it again
        self.do(item2, 'backToValidated')
        self.failIf(len(meeting.getItems()) != 1)
        self.do(meeting, 'setInCouncil')
        self.do(item2, 'present')
        # setting the meeting in council (setInCouncil) add 1 recurring item...
        self.failIf(len(meeting.getItems()) != 3)
        self.failIf(len(meeting.getLateItems()) != 0)
        # an item can be send back to the service so MeetingMembers
        # can edit it and send it back to the meeting
        self.changeUser('pmCreator1')
        self.failIf(self.hasPermission('Modify portal content', item1))
        self.changeUser('pmManager')
        # send the item back to the service
        self.do(item1, 'return_to_proposing_group')
        self.changeUser('pmCreator1')
        self.failUnless(self.hasPermission('Modify portal content', item1))
        self.do(item1, 'backTo_item_in_council_from_returned_to_proposing_group')
        self.failIf(self.hasPermission('Modify portal content', item1))
        # item state follow meeting state
        self.changeUser('pmManager')
        self.assertEquals(item1.queryState(), 'item_in_council')
        self.assertEquals(item2.queryState(), 'presented')
        self.do(meeting, 'backToInCommittee')
        self.assertEquals(item1.queryState(), 'item_in_committee')
        self.assertEquals(item1.queryState(), 'item_in_committee')
        self.do(meeting, 'setInCouncil')
        self.assertEquals(item1.queryState(), 'item_in_council')
        self.assertEquals(item2.queryState(), 'item_in_council')
        # while closing a meeting, every no decided items are accepted
        self.do(item1, 'accept_but_modify')
        self.do(meeting, 'close')
        self.assertEquals(item1.queryState(), 'accepted_but_modified')
        self.assertEquals(item2.queryState(), 'accepted')

    def test_subproduct_call_RecurringItems(self):
        """
            Tests the recurring items system.
        """
        # call MeetingCommunes test and add our own
        mctw.test_subproduct_call_RecurringItems(self)
        # we do the test for the council config
        self.meetingConfig = getattr(self.tool, 'meeting-config-council')
        self._testRecurringItemsCouncil()

    def _testRecurringItemsCouncil(self):
        '''Tests the recurring items system.
           Recurring items are added when the meeting is setInCouncil.'''
        # First, define a recurring item in the meeting config
        # that will be added when the meeting is set to 'in_council'
        self.changeUser('admin')
        self.create('RecurringMeetingItem', title='Rec item 1',
                    proposingGroup='developers',
                    category='deployment',
                    meetingTransitionInsertingMe='setInCouncil')
        setRoles(self.portal, 'pmManager', ['MeetingManager', 'Manager', ])
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date='2007/12/11 09:00:00')
        self.failUnless(len(meeting.getAllItems()) == 0)
        self.do(meeting, 'setInCommittee')
        self.failUnless(len(meeting.getAllItems()) == 0)
        self.do(meeting, 'setInCouncil')
        self.failUnless(len(meeting.getAllItems()) == 1)
        self.do(meeting, 'close')
        self.failUnless(len(meeting.getAllItems()) == 1)

    def test_subproduct_FreezeMeeting(self):
        """
           When we freeze a meeting, every presented items will be frozen
           too and their state will be set to 'itemfrozen'.  When the meeting
           come back to 'created', every items will be corrected and set in the
           'presented' state
        """
        # First, define recurring items in the meeting config
        self.changeUser('pmManager')
        #create a meeting
        meeting = self.create('Meeting', date='2007/12/11 09:00:00')
        #create 2 items and present them to the meeting
        item1 = self.create('MeetingItem', title='The first item')
        item2 = self.create('MeetingItem', title='The second item')
        for item in (item1, item2,):
            self.presentItem(item)
        wftool = self.portal.portal_workflow
        #every presented items are in the 'presented' state
        self.assertEquals('presented', wftool.getInfoFor(item1, 'review_state'))
        self.assertEquals('presented', wftool.getInfoFor(item2, 'review_state'))
        #every items must be in the 'itemfrozen' state if we freeze the meeting
        self.do(meeting, 'freeze')
        self.assertEquals('itemfrozen', wftool.getInfoFor(item1, 'review_state'))
        self.assertEquals('itemfrozen', wftool.getInfoFor(item2, 'review_state'))
        #when correcting the meeting back to created, the items must be corrected
        #back to "presented"
        self.do(meeting, 'backToCreated')
        #when a point is in 'itemfrozen' it's must rest in this state
        #because normally we backToCreated for add new point
        self.assertEquals('itemfrozen', wftool.getInfoFor(item1, 'review_state'))
        self.assertEquals('itemfrozen', wftool.getInfoFor(item2, 'review_state'))

    def test_subproduct_CloseMeeting(self):
        """
           When we close a meeting, every items are set to accepted if they are still
           not decided...
        """
        # First, define recurring items in the meeting config
        self.changeUser('pmManager')
        #create a meeting (with 7 items)
        meetingDate = DateTime().strftime('%y/%m/%d %H:%M:00')
        meeting = self.create('Meeting', date=meetingDate)
        item1 = self.create('MeetingItem')  # id=o2
        item1.setProposingGroup('vendors')
        item1.setAssociatedGroups(('developers',))
        item2 = self.create('MeetingItem')  # id=o3
        item2.setProposingGroup('developers')
        item3 = self.create('MeetingItem')  # id=o4
        item3.setProposingGroup('vendors')
        item4 = self.create('MeetingItem')  # id=o5
        item4.setProposingGroup('developers')
        item5 = self.create('MeetingItem')  # id=o7
        item5.setProposingGroup('vendors')
        item6 = self.create('MeetingItem', title='The sixth item')
        item6.setProposingGroup('vendors')
        item7 = self.create('MeetingItem')  # id=o8
        item7.setProposingGroup('vendors')
        for item in (item1, item2, item3, item4, item5, item6, item7):
            self.presentItem(item)
        #we freeze the meeting
        self.do(meeting, 'freeze')
        #a MeetingManager can put the item back to presented
        self.do(item7, 'backToPresented')
        #we decide the meeting
        #while deciding the meeting, every items that where presented are frozen
        self.do(meeting, 'decide')
        #change all items in all different state (except first who is in good state)
        self.do(item7, 'backToPresented')
        self.do(item2, 'delay')
        self.do(item3, 'pre_accept')
        self.do(item4, 'accept_but_modify')
        self.do(item5, 'refuse')
        self.do(item6, 'accept')
        #we close the meeting
        self.do(meeting, 'close')
        #every items must be in the 'decided' state if we close the meeting
        wftool = self.portal.portal_workflow
        #itemfrozen change into accepted
        self.assertEquals('accepted', wftool.getInfoFor(item1, 'review_state'))
        #delayed rest delayed (it's already a 'decide' state)
        self.assertEquals('delayed', wftool.getInfoFor(item2, 'review_state'))
        #pre_accepted change into accepted
        self.assertEquals('accepted', wftool.getInfoFor(item3, 'review_state'))
        #accepted_but_modified rest accepted_but_modified (it's already a 'decide' state)
        self.assertEquals('accepted_but_modified', wftool.getInfoFor(item4, 'review_state'))
        #refused rest refused (it's already a 'decide' state)
        self.assertEquals('refused', wftool.getInfoFor(item5, 'review_state'))
        #accepted rest accepted (it's already a 'decide' state)
        self.assertEquals('accepted', wftool.getInfoFor(item6, 'review_state'))
        #presented change into accepted
        self.assertEquals('accepted', wftool.getInfoFor(item7, 'review_state'))

    def test_subproduct_RecurringItemsCollege(self):
        '''Call MeetingCommunes test, but give the pmManager the 'Manager' role
           so he has got no problems to add recurring items (need to be able to trigger every transitions).'''
        setRoles(self.portal, 'pmManager', ['MeetingManager', 'Manager', ])
        mctw.test_subproduct_RecurringItemsCollege(self)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testWorkflows, prefix='test_subproduct_'))
    return suite
