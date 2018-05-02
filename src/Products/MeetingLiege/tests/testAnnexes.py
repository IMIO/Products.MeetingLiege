# -*- coding: utf-8 -*-
#
# File: testAnnexes.py
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

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testAnnexes import testAnnexes as pmta


class testAnnexes(MeetingLiegeTestCase, pmta):
    ''' '''
    def test_pm_ItemGetCategorizedElementsWithConfidentialityForBudgetImpactEditors(self):
        """Fails because BudgetImpactEditor is a powerobserver and we manage powerobserver
           access to confidential annexes specifically."""
        pass

    def test_pm_ItemGetCategorizedElementsWithConfidentialityForPowerObservers(self):
        """Fails because we manage powerobserver access to confidential annexes specifically."""
        pass

    def test_pm_SwitchingConfidentialityUsingActionView(self):
        """Fails because power_observers may only access annexes using specific annexType
           even if annex is not confidential."""
        pass

    def _setUpGroupInCharge(self, item):
        """Define groupsOfMatter on category used by p_item."""
        cfg = self.meetingConfig
        cfg.setUseGroupsAsCategories(False)
        cat = cfg.categories.development
        cat.setGroupsOfMatter(('vendors', ))
        item.setCategory('development')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testAnnexes, prefix='test_pm_'))
    return suite
