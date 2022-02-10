# -*- coding: utf-8 -*-
#
# File: testMeeting.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testMeeting import testMeetingType as pmtm


class testMeetingType(MeetingLiegeTestCase, pmtm):
    """Tests the Meeting class methods."""

    def test_pm_InsertItemOnGroupsInCharge(self):
        """Bypass test that insert items in meeting on group in charge as we
           use another implementation, moreover we do not use this inserting method."""
        pass

    def test_pm_InsertItemOnSeveralGroupsInCharge(self):
        """Bypass as MeetingItem.getGroupsIsCharge is overrided."""
        pass

    def test_pm_GetItemInsertOrderByOrderedGroupsInCharge(self):
        """Bypass as MeetingItem.getGroupsIsCharge is overrided."""
        pass

    def test_pm_InsertItemOnSeveralMethods(self):
        """Bypass as MeetingItem.getGroupsIsCharge is overrided."""
        pass


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMeetingType, prefix='test_pm_'))
    return suite
