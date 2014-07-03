# -*- coding: utf-8 -*-
#
# File: testCustomMeetingCategory.py
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

from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase


class testCustomMeetingGroup(MeetingLiegeTestCase):
    '''Tests the MeetingGroup adapted methods.'''

    def test_customGetPloneGroups(self):
        '''
          getPloneGroups have been customized to return extra Plone
          groups when the MeetingGroup is a financial group.
        '''
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
