# -*- coding: utf-8 -*-
#
# File: testContacts.py
#
# GNU General Public License (GPL)
#

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.tests.testContacts import testContacts as pmtc


class testContacts(pmtc, MeetingLiegeTestCase):
    '''Tests the contacts related methods.'''

    def setUp(self):
        ''' '''
        super(testContacts, self).setUp()


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testContacts, prefix='test_pm_'))
    return suite
