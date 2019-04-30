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

from plone.app.testing.bbb import _createMemberarea
from Products.MeetingLiege.adapters import customWfAdaptations
from Products.MeetingLiege.adapters import RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE
from Products.MeetingLiege.config import PROJECTNAME
from Products.MeetingLiege.profiles.zbourgmestre import import_data as bg_import_data
from Products.MeetingLiege.testing import ML_TESTING_PROFILE_FUNCTIONAL
from Products.MeetingLiege.tests.helpers import MeetingLiegeTestingHelpers
from Products.PloneMeeting.exportimport.content import ToolInitializer
from Products.PloneMeeting.MeetingConfig import MeetingConfig
from Products.PloneMeeting.model import adaptations
from Products.PloneMeeting.tests.PloneMeetingTestCase import PloneMeetingTestCase

# monkey patch the MeetingConfig.wfAdaptations again because it is done in
# adapters.py but overrided by Products.MeetingCommunes here in the tests...
MeetingConfig.wfAdaptations = customWfAdaptations
adaptations.RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE = RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE


class MeetingLiegeTestCase(PloneMeetingTestCase, MeetingLiegeTestingHelpers):
    """Base class for defining MeetingLiege test cases."""

    # by default, PloneMeeting's test file testPerformances.py and
    # testConversionWithDocumentViewer.py' are ignored, override the subproductIgnoredTestFiles
    # attribute to take these files into account
    subproductIgnoredTestFiles = ['test_robot.py', 'testPerformances.py', 'testContacts.py', 'testVotes.py']

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
        self._createFinanceGroups()
        self.setMeetingConfig(self.meetingConfig3.getId())
        context = self.portal.portal_setup._getImportContext('Products.MeetingLiege:testing')
        initializer = ToolInitializer(context, PROJECTNAME)
        orgs, active_orgs, savedOrgsData = initializer.addOrgs(bg_import_data.orgs)
        for org in orgs:
            self._select_organization(org.UID())
        initializer.addUsers(bg_import_data.orgs)
        initializer.addUsersOutsideGroups(bg_import_data.data.usersOutsideGroups)
        for userId in ('pmMeetingManagerBG',
                       'generalManager',
                       'bourgmestreManager',
                       'bourgmestreReviewer'):
            _createMemberarea(self.portal, userId)
        cfg = self.meetingConfig
        cfg.setUsedAdviceTypes(cfg.getUsedAdviceTypes() + ('asked_again', ))
        cfg.setItemAdviceStates(('proposed_to_director_waiting_advices', ))
        cfg.setItemAdviceEditStates = (('proposed_to_director_waiting_advices', ))
        cfg.setKeepAccessToItemWhenAdviceIsGiven(True)
