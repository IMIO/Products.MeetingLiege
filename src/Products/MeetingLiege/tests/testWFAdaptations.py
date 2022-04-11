# -*- coding: utf-8 -*-
#
# File: testWFAdaptations.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testWFAdaptations import testWFAdaptations as pmtwfa


class testWFAdaptations(MeetingLiegeTestCase, pmtwfa):

    def test_pm_WFA_availableWFAdaptations(self):
        '''Most of wfAdaptations make no sense, we just use 'return_to_proposing_group'.'''
        self.assertEquals(sorted(self.meetingConfig.listWorkflowAdaptations()),
                          ['accepted_and_returned',
                           'accepted_but_modified',
                           'delayed',
                           'item_validation_shortcuts',
                           'mark_not_applicable',
                           'no_decide',
                           'no_freeze',
                           'no_publication',
                           'only_creator_may_delete',
                           'pre_accepted',
                           'refused',
                           'return_to_proposing_group',
                           'returned',
                           'sent_to_council_emergency',
                           'waiting_advices',
                           'waiting_advices_adviser_send_back',
                           'waiting_advices_proposing_group_send_back'])

    def test_pm_WFA_waiting_advices_may_edit(self):
        """Bypass, not relevant..."""
        pass

    def test_pm_WFA_waiting_advices_unknown_state(self):
        """Bypass, not relevant..."""
        pass

    def test_pm_WFA_waiting_advices(self):
        """Bypass, tested in testCustomWorkflows.py..."""
        pass

    def test_pm_WFA_waiting_advices_with_prevalidation(self):
        """Bypass, tested in testCustomWorkflows.py..."""
        pass

    def test_pm_WFA_item_validation_shortcuts(self):
        """Bypass as mayValidated is overrided..."""
        pass

    def _beforeValidateItemFields(self, item):
        """Set an "archivingRef"."""
        item.setArchivingRef(item.listArchivingRefs()[-1])


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testWFAdaptations, prefix='test_pm_'))
    return suite
