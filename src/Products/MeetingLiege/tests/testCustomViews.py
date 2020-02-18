# -*- coding: utf-8 -*-
#
# File: testCustomViews.py
#
# Copyright (c) 2007-2017 by Imio.be
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

from AccessControl import Unauthorized
from collective.iconifiedcategory.utils import get_categorized_elements
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase


class testCustomViews(MeetingLiegeTestCase):
    """Tests the Meeting adapted methods."""

    def test_DecisionAnnexToSignOnlyViewableByMeetingManagers(self):
        '''When the 'deliberation' is added as decision annex 'to sign', nobody else
           but (Meeting)Managers may see the annex.'''
        cfg = self.meetingConfig
        # hide annex confidentiality, make signed only editable by MeetingManagers
        cfg.setAnnexRestrictShownAndEditableAttributes(
            ('confidentiality_display', 'confidentiality_edit', 'signed_edit'))
        self._setupStorePodAsAnnex()
        # create an item
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')

        # add a decision annex as MeetingManager
        # configure annex_type "decision" so it is "to_sign" by default
        self.changeUser('pmManager')
        decision_annex_type = cfg.annexes_types.item_decision_annexes.get('decision-annex')
        decision_annex_type_group = decision_annex_type.get_category_group()
        decision_annex_type_group.signed_activated = True
        decision_annex_type.to_sign = True
        # add annex
        annex_decision = self.addAnnex(item, relatedTo='item_decision')
        self.assertTrue(annex_decision.to_sign)
        self.assertTrue(bool(get_categorized_elements(item)))

        # not viewable by 'pmCreator1'
        self.changeUser('pmCreator1')
        self.assertFalse(bool(get_categorized_elements(item)))

        # use the actionview to switch to signed so annex is viewable
        view = annex_decision.restrictedTraverse('@@iconified-signed')
        # if pmCreator1 tries, he gets Unauthorized
        self.assertRaises(Unauthorized, view.set_values, {'signed': True})
        # pmManager may change value
        self.changeUser('pmManager')
        view.set_values({'to_sign': True, 'signed': True})
        self.assertTrue(annex_decision.to_sign, item.categorized_elements[annex_decision.UID()]['to_sign'])
        self.assertTrue(annex_decision.signed, item.categorized_elements[annex_decision.UID()]['signed'])
        # annex is viewable
        self.changeUser('pmCreator1')
        self.assertTrue(bool(get_categorized_elements(item)))
