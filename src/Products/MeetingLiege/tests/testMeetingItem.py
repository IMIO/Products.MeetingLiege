# -*- coding: utf-8 -*-
#
# File: testMeetingItem.py
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

from Products.PloneMeeting.config import POWEROBSERVERS_GROUP_SUFFIX
from Products.MeetingLalouviere.tests.MeetingLalouviereTestCase import MeetingLalouviereTestCase
from Products.MeetingCommunes.tests.testMeetingItem import testMeetingItem as mctmi


class testMeetingItem(MeetingLalouviereTestCase, mctmi):
    """
        Tests the MeetingItem class methods.
    """

    def test_subproduct_call_IsPrivacyViewable(self):
        '''
          Original test, see doc string in PloneMeeting.
          Here, as soon as a user can access an item, the item isPrivacyViewable.
          See adapters.isPrivacyViewable overrided method.
        '''
        self.setMeetingConfig(self.meetingConfig2.getId())
        # we will use the copyGroups to check who can fully access item and who can not
        self.meetingConfig.setItemCopyGroupsStates(('presented', ))
        # make powerobserver1 a PowerObserver
        self.portal.portal_groups.addPrincipalToGroup('powerobserver1', '%s_%s' %
                                                      (self.meetingConfig.getId(), POWEROBSERVERS_GROUP_SUFFIX))
        # create a 'public' and a 'secret' item
        self.changeUser('pmManager')
        # add copyGroups that check that 'external' viewers can access the item but not isPrivacyViewable
        publicItem = self.create('MeetingItem')
        publicItem.setCategory('development')
        publicItem.setCopyGroups('vendors_reviewers')
        publicItem.reindexObject()
        secretItem = self.create('MeetingItem')
        secretItem.setPrivacy('secret')
        secretItem.setCategory('development')
        secretItem.setCopyGroups('vendors_reviewers')
        secretItem.reindexObject()
        self.create('Meeting', date=DateTime('2013/06/01 08:00:00'))
        self.presentItem(publicItem)
        self.presentItem(secretItem)
        # log in as a user that is in copyGroups
        self.changeUser('pmReviewer2')
        member = self.portal.portal_membership.getAuthenticatedMember()
        # the user can see the item because he is in the copyGroups
        # not because he is in the same proposing group
        secretItemPloneGroupsOfProposingGroup = getattr(self.tool,
                                                        secretItem.getProposingGroup()).getPloneGroups(idsOnly=True)
        self.failIf(set(secretItemPloneGroupsOfProposingGroup).intersection
                    (set(self.portal.portal_groups.getGroupsForPrincipal(member))))
        # pmReviewer2 can access the item and isPrivacyViewable
        self.failUnless(self.hasPermission('View', secretItem))
        self.failUnless(self.hasPermission('View', publicItem))
        # XXX Begin change for MeetingLalouviere
        self.failUnless(secretItem.isPrivacyViewable())
        # XXX End change for MeetingLalouviere
        self.failUnless(publicItem.isPrivacyViewable())
        # a user in the same proposingGroup can fully access the secret item
        self.changeUser('pmCreator1')
        self.failUnless(secretItem.isPrivacyViewable())
        self.failUnless(publicItem.isPrivacyViewable())
        # MeetingManager
        self.changeUser('pmManager')
        self.failUnless(secretItem.isPrivacyViewable())
        self.failUnless(publicItem.isPrivacyViewable())
        # PowerObserver
        self.changeUser('powerobserver1')
        self.failUnless(secretItem.isPrivacyViewable())
        self.failUnless(publicItem.isPrivacyViewable())


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    # launch only tests prefixed by 'test_mc_' to avoid launching the tests coming from pmtmi
    suite.addTest(makeSuite(testMeetingItem, prefix='test_subproduct_'))
    return suite
