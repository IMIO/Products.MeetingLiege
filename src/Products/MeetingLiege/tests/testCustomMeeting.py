# -*- coding: utf-8 -*-
#
# File: testCustomMeeting.py
#
# GNU General Public License (GPL)
#

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
        meeting = self._createMeetingWithItems()

        items = meeting.adapted().getPrintableItemsByCategory()
        itemsWC = meeting.adapted().getPrintableItemsByCategory(groupByCategory=False)

        self.assertEquals(items[0][1], itemsWC[0])
        self.assertEquals(items[0][2], itemsWC[1])
        self.assertEquals(items[1][1], itemsWC[2])
        self.assertEquals(items[1][2], itemsWC[3])
        self.assertEquals(items[2][1], itemsWC[4])
