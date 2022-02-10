# -*- coding: utf-8 -*-
#
# File: testWFAdaptations.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testWFAdaptations import testWFAdaptations as pmtwfa


class testWFAdaptations(MeetingLiegeTestCase, pmtwfa):

    def test_pm_WFA_availableWFAdaptations(self):
        '''Most of wfAdaptations make no sense, we just use 'return_to_proposing_group'.'''
        self.assertEquals(sorted(self.meetingConfig.listWorkflowAdaptations()),
                          ['return_to_proposing_group'])


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testWFAdaptations, prefix='test_pm_'))
    return suite
