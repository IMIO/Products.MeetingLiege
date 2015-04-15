# -*- coding: utf-8 -*-
#
# File: testCustomMeeting.py
#
# Copyright (c) 2007-2012 by CommunesPlone.org
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

from plone.app.testing import login


class testCustomMeeting(MeetingLiegeTestCase):
    """
        Tests the Meeting adapted methods
    """
    def test_GetPrintableItemsByCategoryWithCollege(self):
        meetingConfigCollege = self.meetingConfig.getId()
        self.meetingConfig.setUseGroupsAsCategories(False)
        meetingConfigCouncil = self.meetingConfig2.getId()
        self.changeUser('pmManager')
        self.meetingConfig.setInsertingMethodsOnAddItem(
            self.meetingConfig2.getInsertingMethodsOnAddItem()
        )

        #makes the college meeting
        self.setMeetingConfig(meetingConfigCollege)
        meetingDate = DateTime('2019/09/09 19:19:19')
        collegeMeeting = self._createMeetingWithItems(meetingDate=meetingDate)
        collegeMeeting.setAdoptsNextCouncilAgenda(True)
        #makes some items from development ready to go to council
        for item in collegeMeeting.getItemsInOrder():
            #item.setOtherMeetingConfigsClonableTo('meeting-config-council')
            item.getCategory(theObject=True).setCategoryMappingsWhenCloningToOtherMC(
                'meeting-config-council.%s' % item.getCategory()
            )
        item0 = collegeMeeting.getItemsInOrder()[0]
        item0.setOtherMeetingConfigsClonableTo('meeting-config-council')
        item3 = collegeMeeting.getItemsInOrder()[3]
        item3.setOtherMeetingConfigsClonableTo('meeting-config-council')
        #makes one item from events ready to go to council
        item1 = collegeMeeting.getItemsInOrder()[1]
        item1.setOtherMeetingConfigsClonableTo('meeting-config-council')
        #makes one item from research ready to go to council
        item4 = collegeMeeting.getItemsInOrder()[4]
        item4.setOtherMeetingConfigsClonableTo('meeting-config-council')

        #makes the council one
        self.setMeetingConfig(meetingConfigCouncil)
        meetingDate = DateTime('2019/09/19 19:19:19')
        councilMeeting = self._createMeetingWithItems(meetingDate=meetingDate)
        #pull out the only council item from the research category
        self.backToState(councilMeeting.getItemsInOrder()[4],
                         self.WF_STATE_NAME_MAPPINGS['validated']
                         )
        #build the list of uids
        councilItemUids = []
        for item in councilMeeting.getItemsInOrder():
            councilItemUids.append(item.UID())

        items = councilMeeting.adapted().getPrintableItemsByCategory(
            itemUids=councilItemUids,
            withCollege=True
        )

        #Are all the categories there?
        self.assertTrue([item[0].getId() for item in items] ==
                        ['development', 'events', 'research'])
        #Is there any item missing?
        self.assertTrue([len(item) for item in items] == [5, 4, 2])
        #Checks from where come the items
        #For the development category
        self.assertTrue(items[0][1].getPortalTypeName() ==
                        'MeetingItemCollege')
        self.assertTrue(items[0][2].getPortalTypeName() ==
                        'MeetingItemCollege')
        self.assertTrue(items[0][3].getPortalTypeName() ==
                        'MeetingItemCouncil')
        self.assertTrue(items[0][4].getPortalTypeName() ==
                        'MeetingItemCouncil')
        #For the events category
        self.assertTrue(items[1][1].getPortalTypeName() ==
                        'MeetingItemCollege')
        self.assertTrue(items[1][2].getPortalTypeName() ==
                        'MeetingItemCouncil')
        self.assertTrue(items[1][3].getPortalTypeName() ==
                        'MeetingItemCouncil')
        #For the research category
        self.assertTrue(items[2][1].getPortalTypeName() ==
                        'MeetingItemCollege')

