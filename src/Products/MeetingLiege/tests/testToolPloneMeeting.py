# -*- coding: utf-8 -*-
#
# File: testToolPloneMeeting.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testToolPloneMeeting import testToolPloneMeeting as pmtt


class testToolPloneMeeting(MeetingLiegeTestCase, pmtt):
    '''Tests the ToolPloneMeeting class methods.'''

    def test_pm_get_orgs_for_user(self):
        """Do not break test with financial suffixes."""
        self.changeUser('siteadmin')
        # creating finance groups will restrict use of financial suffixes
        self._createFinanceGroups()
        super(testToolPloneMeeting, self).test_pm_get_orgs_for_user()


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testToolPloneMeeting, prefix='test_pm_'))
    return suite
