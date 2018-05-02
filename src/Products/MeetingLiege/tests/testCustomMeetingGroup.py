# -*- coding: utf-8 -*-
#
# File: testCustomMeetingCategory.py
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

from OFS.ObjectManager import BeforeDeleteException
from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.setuphandlers import _createFinanceGroups
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase


class testCustomMeetingGroup(MeetingLiegeTestCase):
    '''Tests the MeetingGroup adapted methods.'''

    def test_GroupNotRemovableIfUsed(self):
        """A MeetingGroup may not be removed if used in :
           - MeetingConfig.archivingRefs;
           - MeetingCategory.groupsOfMatter."""
        self.changeUser('siteadmin')
        cfg = self.meetingConfig
        # create a new group so it is used nowhere
        newGroup = self.create('MeetingGroup')
        newGroupId = newGroup.getId()
        cfg.setUseGroupsAsCategories(False)
        cfg.setArchivingRefs((
            {'active': '1',
             'restrict_to_groups': [newGroupId, ],
             'row_id': '1',
             'code': '1',
             'label': "1"},
            {'active': '1',
             'restrict_to_groups': [],
             'row_id': '2',
             'code': '2',
             'label': '2'},))
        with self.assertRaises(BeforeDeleteException) as cm:
            self.tool.manage_delObjects([newGroupId, ])
        self.assertEquals(cm.exception.message, 'can_not_delete_meetinggroup_archivingrefs')
        cfg.setArchivingRefs((
            {'active': '1',
             'restrict_to_groups': [],
             'row_id': '1',
             'code': '1',
             'label': "1"},
            {'active': '1',
             'restrict_to_groups': [],
             'row_id': '2',
             'code': '2',
             'label': '2'},))

        # now it is removable
        self.tool.manage_delObjects([newGroupId, ])
        self.failIf(hasattr(self.tool, newGroupId))

    def test_CustomGetPloneGroups(self):
        '''
          getPloneGroups have been customized to return extra Plone
          groups when the MeetingGroup is a financial group.
        '''
        self.changeUser('admin')
        _createFinanceGroups(self.portal)
        vendorsGroup = self.tool.vendors
        vendorsPloneGroups = [group.getId() for group in vendorsGroup.getPloneGroups()]
        vendorsPloneGroups.sort()
        self.assertTrue(vendorsPloneGroups == ['vendors_administrativereviewers',
                                               'vendors_advisers',
                                               'vendors_creators',
                                               'vendors_internalreviewers',
                                               'vendors_observers',
                                               'vendors_prereviewers',
                                               'vendors_reviewers'])
        financeGroup = getattr(self.tool, FINANCE_GROUP_IDS[0])
        financePloneGroups = [group.getId() for group in financeGroup.getPloneGroups()]
        financePloneGroups.sort()
        self.assertTrue(financePloneGroups == ['%s_administrativereviewers' % FINANCE_GROUP_IDS[0],
                                               '%s_advisers' % FINANCE_GROUP_IDS[0],
                                               '%s_creators' % FINANCE_GROUP_IDS[0],
                                               '%s_financialcontrollers' % FINANCE_GROUP_IDS[0],
                                               '%s_financialmanagers' % FINANCE_GROUP_IDS[0],
                                               '%s_financialreviewers' % FINANCE_GROUP_IDS[0],
                                               '%s_internalreviewers' % FINANCE_GROUP_IDS[0],
                                               '%s_observers' % FINANCE_GROUP_IDS[0],
                                               '%s_prereviewers' % FINANCE_GROUP_IDS[0],
                                               '%s_reviewers' % FINANCE_GROUP_IDS[0]])
