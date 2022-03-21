# -*- coding: utf-8 -*-
#
# File: testMeetingConfig.py
#
# Copyright (c) 2007-2013 by Imio.be
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

from imio.helpers.cache import cleanRamCacheFor
from plone import api
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testMeetingConfig import testMeetingConfig as pmtmc


class testMeetingConfig(MeetingLiegeTestCase, pmtmc):
    '''Call testMeetingConfig tests.'''

    def test_pm_UpdatePersonalLabels(self):
        """ """
        # remove extra users from their groups to not break test
        for extra_user_id in ['pmAdminReviewer1', 'pmInternalReviewer1', 'pmReviewerLevel1']:
            user = api.user.get(extra_user_id)
            # remove from every groups, bypass Plone groups (including virtual)
            for group_id in [user_group_id for user_group_id in user.getGroups() if '_' in user_group_id]:
                api.group.remove_user(groupname=group_id, username=extra_user_id)
        cleanRamCacheFor('Products.PloneMeeting.ToolPloneMeeting._users_groups_value')
        super(testMeetingConfig, self).test_pm_UpdatePersonalLabels()

    def test_pm_Validate_itemWFValidationLevels_removed_depending_used_state_item(self):
        """Bypass..."""


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMeetingConfig, prefix='test_pm_'))
    return suite
