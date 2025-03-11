# -*- coding: utf-8 -*-
#
# File: testColumns.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testColumns import testColumns as pmtc


class testColumns(MeetingLiegeTestCase, pmtc):
    ''' '''


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testColumns, prefix='test_pm_'))
    return suite
