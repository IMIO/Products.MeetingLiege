# -*- coding: utf-8 -*-
#
# File: testAdvices.py
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
from Products.MeetingLalouviere.tests.MeetingLalouviereTestCase import MeetingLalouviereTestCase
from Products.MeetingCommunes.tests.testAdvices import testAdvices as mcta


class testAdvices(MeetingLalouviereTestCase, mcta):
    '''Tests various aspects of advices management.
       Advices are enabled for PloneGov Assembly, not for PloneMeeting Assembly.'''

    def setUp(self):
        """Redefine advices related states."""
        super(mcta, self).setUp()
        self.setMeetingConfig(self.meetingConfig2.getId())
        self.meetingConfig.setItemAdviceStates(('proposed_to_director', 'validated', ))
        self.meetingConfig.setItemAdviceEditStates(('proposed_to_director', ))
        self.meetingConfig.setItemAdviceViewStates(('presented', ))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testAdvices, prefix='test_subproduct_'))
    return suite
