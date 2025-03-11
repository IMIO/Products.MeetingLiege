# -*- coding: utf-8 -*-
#
# File: testSearches.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testSearches import testSearches as pmts


class testSearches(MeetingLiegeTestCase, pmts):
    """Test searches."""

    def runSearchItemsToValidateOfEveryReviewerLevelsAndLowerLevelsTest(self):
        '''
          Helper method for activating the test_pm_SearchItemsToValidateOfEveryReviewerLevelsAndLowerLevels
          test when called from a subplugin.
        '''
        return True


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testSearches, prefix='test_pm_'))
    return suite
