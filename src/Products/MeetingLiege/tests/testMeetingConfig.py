# -*- coding: utf-8 -*-
#
# File: testMeetingConfig.py
#
# Copyright (c) 2007-2013 by Imio.be
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
from Products.MeetingLalouviere.tests.MeetingLalouviereTestCase import MeetingLalouviereTestCase
from Products.MeetingCommunes.tests.testMeetingConfig import testMeetingConfig as mctmc


class testMeetingConfig(MeetingLalouviereTestCase, mctmc):
    '''Call testMeetingConfig tests.'''

    def test_subproduct_call_searchItemsToPrevalidate(self):
        '''No sense...'''
        pass

    def test_subproduct_call_searchItemsToValidate(self):
        '''Used in the meeting-config-council.'''
        self.setMeetingConfig(self.meetingConfig2.getId())
        # create an item
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        self.proposeItem(item)
        self.failIf(self.meetingConfig.searchItemsToValidate('', '', '', ''))
        self.changeUser('pmReviewer1')
        self.failUnless(self.meetingConfig.searchItemsToValidate('', '', '', ''))
        # now give a view on the item by 'pmReviewer2' and check if, as a reviewer,
        # the search does returns him the item, it should not as he is just a reviewer
        # but not able to really validate the new item
        self.meetingConfig.setUseCopies(True)
        self.meetingConfig.setItemCopyGroupsStates(('proposed_to_director', ))
        item.setCopyGroups(('vendors_directors',))
        item.at_post_edit_script()
        self.changeUser('pmReviewer2')
        # the user can see the item
        self.failUnless(self.hasPermission('View', item))
        # but the search will not return it
        self.failIf(self.meetingConfig.searchItemsToValidate('', '', '', ''))
        # if the item is validated, it will not appear for pmReviewer1 anymore
        self.changeUser('pmReviewer1')
        self.failUnless(self.meetingConfig.searchItemsToValidate('', '', '', ''))
        self.validateItem(item)
        self.failIf(self.meetingConfig.searchItemsToValidate('', '', '', ''))

    def test_subproduct_call_searchReviewableItems(self):
        '''Test the searchReviewableItems search.'''
        pass


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMeetingConfig, prefix='test_subproduct_'))
    return suite
