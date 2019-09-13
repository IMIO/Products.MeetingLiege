# -*- coding: utf-8 -*-

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testMeetingItem import testMeetingItem as pmtmi


class testMeetingItem(MeetingLiegeTestCase, pmtmi):
    """
        Tests the MeetingItem class methods.
    """

    def test_pm_Completeness(self):
        '''Already tested in testWorkflows.'''
        pass

    def test_pm_Emergency(self):
        '''Already tested in testWorkflows.'''
        pass

    def test_pm_ItemIsSigned(self):
        '''Bypass as we changed states in which itemIsSigned may
           be changed, tested in testCustomMeetingItem.test_ItemSignableSooner.'''
        pass

    def test_pm_SendItemToOtherMCWithoutDefinedAnnexType(self):
        '''Bypass as we changed behavior, we do not keep decision annexes.'''
        pass

    def test_pm_GetCertifiedSignaturesFromGroupInCharge(self):
        '''Bypass as getGroupsInCharge is overrided and defined on the category.'''


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMeetingItem, prefix='test_pm_'))
    return suite
