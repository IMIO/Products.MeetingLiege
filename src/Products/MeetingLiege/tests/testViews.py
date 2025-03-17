# -*- coding: utf-8 -*-
#
# File: testViews.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testViews import testViews as pmtv


class testViews(MeetingLiegeTestCase, pmtv):
    ''' '''

    def test_pm_deliberation_for_restapi(self):
        """Override and print_deliberation was overrided."""
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem', motivation=self.motivationText, decision=self.decisionText)
        view = item.restrictedTraverse('@@document-generation')
        helper = view.get_generation_context_helper()
        data = helper.deliberation_for_restapi()
        self.assertEqual(
            data["deliberation"],
            self.motivationText +
            "<p>Sur proposition du Coll&#232;ge communal, et apr&#232;s examen "
            "du dossier par la Commission comp&#233;tente ;</p>" +
            self.decisionText)
        self.assertEqual(
            data["deliberation_motivation"],
            self.motivationText +
            "<p>Sur proposition du Coll&#232;ge communal, et apr&#232;s examen "
            "du dossier par la Commission comp&#233;tente ;</p>" +
            self.decisionText)
        self.assertEqual(
            data["deliberation_decision"],
            self.motivationText +
            "<p>Sur proposition du Coll&#232;ge communal, et apr&#232;s examen "
            "du dossier par la Commission comp&#233;tente ;</p>" +
            self.decisionText)
        self.assertEqual(
            data["public_deliberation"],
            self.motivationText +
            "<p>Sur proposition du Coll&#232;ge communal, et apr&#232;s examen "
            "du dossier par la Commission comp&#233;tente ;</p>" +
            self.decisionText)
        self.assertEqual(
            data["public_deliberation_decided"],
            self.motivationText +
            "<p>Sur proposition du Coll&#232;ge communal, et apr&#232;s examen "
            "du dossier par la Commission comp&#233;tente ;</p>" +
            self.decisionText)
        return item, view, helper, data


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testViews, prefix='test_pm_'))
    return suite
