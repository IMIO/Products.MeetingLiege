# -*- coding: utf-8 -*-
#
# File: testFaceted.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testFaceted import testFaceted as pmtf


class testFaceted(MeetingLiegeTestCase, pmtf):
    '''Tests the faceted navigation.'''


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testFaceted, prefix='test_pm_'))
    return suite
