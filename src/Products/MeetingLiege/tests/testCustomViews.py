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

from collective.iconifiedcategory.utils import get_category_object

from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase


class testCustomViews(MeetingLiegeTestCase):
    """Tests the Meeting adapted methods."""

    def test_MLSignedChangeView(self):
        """SignedChangeView was overrided so only MeetingManagers may set an element as 'signed'."""
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        annex = self.addAnnex(item)
        view = annex.restrictedTraverse('@@iconified-signed')
        category = get_category_object(annex, annex.content_category)
        group = category.get_category_group()
        group.signed_activated = True

        # for non (Meeting)Managers, only able to switch from 'not to sign' to 'to sign', unable to set as 'signed'
        # 'not to sign' to 'to sign'
        self.assertEqual(
            view._get_next_values({'to_sign': False, 'signed': False}),
            (0, {'to_sign': True, 'signed': False}))
        # when when set 'to sign', the next value will be 'not to sign' and not 'signed'
        self.assertEqual(
            view._get_next_values({'to_sign': True, 'signed': False}),
            (-1, {'to_sign': False, 'signed': False}))

        # (Meeting)Managers are able to set an element as signed
        self.changeUser('pmManager')
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
