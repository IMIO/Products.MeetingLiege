# -*- coding: utf-8 -*-
#
# File: testCustomMeeting.py
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
from DateTime import DateTime

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase


class testCustomMeeting(MeetingLiegeTestCase):
    """
        Tests the Meeting adapted methods
    """

    def test_GetPrintableItemsByCategoryWithoutCategories(self):
        self.meetingConfig.setUseGroupsAsCategories(False)
        meetingConfigCouncil = self.meetingConfig2.getId()
        self.changeUser('pmManager')
        self.meetingConfig.setInsertingMethodsOnAddItem(
            self.meetingConfig2.getInsertingMethodsOnAddItem()
        )

        meetingConfigCouncil = self.meetingConfig2.getId()
        self.setMeetingConfig(meetingConfigCouncil)
        meetingDate = DateTime('2019/09/09 19:19:19')
        meeting = self._createMeetingWithItems(meetingDate=meetingDate)

        items = meeting.adapted().getPrintableItemsByCategory()
        itemsWC = meeting.adapted().getPrintableItemsByCategory(groupByCategory=False)

        self.assertEquals(items[0][1], itemsWC[0])
        self.assertEquals(items[0][2], itemsWC[1])
        self.assertEquals(items[1][1], itemsWC[2])
        self.assertEquals(items[1][2], itemsWC[3])
        self.assertEquals(items[2][1], itemsWC[4])
