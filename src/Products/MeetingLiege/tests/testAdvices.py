# -*- coding: utf-8 -*-
#
# File: testAdvices.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testAdvices import testAdvices as pmta


class testAdvices(MeetingLiegeTestCase, pmta):
    '''Call testAdvices from PloneMeeting.'''

    def test_pm_ShowAdvices(self):
        """Always True."""
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        self.assertEqual(self.tool.getMeetingConfig(item), self.meetingConfig)
        self.assertTrue(item.adapted().showAdvices())
        self.setMeetingConfig(self.meetingConfig2.getId())
        item2 = self.create('MeetingItem')
        self.assertEqual(self.tool.getMeetingConfig(item2), self.meetingConfig2)
        self.assertTrue(item2.adapted().showAdvices())


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testAdvices, prefix='test_pm_'))
    return suite
