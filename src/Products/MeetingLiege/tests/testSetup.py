# -*- coding: utf-8 -*-
#
# File: testSetup.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testSetup import testSetup as pmts


class testSetup(MeetingLiegeTestCase, pmts):
    '''Tests the setup, especially registered profiles.'''


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testSetup, prefix='test_pm_'))
    return suite
