# -*- coding: utf-8 -*-
#
# GNU General Public License (GPL)
#

from plone.app.testing.bbb import _createMemberarea
from Products.MeetingLiege.config import PROJECTNAME
from Products.MeetingLiege.profiles.zbourgmestre import import_data as bg_import_data
from Products.MeetingLiege.testing import ML_TESTING_PROFILE_FUNCTIONAL
from Products.MeetingLiege.tests.helpers import MeetingLiegeTestingHelpers
from Products.PloneMeeting.exportimport.content import ToolInitializer
from Products.PloneMeeting.tests.PloneMeetingTestCase import PloneMeetingTestCase


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
        cfg.setKeepAccessToItemWhenAdvice('is_given')
