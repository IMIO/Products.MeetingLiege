# -*- coding: utf-8 -*-
#
# File: testWorkflows.py
#
# Copyright (c) 2007-2014 by Imio.be
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

from zope.i18n import translate
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer

from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.permissions import View

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.MeetingCommunes.tests.testWorkflows import testWorkflows as mctw


class testWorkflows(MeetingLiegeTestCase, mctw):
    """Tests the default workflows implemented in MeetingLiege."""

    def test_subproduct_call_WholeDecisionProcess(self):
        """This test is bypassed, we use several tests here under."""
        pass

    def test_subproduct_call_CollegeProcessWithoutAdvices(self):
        '''This test covers the whole decision workflow. It begins with the
           creation of some items, and ends by closing a meeting.
           The usecase here is to test the workflow without normal and finances advice.'''
        # pmCreator1 creates an item and proposes it to the administrative reviewer
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem', title='The first item')
        # pmCreator may only 'proposeToAdministrativeReviewer'
        self.assertTrue(self.transitions(item) == ['proposeToAdministrativeReviewer', ])
        # a MeetingManager is able to validate an item immediatelly, bypassing the entire validation workflow
        self.changeUser('pmManager')
        self.assertTrue(self.transitions(item) == ['proposeToAdministrativeReviewer',
                                                   'validate', ])
        # the pmCreator1 send the item to the administrative reviewer
        self.changeUser('pmCreator1')
        self.do(item, 'proposeToAdministrativeReviewer')
        # pmCreator1 can no more edit item but can still view it
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, item))
        self.changeUser('pmAdminReviewer1')
        # pmAdminReviewer1 may access item and edit it
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(self.hasPermission(ModifyPortalContent, item))
        # he may send the item back to the pmCreator1 or send it to the internal reviewer
        self.assertTrue(self.transitions(item) == ['backToItemCreated',
                                                   'proposeToInternalReviewer', ])
        self.do(item, 'proposeToInternalReviewer')
        # pmAdminReviewer1 can no more edit item but can still view it
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, item))
        # pmInternalReviewer1 may access item and edit it
        self.changeUser('pmInternalReviewer1')
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(self.hasPermission(ModifyPortalContent, item))
        # he may send the item back to the administrative reviewer or send it to the reviewer (director)
        self.assertTrue(self.transitions(item) == ['backToProposedToAdministrativeReviewer',
                                                   'proposeToDirector', ])
        self.do(item, 'proposeToDirector')
        # pmInternalReviewer1 can no more edit item but can still view it
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, item))
        # pmReviewer1 (director) may access item and edit it
        self.changeUser('pmReviewer1')
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(self.hasPermission(ModifyPortalContent, item))
        # he may send the item back to the internal reviewer or validate it
        self.assertTrue(self.transitions(item) == ['backToProposedToInternalReviewer',
                                                   'validate', ])
        self.do(item, 'validate')
        # pmReviewer1 can no more edit item but can still view it
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, item))

        # create a meeting, a MeetingManager will manage it now
        self.changeUser('pmManager')
        # the item can be removed sent back to the reviewer (director) or sent back in 'itemcreated'
        self.assertTrue(self.transitions(item) == ['backToItemCreated',
                                                   'backToProposedToDirector', ])
        meeting = self.create('Meeting', date='2014/01/01 09:00:00')
        # the item is available for the meeting
        availableItemUids = [brain.UID for brain in meeting.getAvailableItems()]
        self.assertTrue(item.UID() in availableItemUids)
        self.do(item, 'present')
        self.assertTrue(item.queryState() == 'presented')
        # the item can be removed from the meeting or sent back in 'itemcreated'
        self.assertTrue(self.transitions(item) == ['backToValidated', ])
        # the meeting can now be frozen then decided
        self.do(meeting, 'freeze')
        # the item has been automatically frozen
        self.assertTrue(item.queryState(), 'itemfrozen')
        # but the item can be sent back to 'presented'
        self.assertTrue(self.transitions(item) == ['backToPresented', ])
        self.do(meeting, 'decide')
        # the item is still frozen but can be decided
        self.assertTrue(item.queryState(), 'itemfrozen')
        self.assertTrue(self.transitions(item) == ['accept',
                                                   'accept_but_modify',
                                                   'backToPresented',
                                                   'delay',
                                                   'mark_not_applicable',
                                                   'pre_accept',
                                                   'refuse'])
        # if we pre_accept an item, we can accept it after
        self.do(item, 'pre_accept')
        self.assertTrue(self.transitions(item) == ['accept',
                                                   'accept_but_modify',
                                                   'backToItemFrozen'])
        # if we decide an item, it may still be set backToItemFrozen until the meeting is closed
        self.do(item, 'accept')
        self.assertTrue(self.transitions(item) == ['backToItemFrozen', ])
        # the meeting may be closed or back to frozen
        self.assertTrue(self.transitions(meeting) == ['backToFrozen',
                                                      'close', ])
        self.do(meeting, 'close')
        self.assertTrue(not self.transitions(item))

    def test_subproduct_call_CollegeProcessWithNormalAdvices(self):
        '''How does the process behave when some 'normal' advices,
           aka not 'finances' advices are aksed.'''
        # normal advices can be given when item in state 'itemcreated_waiting_advices',
        # asked by item creator and when item in state 'proposed_to_internal_reviewer_waiting_advices',
        # asekd by internal reviewer
        self.meetingConfig.setItemAdviceStates(('itemcreated_waiting_advices',
                                                'proposed_to_internal_reviewer_waiting_advices'))
        self.meetingConfig.setItemAdviceEditStates = (('itemcreated_waiting_advices',
                                                       'proposed_to_internal_reviewer_waiting_advices'))
        self.meetingConfig.setItemAdviceViewStates = (('itemcreated_waiting_advices', 'proposed_to_administrative_reviewer',
                                                       'proposed_to_internal_reviewer', 'proposed_to_internal_reviewer_waiting_advices',
                                                       'proposed_to_director', 'validated', 'presented',
                                                       'itemfrozen', 'refused', 'delayed', 'removed',
                                                       'pre_accepted', 'accepted', 'accepted_but_modified', ))
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem', title='The first item')
        # if no advice to ask, pmCreator may only 'proposeToAdministrativeReviewer'
        self.assertTrue(self.transitions(item) == ['proposeToAdministrativeReviewer', ])
        # the mayAskAdvicesByItemCreator wfCondition returns a 'No' instance
        advice_required_to_ask_advices = translate('advice_required_to_ask_advices',
                                                   domain='PloneMeeting',
                                                   context=self.request)
        self.assertTrue(item.wfConditions().mayAskAdvicesByItemCreator().msg == advice_required_to_ask_advices)
        # now ask 'vendors' advice
        item.setOptionalAdvisers(('vendors', ))
        item.at_post_edit_script()
        self.assertTrue(self.transitions(item) == ['askAdvicesByItemCreator',
                                                   'proposeToAdministrativeReviewer', ])
        # give advice
        self.do(item, 'askAdvicesByItemCreator')
        # pmReviewer2 is adviser for vendors
        self.changeUser('pmReviewer2')
        createContentInContainer(item,
                                 'meetingadvice',
                                 **{'advice_group': 'vendors',
                                    'advice_type': u'positive',
                                    'advice_comment': RichTextValue(u'My comment vendors')})
        # no more advice to give
        self.assertTrue(not item.hasAdvices(toGive=True))
        # item may be proposed directly to administrative reviewer
        # from state 'itemcreated_waiting_advices'
        # we continue wf as internal reviewer may also ask advice
        self.changeUser('pmCreator1')
        self.do(item, 'proposeToAdministrativeReviewer')
        self.changeUser('pmAdminReviewer1')
        self.do(item, 'proposeToInternalReviewer')
        self.changeUser('pmInternalReviewer1')
        # no advice to give so not askable
        self.assertTrue(self.transitions(item) == ['backToProposedToAdministrativeReviewer',
                                                   'proposeToDirector', ])
        item.setOptionalAdvisers(('vendors', 'developers'))
        item.at_post_edit_script()
        # now that there is an advice to give (developers)
        # internal reviewer may ask it
        self.assertTrue(self.transitions(item) == ['askAdvicesByInternalReviewer',
                                                   'backToProposedToAdministrativeReviewer',
                                                   'proposeToDirector', ])
        # give advice
        self.do(item, 'askAdvicesByInternalReviewer')
        # pmAdviser1 is adviser for developers
        self.changeUser('pmAdviser1')
        createContentInContainer(item,
                                 'meetingadvice',
                                 **{'advice_group': 'developers',
                                    'advice_type': u'positive',
                                    'advice_comment': RichTextValue(u'My comment developers')})
        # item may be proposed directly to director
        # from state 'proposed_to_internal_reviewer_waiting_advices'
        self.changeUser('pmInternalReviewer1')
        self.do(item, 'proposeToDirector')

    def test_subproduct_call_RemoveObjects(self):
        """
            Tests objects removal (items, meetings, annexes...).
        """
        # we do the test for the college config
        self.meetingConfig = getattr(self.tool, 'meeting-config-college')
        self.test_pm_RemoveObjects()
        # items are validated by default for the council config
        # so are not removable by item creators/reviewers
        #self.meetingConfig = getattr(self.tool, 'meeting-config-council')
        #self.test_pm_RemoveObjects()


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testWorkflows, prefix='test_subproduct_'))
    return suite
