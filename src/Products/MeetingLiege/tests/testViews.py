# -*- coding: utf-8 -*-
#
# File: testViews.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testViews import testViews as pmtv


class testViews(MeetingLiegeTestCase, pmtv):
    ''' '''


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testViews, prefix='test_pm_'))
    return suite
