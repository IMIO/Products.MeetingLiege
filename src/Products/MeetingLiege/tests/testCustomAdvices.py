# -*- coding: utf-8 -*-
#
# File: testAdvices.py
#
# Copyright (c) 2007-2015 by Imio.be
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

from zope.component import queryUtility
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.interfaces import IVocabularyFactory

from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer

from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.events import _everyAdvicesAreGivenFor
from Products.MeetingLiege.setuphandlers import _configureCollegeCustomAdvisers
from Products.MeetingLiege.setuphandlers import _createFinanceGroups
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase


class testCustomAdvices(MeetingLiegeTestCase):
    '''Tests various aspects of advices management.
       Advices are enabled for PloneGov Assembly, not for PloneMeeting Assembly.'''

    def test_FinancialManagerMayChangeAdviceDelayWhenAddableOrEditable(self):
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
                                          'meetingadvicefinances',
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
        self.assertFalse(item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_editable'])
        self.assertTrue(not delayView._mayEditDelays(isAutomatic=isAutomatic))

    def test_ItemSentBackToAskerWhenEveryAdvicesGiven(self):
        '''Check that, when every advices are given, the item is automatically sent back to 'itemcreated'
           of 'proposed_to_internal_reviewer' depending on which 'waiting advices' state it is.'''
        self.changeUser('admin')
        self.meetingConfig.setUsedAdviceTypes(self.meetingConfig.getUsedAdviceTypes() + ('asked_again', ))
        self.meetingConfig.setItemAdviceStates(('itemcreated_waiting_advices',
                                                'proposed_to_internal_reviewer_waiting_advices'))
        self.meetingConfig.setItemAdviceEditStates = (('itemcreated_waiting_advices',
                                                       'proposed_to_internal_reviewer_waiting_advices'))
        self.meetingConfig.setItemAdviceViewStates = (('itemcreated_waiting_advices',
                                                       'proposed_to_administrative_reviewer',
                                                       'proposed_to_internal_reviewer',
                                                       'proposed_to_internal_reviewer_waiting_advices',
                                                       'proposed_to_director', 'validated', 'presented',
                                                       'itemfrozen', 'refused', 'delayed', 'removed',
                                                       'pre_accepted', 'accepted', 'accepted_but_modified', ))
        _configureCollegeCustomAdvisers(self.portal)
        _createFinanceGroups(self.portal)
        self._setupFinanceGroups()

        # ask finance advice and vendors advice
        # finance advice is not considered in the case we test here
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem', title='The item')
        item.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        item.setOptionalAdvisers(('vendors', ))
        item.at_post_edit_script()
        self.assertTrue(FINANCE_GROUP_IDS[0] in item.adviceIndex)
        self.assertTrue('vendors' in item.adviceIndex)

        # check when item is 'itemcreated_waiting_advices'
        self._checkItemSentBackToServiceWhenEveryAdvicesGiven(item,
                                                              askAdvicesTr='askAdvicesByItemCreator',
                                                              availableBackTr='backToItemCreated',
                                                              returnState='itemcreated')
        # Give to pmInternalReviewer1 the creator role to grant him access to
        # items in creation.
        self.changeUser('admin')
        pg = self.portal.portal_groups
        dcGroup = pg.getGroupById('developers_creators')
        dcGroup.addMember('pmInternalReviewer1')

        # now check for 'proposed_to_internal_reviewer_waiting_advices'
        # From item created.
        self.deleteAsManager(item.meetingadvice.UID())
        self.changeUser('pmInternalReviewer1')
        self._checkItemSentBackToServiceWhenEveryAdvicesGiven(item,
                                                              askAdvicesTr='askAdvicesByInternalReviewer',
                                                              availableBackTr='backToProposedToInternalReviewer',
                                                              returnState='proposed_to_internal_reviewer')

        # From proposed to administrative reviewer.
        self.deleteAsManager(item.meetingadvice.UID())
        self.changeUser('pmManager')
        self.do(item, 'backToProposedToAdministrativeReviewer')
        self.changeUser('pmInternalReviewer1')
        self._checkItemSentBackToServiceWhenEveryAdvicesGiven(item,
                                                              askAdvicesTr='askAdvicesByInternalReviewer',
                                                              availableBackTr='backToProposedToInternalReviewer',
                                                              returnState='proposed_to_internal_reviewer')

        # From proposed to internal reviewer.
        self.deleteAsManager(item.meetingadvice.UID())
        self.changeUser('pmInternalReviewer1')
        self._checkItemSentBackToServiceWhenEveryAdvicesGiven(item,
                                                              askAdvicesTr='askAdvicesByInternalReviewer',
                                                              availableBackTr='backToProposedToInternalReviewer',
                                                              returnState='proposed_to_internal_reviewer')

    def _checkItemSentBackToServiceWhenEveryAdvicesGiven(self,
                                                         item,
                                                         askAdvicesTr,
                                                         availableBackTr,
                                                         returnState):
        """Helper method for 'test_subproduct_ItemSentBackToAskerWhenEveryAdvicesGiven'."""
        # save current logged in user, the group asker user
        adviceAskerUserId = self.member.getId()
        # ask advices
        self.do(item, askAdvicesTr)
        # item can be sent back to returnState by creator even if every advices are not given
        self.assertTrue(availableBackTr in self.transitions(item))
        self.assertFalse(_everyAdvicesAreGivenFor(item))

        # now add advice as vendors and do not hide it, advice will be considered given
        self.changeUser('pmReviewer2')
        createContentInContainer(item,
                                 'meetingadvice',
                                 **{'advice_group': 'vendors',
                                    'advice_type': u'positive',
                                    'advice_hide_during_redaction': False,
                                    'advice_comment': RichTextValue(u'My comment')})
        # directly sent back to service
        self.assertTrue(item.queryState() == returnState)
        self.assertTrue(_everyAdvicesAreGivenFor(item))

        # now add advice as vendors and do not hide it, advice will be considered given
        self.changeUser('admin')
        item.restrictedTraverse('@@delete_givenuid')(item.meetingadvice.UID())
        self.do(item, askAdvicesTr)
        self.changeUser('pmReviewer2')
        advice = createContentInContainer(item,
                                          'meetingadvice',
                                          **{'advice_group': 'vendors',
                                             'advice_type': u'positive',
                                             'advice_hide_during_redaction': True,
                                             'advice_comment': RichTextValue(u'My comment')})
        # still waiting advices
        self.assertTrue(item.queryState() == '{0}_waiting_advices'.format(returnState))
        self.assertFalse(_everyAdvicesAreGivenFor(item))
        # if we just change 'advice_hide_during_redaction', advice is given and item's sent back
        advice.advice_hide_during_redaction = False
        notify(ObjectModifiedEvent(advice))
        self.assertTrue(item.queryState() == returnState)
        self.assertTrue(_everyAdvicesAreGivenFor(item))

        # now test with 'asked_again'
        self.changeUser(adviceAskerUserId)
        advice.restrictedTraverse('@@change-advice-asked-again')()
        self.assertTrue(advice.advice_type == 'asked_again')
        self.do(item, askAdvicesTr)
        self.changeUser('pmReviewer2')
        notify(ObjectModifiedEvent(advice))
        # still waiting advices
        self.assertTrue(item.queryState() == '{0}_waiting_advices'.format(returnState))
        self.assertFalse(_everyAdvicesAreGivenFor(item))
        # change advice_type, it will be sent back then
        advice.advice_type = u'positive'
        notify(ObjectModifiedEvent(advice))
        self.assertTrue(item.queryState() == returnState)
        self.assertTrue(_everyAdvicesAreGivenFor(item))

    def test_AdviceTypeVocabulary(self):
        """'Products.PloneMeeting.content.advice.advice_type_vocabulary' was overrided
           to manage values of finance advice."""
        item, finance_advice = self._setupCollegeItemWithFinanceAdvice()
        self.changeUser('pmManager')
        vocab = queryUtility(IVocabularyFactory,
                             "Products.PloneMeeting.content.advice.advice_type_vocabulary")
        # ask 'vendors' advice on item
        item.setOptionalAdvisers(('vendors', ))
        item.at_post_edit_script()
        self.do(item, 'backToProposedToDirector')
        vendors_advice = createContentInContainer(
            item,
            'meetingadvice',
            **{'advice_group': 'vendors',
               'advice_type': u'negative',
               'advice_comment': RichTextValue(u'<p>My comment vendors</p>'),
               'advice_observations': RichTextValue(u'<p>My observation vendors</p>')})
        finance_keys = vocab(finance_advice).by_value.keys()
        finance_keys.sort()
        self.assertEquals(finance_keys,
                          ['negative_finance', 'not_required_finance',
                           'positive_finance', 'positive_with_remarks_finance'])
        vendors_keys = vocab(vendors_advice).by_value.keys()
        vendors_keys.sort()
        self.assertEquals(vendors_keys,
                          ['negative', 'nil', 'positive', 'positive_with_remarks'])
