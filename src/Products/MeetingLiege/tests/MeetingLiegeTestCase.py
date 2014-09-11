# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2010 by PloneGov
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

from Products.CMFCore.utils import getToolByName
from Products.MeetingCommunes.tests.MeetingCommunesTestCase import MeetingCommunesTestCase
from Products.MeetingLiege.testing import ML_TESTING_PROFILE_FUNCTIONAL
from Products.MeetingLiege.tests.helpers import MeetingLiegeTestingHelpers

# monkey patch the MeetingConfig.wfAdaptations again because it is done in
# adapters.py but overrided by Products.MeetingCommunes here in the tests...
from Products.PloneMeeting.MeetingConfig import MeetingConfig
from Products.MeetingLiege.adapters import customWfAdaptations
from Products.MeetingLiege.config import FINANCE_GROUP_IDS

MeetingConfig.wfAdaptations = customWfAdaptations


class MeetingLiegeTestCase(MeetingCommunesTestCase, MeetingLiegeTestingHelpers):
    """Base class for defining MeetingLiege test cases."""

    layer = ML_TESTING_PROFILE_FUNCTIONAL

    def _setupFinanceGroups(self):
        '''Configure finance groups.'''
        groupsTool = getToolByName(self.portal, 'portal_groups')
        # add pmFinController, pmFinReviewer and pmFinManager to advisers and to their respective finance group
        groupsTool.addPrincipalToGroup('pmFinController', '%s_advisers' % FINANCE_GROUP_IDS[0])
        groupsTool.addPrincipalToGroup('pmFinReviewer', '%s_advisers' % FINANCE_GROUP_IDS[0])
        groupsTool.addPrincipalToGroup('pmFinManager', '%s_advisers' % FINANCE_GROUP_IDS[0])
        groupsTool.addPrincipalToGroup('pmFinController', '%s_financialcontrollers' % FINANCE_GROUP_IDS[0])
        groupsTool.addPrincipalToGroup('pmFinReviewer', '%s_financialreviewers' % FINANCE_GROUP_IDS[0])
        groupsTool.addPrincipalToGroup('pmFinManager', '%s_financialmanagers' % FINANCE_GROUP_IDS[0])
