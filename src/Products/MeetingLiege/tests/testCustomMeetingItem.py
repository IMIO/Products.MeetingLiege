# -*- coding: utf-8 -*-
#
# File: testCustomMeetingItem.py
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

from DateTime import DateTime

from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.setuphandlers import _configureCollegeCustomAdvisers
from Products.MeetingLiege.setuphandlers import _createFinanceGroups
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase


class testCustomMeetingItem(MeetingLiegeTestCase):
    """
        Tests the MeetingItem adapted methods
    """

    def test_InitFieldsWhenItemSentToCouncil(self):
        '''When an item is sent from College to Council, fields 'title' and 'privacy'
           are initialized from what is defined on the College item.'''
        # create a college item
        self.changeUser('pmManager')
        item = self.create('MeetingItem')
        item.setDecisionForCouncil('<p>My decision for council</p>')
        # default privacy is 'public', set 'secret' so we see that it is actually applied
        item.setPrivacyForCouncil('secret')
        # make item sendable to council
        item.setOtherMeetingConfigsClonableTo('meeting-config-council')
        # send the item to the council
        meeting = self.create('Meeting', date=DateTime('2014/01/01'))
        self.presentItem(item)
        self.closeMeeting(meeting)
        # the item has been sent, get it and test that relevant fields are correctly initialized
        newItem = item.getBRefs('ItemPredecessor')[0]
        self.assertTrue(newItem.getPredecessor().UID() == item.UID())
        self.assertTrue(newItem.getDecision() == '<p>My decision for council</p>')
        self.assertTrue(newItem.getPrivacy() == 'secret')

    def test_FinanceAdviceAskedDependingOnArchivingRef(self):
        '''Finance advice is asked depending on archivingRef.'''
        # create finance groups
        self.changeUser('admin')
        _createFinanceGroups(self.portal)
        _configureCollegeCustomAdvisers(self.portal)
        self.changeUser('pmManager')
        dataNoFinanceAdvice = self.meetingConfig.adapted()._dataForArchivingRefRowId(row_id='001')
        dataDFCompta = self.meetingConfig.adapted()._dataForArchivingRefRowId(row_id='008')
        dataDFControle = self.meetingConfig.adapted()._dataForArchivingRefRowId(row_id='012')
        # we have the right data
        self.assertTrue(dataNoFinanceAdvice['row_id'] == '001')
        self.assertTrue(dataNoFinanceAdvice['finance_advice'] == 'no_finance_advice')
        self.assertTrue(dataDFCompta['row_id'] == '008')
        self.assertTrue(dataDFCompta['finance_advice'] == FINANCE_GROUP_IDS[1])
        self.assertTrue(dataDFControle['row_id'] == '012')
        self.assertTrue(dataDFControle['finance_advice'] == FINANCE_GROUP_IDS[0])
        # create an item with relevant archivingRef
        item = self.create('MeetingItem')
        # archiving ref not asking any finance advice
        item.setArchivingRef('001')
        item.at_post_edit_script()
        self.assertTrue(item.adviceIndex == {})
        # use an archiving ref that call 'df-comptabilita-c-et-audit-financier' advice
        item.setArchivingRef('008')
        item.at_post_edit_script()
        self.assertTrue(FINANCE_GROUP_IDS[1] in item.adviceIndex)
        self.assertTrue(len(item.adviceIndex) == 1)
        # use an archiving ref that call 'df-contrale' advice
        item.setArchivingRef('012')
        item.at_post_edit_script()
        self.assertTrue(FINANCE_GROUP_IDS[0] in item.adviceIndex)
        self.assertTrue(len(item.adviceIndex) == 1)
