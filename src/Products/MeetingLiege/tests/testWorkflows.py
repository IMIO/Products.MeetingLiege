# -*- coding: utf-8 -*-
#
# File: testWorkflows.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testWorkflows import testWorkflows as pmtw


class testWorkflows(MeetingLiegeTestCase, pmtw):
    """Tests the default workflows implemented in MeetingLiege."""

    def test_pm_WholeDecisionProcess(self):
        """Bypass this test..."""
        pass

    def test_pm_WorkflowPermissions(self):
        """Bypass this test..."""
        pass

    def test_pm_RecurringItems(self):
        """Bypass this test..."""
        pass


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testWorkflows, prefix='test_pm_'))
    return suite
