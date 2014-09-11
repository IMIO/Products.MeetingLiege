# -*- coding: utf-8 -*-
#
# File: testAdvices.py
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
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer

from Products.MeetingCommunes.tests.testAdvices import testAdvices as mcta

from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.setuphandlers import _configureCollegeCustomAdvisers
from Products.MeetingLiege.setuphandlers import _createFinanceGroups
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase


class testAdvices(MeetingLiegeTestCase, mcta):
    '''Tests various aspects of advices management.
       Advices are enabled for PloneGov Assembly, not for PloneMeeting Assembly.'''

    def test_subproduct_FinancialManagerMayChangeAdviceDelayWhenAddableOrEditable(self):
        '''Check that a financial manager may still change advice asked to his financial
           group while the advice is still addable or editable.'''
        self.changeUser('admin')
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # add finance groups
        _createFinanceGroups(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # ask finance advice and ask advice (set item to 'proposed_to_finances')
        # not need a finances advice
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='The first item')
        item.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        item.at_post_edit_script()
        self.assertTrue(FINANCE_GROUP_IDS[0] in item.adviceIndex)
        self.proposeItem(item)
        self.do(item, 'proposeToFinance')
        item.setCompleteness('completeness_complete')
        item.at_post_edit_script()
        # ok, now advice can be given
        # a financial manager may change delays
        self.changeUser('pmFinManager')
        delayView = item.restrictedTraverse('@@advice-available-delays')
        # advice has been asked automatically
        isAutomatic = not bool(item.adviceIndex[FINANCE_GROUP_IDS[0]]['optional'])
        # advice is addable, delays may be changed
        self.assertTrue(delayView._mayEditDelays(isAutomatic=isAutomatic))
        # add the advice, delay still changeable as advice is editable
        advice = createContentInContainer(item,
                                          'meetingadvice',
                                          **{'advice_group': FINANCE_GROUP_IDS[0],
                                             'advice_type': u'positive_finance',
                                             'advice_comment': RichTextValue(u'My comment finance')})
        self.assertTrue(delayView._mayEditDelays(isAutomatic=isAutomatic))
        # other members of the finance group can not edit advice delay
        self.changeUser('pmFinController')
        self.assertTrue(not delayView._mayEditDelays(isAutomatic=isAutomatic))
        # send to financial reviewer
        self.do(advice, 'proposeToFinancialReviewer')
        self.assertTrue(not delayView._mayEditDelays(isAutomatic=isAutomatic))
        # delay editable by manager but not by others
        self.changeUser('pmFinManager')
        self.assertTrue(delayView._mayEditDelays(isAutomatic=isAutomatic))
        self.changeUser('pmFinReviewer')
        self.assertTrue(not delayView._mayEditDelays(isAutomatic=isAutomatic))
        # send to finance manager
        self.do(advice, 'proposeToFinancialManager')
        self.assertTrue(not delayView._mayEditDelays(isAutomatic=isAutomatic))
        # delay editable by finance manager but not by others
        self.changeUser('pmFinManager')
        self.assertTrue(delayView._mayEditDelays(isAutomatic=isAutomatic))
        # if manager sign the advice, so advice is no more editable
        # even the finance manager may no more edit advice delay
        self.do(advice, 'signFinancialAdvice')
        self.assertTrue(not delayView._mayEditDelays(isAutomatic=isAutomatic))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testAdvices, prefix='test_subproduct_'))
    return suite
