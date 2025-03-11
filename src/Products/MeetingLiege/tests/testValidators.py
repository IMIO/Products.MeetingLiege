# -*- coding: utf-8 -*-
#
# File: testValidators.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testValidators import testValidators as pmtv


class testValidators(MeetingLiegeTestCase, pmtv):
    """Tests the validators."""


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testValidators, prefix='test_pm_'))
    return suite
