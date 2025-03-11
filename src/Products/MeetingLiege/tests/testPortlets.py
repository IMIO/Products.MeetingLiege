# -*- coding: utf-8 -*-
#
# File: testPortlets.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testPortlets import testPortlets as pmtp


class testPortlets(MeetingLiegeTestCase, pmtp):
    '''Tests the portlets methods.'''


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testPortlets, prefix='test_pm_'))
    return suite
