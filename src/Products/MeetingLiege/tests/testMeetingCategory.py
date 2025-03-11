# -*- coding: utf-8 -*-
#
# File: testMeetingCategory.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testMeetingCategory import testMeetingCategory as pmtmc


class testMeetingCategory(MeetingLiegeTestCase, pmtmc):
    '''Tests the MeetingCategory class methods.'''


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMeetingCategory, prefix='test_pm_'))
    return suite
