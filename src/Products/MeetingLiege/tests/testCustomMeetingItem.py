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
        item.setTitleForCouncil('My title for council')
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
        self.assertTrue(newItem.Title() == 'My title for council')
        self.assertTrue(newItem.getPrivacy() == 'secret')

    def test_FinanceAdviceAskedDependingOnArchivingRef(self):
        '''Finance advice is asked depending on archivingRef.'''
        # add archivingRefs in the configuration
        self.meetingConfig.setCustomAdvisers([
            {'row_id': 'unique_id_002',
             'group': 'df-contrale',
             'gives_auto_advice_on': "python: item.adapted().needFinanceAdviceOf('df-contrale')",
             'for_item_created_from': '2014/01/01',
             'delay': '10',
             'delay_left_alert': '4',
             'delay_label': u'Incidence financière',
             },
            {'row_id': 'unique_id_003',
             'group': 'df-contrale',
             'for_item_created_from': '2014/01/01',
             'delay': '5',
             'delay_left_alert': '4',
             'delay_label': u'Incidence financière (Urgence)',
             'is_linked_to_previous_row': '1',
             },
            {'row_id': 'unique_id_004',
             'group': 'df-contrale',
             'for_item_created_from': '2014/01/01',
             'delay': '20',
             'delay_left_alert': '4',
             'delay_label': u'Incidence financière (Prolongation)',
             'is_linked_to_previous_row': '1',
             },
            {'row_id': 'unique_id_005',
             'group': 'df-comptabilita-c-et-audit-financier',
             'gives_auto_advice_on': "python: item.adapted().needFinanceAdviceOf('df-comptabilita-c-et-audit-financier')",
             'for_item_created_from': '2014/01/01',
             'delay': '10',
             'delay_left_alert': '4',
             'delay_label': u'Incidence financière',
             },
            {'row_id': 'unique_id_006',
             'group': 'df-comptabilita-c-et-audit-financier',
             'for_item_created_from': '2014/01/01',
             'delay': '5',
             'delay_left_alert': '4',
             'delay_label': u'Incidence financière (Urgence)',
             'is_linked_to_previous_row': '1',
             },
            {'row_id': 'unique_id_007',
             'group': 'df-comptabilita-c-et-audit-financier',
             'for_item_created_from': '2014/01/01',
             'delay': '20',
             'delay_left_alert': '4',
             'delay_label': u'Incidence financière (Prolongation)',
             'is_linked_to_previous_row': '1',
             }, ])

        self.meetingConfig.setArchivingRefs(
            (
                {'code': '1.1',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '001',
                 'finance_advice': 'no_finance_advice',
                 'label': "Archiving ref 1"},
                {'code': '1.2',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '002',
                 'finance_advice': 'df-comptabilita-c-et-audit-financier',
                 'label': 'Archiving ref 2'},
                {'code': '1.3',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '003',
                 'finance_advice': 'df-contrale',
                 'label': 'Archiving ref 3'}, )
        )
        # create an item with relevant archivingRef
        self.changeUser('pmManager')
        item = self.create('MeetingItem')
        # archiving ref not asking any finance advice
        item.setArchivingRef('001')
        item.at_post_edit_script()
        self.assertTrue(item.adviceIndex == {})
        # use an archiving ref that call 'df-comptabilita-c-et-audit-financier' advice
        item.setArchivingRef('002')
        item.at_post_edit_script()
        self.assertTrue('df-comptabilita-c-et-audit-financier' in item.adviceIndex)
        self.assertTrue(len(item.adviceIndex) == 1)
        # use an archiving ref that call 'df-contrale' advice
        item.setArchivingRef('003')
        item.at_post_edit_script()
        self.assertTrue('df-contrale' in item.adviceIndex)
        self.assertTrue(len(item.adviceIndex) == 1)
