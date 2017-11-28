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

from collective.iconifiedcategory.utils import get_categorized_elements
from collective.iconifiedcategory.utils import get_category_object
from Products.CMFCore.permissions import ModifyPortalContent
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase


class testCustomViews(MeetingLiegeTestCase):
    """Tests the Meeting adapted methods."""

    def test_MLSignedChangeView(self):
        """SignedChangeView was overrided so only MeetingManagers may set
           an element as 'to_sign' or 'signed'."""
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        annex = self.addAnnex(item)
        view = annex.restrictedTraverse('@@iconified-signed')
        category = get_category_object(annex, annex.content_category)
        group = category.get_category_group()
        group.signed_activated = True

        # for non (Meeting)Managers, nothing doable even if annex editable
        self.assertTrue(self.hasPermission(ModifyPortalContent, annex))
        self.assertFalse(view._may_set_values({}))

        # (Meeting)Managers are able to set an element as signed
        self.changeUser('pmManager')
        self.assertTrue(self.hasPermission(ModifyPortalContent, annex))
        self.assertTrue(view._may_set_values({}))
        # 'loop between possibilities'not to sign' to 'to sign'
        self.assertEqual(
            view._get_next_values({'to_sign': False, 'signed': False}),
            (0, {'to_sign': True, 'signed': False}))
        # 'to sign' to 'signed'
        self.assertEqual(
            view._get_next_values({'to_sign': True, 'signed': False}),
            (1, {'to_sign': True, 'signed': True}))
        # 'signed' to 'not to sign'
        self.assertEqual(
            view._get_next_values({'to_sign': True, 'signed': True}),
            (-1, {'to_sign': False, 'signed': False}))

    def test_DecisionAnnexToSignOnlyViewableToMeetingManagers(self):
        '''When the 'deliberation' is added as decision annex 'to sign', nobody else
           but (Meeting)Managers may see the annex.'''
        cfg = self.meetingConfig
        self._setupStorePodAsAnnex()
        # create an item
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')

        # add a decision annex as MeetingManager
        # configure annex_type "decision" so it is "to_sign" by default
        self.changeUser('pmManager')
        decision_annex = cfg.annexes_types.item_decision_annexes.get('decision-annex')
        decision_annex_group = decision_annex.get_category_group()
        decision_annex_group.signed_activated = True
        decision_annex.to_sign = True
        # add annex
        annex = self.addAnnex(item, relatedTo='item_decision')
        self.assertTrue(annex.to_sign)
        self.assertTrue(bool(get_categorized_elements(item)))

        # not viewable by 'pmCreator1'
        self.changeUser('pmCreator1')
        self.assertFalse(bool(get_categorized_elements(item)))
