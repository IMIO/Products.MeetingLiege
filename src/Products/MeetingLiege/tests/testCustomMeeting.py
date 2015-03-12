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

from plone.app.testing import login
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase


class testCustomMeeting(MeetingLiegeTestCase):
    """
        Tests the Meeting adapted methods
    """
    def test_GetPrintableItemsByCategoryWithCollege(self):
        import ipdb; ipdb.set_trace()  # XXX BREAKPOINT
        login(self.portal, 'admin')
        self.setMeetingConfig(self.meetingConfig2.getId())
        meeting = self._createMeetingWithItems()
        #build the list of uids
        itemUids = []
        for item in meeting.getItemsInOrder():
            itemUids.append(item.UID())

