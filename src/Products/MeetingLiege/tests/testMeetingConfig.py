# -*- coding: utf-8 -*-
#
# File: testMeetingConfig.py
#
# GNU General Public License (GPL)
#

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
        super(testMeetingConfig, self).test_pm_UpdatePersonalLabels()

    def test_pm_Validate_itemWFValidationLevels_removed_used_state_in_config(self):
        """Bypass..."""
        pass

    def test_pm_Validate_itemWFValidationLevels_removed_depending_used_state_item(self):
        """Bypass..."""
        pass


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMeetingConfig, prefix='test_pm_'))
    return suite
