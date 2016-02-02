# -*- coding: utf-8 -*-
#
# File: testWorkflows.py
#
# Copyright (c) 2015 by Imio.be
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
from Products.MeetingCommunes.tests.testWorkflows import testWorkflows as mctw


class testWorkflows(MeetingLiegeTestCase, mctw):
    """Tests the default workflows implemented in MeetingLiege."""

    def test_pm_WholeDecisionProcess(self):
        """This test is bypassed, we use several tests here under."""
        pass

    def test_pm_RemoveObjects(self):
        '''Run the test_pm_RemoveObjects from PloneMeeting.'''
        # we do the test for the college config
        self.meetingConfig = getattr(self.tool, 'meeting-config-college')
        super(mctw, self).test_pm_RemoveObjects()
        # items are validated by default for the council config
        # so are not removable by item creators/reviewers
        #self.meetingConfig = getattr(self.tool, 'meeting-config-council')
        #super(testWorkflows, self).test_pm_RemoveObjects()


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testWorkflows, prefix='test_pm_'))
    return suite
