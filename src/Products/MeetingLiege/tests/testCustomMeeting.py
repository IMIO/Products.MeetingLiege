# -*- coding: utf-8 -*-
#
# File: testCustomMeeting.py
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

from Products.MeetingLalouviere.tests.MeetingLalouviereTestCase import \
    MeetingLalouviereTestCase


class testCustomMeeting(MeetingLalouviereTestCase):
    """
        Tests the Meeting adapted methods
    """

    def test_getCategories(self):
        """
          Check what are returned while getting different types of categories
          This method is used in "meeting-config-council"
        """
        self.meetingConfig = self.meetingConfig2
        # add some "Suppl" categories
        self.changeUser('admin')
        supplCategories = ['deployment-1er-supplement',
                           'maintenance-1er-supplement',
                           'development-1er-supplement',
                           'events-1er-supplement',
                           'research-1er-supplement',
                           'projects-1er-supplement',
                           'marketing-1er-supplement',
                           'subproducts-1er-supplement',
                           'points-conseillers-2eme-supplement',
                           'points-conseillers-3eme-supplement']
        for supplCat in supplCategories:
            newCatId = self.meetingConfig.categories.invokeFactory('MeetingCategory',
                                                                   id=supplCat,
                                                                   title='supplCat')
            newCat = getattr(self.meetingConfig.categories, newCatId)
            newCat.processForm()
        self.changeUser('pmManager')
        m = self.create('Meeting', date='2009/11/26 09:00:00')
        expectedNormal = ['deployment',
                          'maintenance',
                          'development',
                          'events',
                          'research',
                          'projects',
                          'marketing',
                          'subproducts']
        self.assertEquals(m.getNormalCategories(), expectedNormal)

        expectedFirstSuppl = ['deployment-1er-supplement',
                              'maintenance-1er-supplement',
                              'development-1er-supplement',
                              'events-1er-supplement',
                              'research-1er-supplement',
                              'projects-1er-supplement',
                              'marketing-1er-supplement',
                              'subproducts-1er-supplement']
        self.assertEquals(m.getFirstSupplCategories(), expectedFirstSuppl)
        expectedSecondSuppl = ['points-conseillers-2eme-supplement']
        self.assertEquals(m.getSecondSupplCategories(), expectedSecondSuppl)
        expectedThirdSuppl = ['points-conseillers-3eme-supplement']
        self.assertEquals(m.getThirdSupplCategories(), expectedThirdSuppl)

    def test_getAvailableItems(self):
        '''
          Already tested in MeetingLaouviere.tests.testMeeting.py
        '''
        pass
