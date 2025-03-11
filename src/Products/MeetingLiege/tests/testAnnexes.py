# -*- coding: utf-8 -*-
#
# File: testAnnexes.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testAnnexes import testAnnexes as pmta


class testAnnexes(MeetingLiegeTestCase, pmta):
    ''' '''
    def test_pm_ItemGetCategorizedElementsWithConfidentialityForBudgetImpactEditors(self):
        """Fails because BudgetImpactEditor is a powerobserver and we manage powerobserver
           access to confidential annexes specifically."""
        pass

    def test_pm_ItemGetCategorizedElementsWithConfidentialityForPowerObservers(self):
        """Fails because we manage powerobserver access to confidential annexes specifically."""
        pass

    def test_pm_SwitchingConfidentialityUsingActionView(self):
        """Fails because power_observers may only access annexes using specific annexType
           even if annex is not confidential."""
        pass


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testAnnexes, prefix='test_pm_'))
    return suite
