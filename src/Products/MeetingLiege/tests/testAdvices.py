# -*- coding: utf-8 -*-
#
# File: testAdvices.py
#
# Copyright (c) 2007-2015 by Imio.be
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

from Products.PloneMeeting.tests.testAdvices import testAdvices as pmta
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase


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
