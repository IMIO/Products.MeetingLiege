# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2018 by Imio.be
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

from Products.PloneTestCase.setup import _createHomeFolder
from Products.PloneMeeting.MeetingConfig import MeetingConfig
from Products.PloneMeeting.model import adaptations
from Products.PloneMeeting.tests.PloneMeetingTestCase import PloneMeetingTestCase
from Products.MeetingLiege.adapters import customWfAdaptations
from Products.MeetingLiege.adapters import RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE
from Products.MeetingLiege.profiles.zbourgmestre import import_data as bg_import_data
from Products.MeetingLiege.testing import ML_TESTING_PROFILE_FUNCTIONAL
from Products.MeetingLiege.tests.helpers import MeetingLiegeTestingHelpers

# monkey patch the MeetingConfig.wfAdaptations again because it is done in
# adapters.py but overrided by Products.MeetingCommunes here in the tests...
MeetingConfig.wfAdaptations = customWfAdaptations
adaptations.RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE = RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE


class MeetingLiegeTestCase(PloneMeetingTestCase, MeetingLiegeTestingHelpers):
    """Base class for defining MeetingLiege test cases."""

    # by default, PloneMeeting's test file testPerformances.py and
    # testConversionWithDocumentViewer.py' are ignored, override the subproductIgnoredTestFiles
    # attribute to take these files into account
    # subproductIgnoredTestFiles = ['testPerformances.py', ]

    layer = ML_TESTING_PROFILE_FUNCTIONAL

    def setUp(self):
        PloneMeetingTestCase.setUp(self)
        self.meetingConfig = getattr(self.tool, 'meeting-config-college')
        self.meetingConfig2 = getattr(self.tool, 'meeting-config-council')
        self.meetingConfig3 = getattr(self.tool, 'meeting-config-bourgmestre')

    def setUpBourgmestreConfig(self):
        """Setup meeting-config-bourgmestre :
           - Create groups and users;
           - ...
        """
        self.changeUser('siteadmin')
        self.setMeetingConfig(self.meetingConfig3.getId())
        self.tool.addUsersAndGroups(groups=bg_import_data.groups)
        for userId in ('generalManager',
                       'bourgmestreManager',
                       'bourgmestreReviewer'):
            _createHomeFolder(self.portal, userId)
