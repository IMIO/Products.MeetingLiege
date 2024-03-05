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
        self._enableField('category')
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

        self.assertEqual(items[0][1], itemsWC[0])
        self.assertEqual(items[0][2], itemsWC[1])
        self.assertEqual(items[1][1], itemsWC[2])
        self.assertEqual(items[1][2], itemsWC[3])
        self.assertEqual(items[2][1], itemsWC[4])
