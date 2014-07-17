# -*- coding: utf-8 -*-
#
# File: testWorkflows.py
#
# Copyright (c) 2007-2014 by Imio.be
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

from zope.i18n import translate
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer

from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName

from Products.PloneMeeting.indexes import indexAdvisers

from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.setuphandlers import _configureCollegeCustomAdvisers
from Products.MeetingLiege.setuphandlers import _createFinanceGroups
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.MeetingCommunes.tests.testWorkflows import testWorkflows as mctw


class testWorkflows(MeetingLiegeTestCase, mctw):
    """Tests the default workflows implemented in MeetingLiege."""

    def test_subproduct_call_WholeDecisionProcess(self):
        """This test is bypassed, we use several tests here under."""
        pass

    def test_subproduct_CollegeProcessWithoutAdvices(self):
        '''This test covers the whole decision workflow. It begins with the
           creation of some items, and ends by closing a meeting.
           The usecase here is to test the workflow without normal and finances advice.'''
        # pmCreator1 creates an item and proposes it to the administrative reviewer
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem', title='The first item')
        # pmCreator may only 'proposeToAdministrativeReviewer'
        self.assertTrue(self.transitions(item) == ['proposeToAdministrativeReviewer', ])
        # a MeetingManager is able to validate an item immediatelly, bypassing the entire validation workflow
        self.changeUser('pmManager')
        self.assertTrue(self.transitions(item) == ['proposeToAdministrativeReviewer',
                                                   'validate', ])
        # the pmCreator1 send the item to the administrative reviewer
        self.changeUser('pmCreator1')
        self.do(item, 'proposeToAdministrativeReviewer')
        # pmCreator1 can no more edit item but can still view it
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, item))
        self.changeUser('pmAdminReviewer1')
        # pmAdminReviewer1 may access item and edit it
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(self.hasPermission(ModifyPortalContent, item))
        # he may send the item back to the pmCreator1 or send it to the internal reviewer
        self.assertTrue(self.transitions(item) == ['backToItemCreated',
                                                   'proposeToInternalReviewer', ])
        self.do(item, 'proposeToInternalReviewer')
        # pmAdminReviewer1 can no more edit item but can still view it
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, item))
        # pmInternalReviewer1 may access item and edit it
        self.changeUser('pmInternalReviewer1')
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(self.hasPermission(ModifyPortalContent, item))
        # he may send the item back to the administrative reviewer or send it to the reviewer (director)
        self.assertTrue(self.transitions(item) == ['backToProposedToAdministrativeReviewer',
                                                   'proposeToDirector', ])
        self.do(item, 'proposeToDirector')
        # pmInternalReviewer1 can no more edit item but can still view it
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, item))
        # pmReviewer1 (director) may access item and edit it
        self.changeUser('pmReviewer1')
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(self.hasPermission(ModifyPortalContent, item))
        # he may send the item back to the internal reviewer or validate it
        self.assertTrue(self.transitions(item) == ['backToProposedToInternalReviewer',
                                                   'validate', ])
        self.do(item, 'validate')
        # pmReviewer1 can no more edit item but can still view it
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, item))

        # create a meeting, a MeetingManager will manage it now
        self.changeUser('pmManager')
        # the item can be removed sent back to the reviewer (director) or sent back in 'itemcreated'
        self.assertTrue(self.transitions(item) == ['backToItemCreated',
                                                   'backToProposedToDirector', ])
        meeting = self.create('Meeting', date='2014/01/01 09:00:00')
        # the item is available for the meeting
        availableItemUids = [brain.UID for brain in meeting.getAvailableItems()]
        self.assertTrue(item.UID() in availableItemUids)
        self.do(item, 'present')
        self.assertTrue(item.queryState() == 'presented')
        # the item can be removed from the meeting or sent back in 'itemcreated'
        self.assertTrue(self.transitions(item) == ['backToValidated', ])
        # the meeting can now be frozen then decided
        self.do(meeting, 'freeze')
        # the item has been automatically frozen
        self.assertTrue(item.queryState() == 'itemfrozen')
        # but the item can be sent back to 'presented'
        self.assertTrue(self.transitions(item) == ['backToPresented', ])
        self.do(meeting, 'decide')
        # the item is still frozen but can be decided
        self.assertTrue(item.queryState() == 'itemfrozen')
        self.assertTrue(self.transitions(item) == ['accept',
                                                   'accept_but_modify',
                                                   'backToPresented',
                                                   'delay',
                                                   'mark_not_applicable',
                                                   'pre_accept',
                                                   'refuse'])
        # if we pre_accept an item, we can accept it after
        self.do(item, 'pre_accept')
        self.assertTrue(self.transitions(item) == ['accept',
                                                   'accept_but_modify',
                                                   'backToItemFrozen'])
        # if we decide an item, it may still be set backToItemFrozen until the meeting is closed
        self.do(item, 'accept')
        self.assertTrue(self.transitions(item) == ['backToItemFrozen', ])
        # the meeting may be closed or back to frozen
        self.assertTrue(self.transitions(meeting) == ['backToFrozen',
                                                      'close', ])
        self.do(meeting, 'close')
        self.assertTrue(not self.transitions(item))

    def test_subproduct_CollegeProcessWithNormalAdvices(self):
        '''How does the process behave when some 'normal' advices,
           aka not 'finances' advices are aksed.'''
        # normal advices can be given when item in state 'itemcreated_waiting_advices',
        # asked by item creator and when item in state 'proposed_to_internal_reviewer_waiting_advices',
        # asekd by internal reviewer
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
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem', title='The first item')
        # if no advice to ask, pmCreator may only 'proposeToAdministrativeReviewer'
        self.assertTrue(self.transitions(item) == ['proposeToAdministrativeReviewer', ])
        # the mayAskAdvicesByItemCreator wfCondition returns a 'No' instance
        advice_required_to_ask_advices = translate('advice_required_to_ask_advices',
                                                   domain='PloneMeeting',
                                                   context=self.request)
        self.assertTrue(item.wfConditions().mayAskAdvicesByItemCreator().msg == advice_required_to_ask_advices)
        # now ask 'vendors' advice
        item.setOptionalAdvisers(('vendors', ))
        item.at_post_edit_script()
        self.assertTrue(self.transitions(item) == ['askAdvicesByItemCreator',
                                                   'proposeToAdministrativeReviewer', ])
        # give advice
        self.do(item, 'askAdvicesByItemCreator')
        # pmReviewer2 is adviser for vendors
        self.changeUser('pmReviewer2')
        createContentInContainer(item,
                                 'meetingadvice',
                                 **{'advice_group': 'vendors',
                                    'advice_type': u'positive',
                                    'advice_comment': RichTextValue(u'My comment vendors')})
        # no more advice to give
        self.assertTrue(not item.hasAdvices(toGive=True))
        # item may be proposed directly to administrative reviewer
        # from state 'itemcreated_waiting_advices'
        # we continue wf as internal reviewer may also ask advice
        self.changeUser('pmCreator1')
        self.do(item, 'proposeToAdministrativeReviewer')
        self.changeUser('pmAdminReviewer1')
        self.do(item, 'proposeToInternalReviewer')
        self.changeUser('pmInternalReviewer1')
        # no advice to give so not askable
        self.assertTrue(self.transitions(item) == ['backToProposedToAdministrativeReviewer',
                                                   'proposeToDirector', ])
        item.setOptionalAdvisers(('vendors', 'developers'))
        item.at_post_edit_script()
        # now that there is an advice to give (developers)
        # internal reviewer may ask it
        self.assertTrue(self.transitions(item) == ['askAdvicesByInternalReviewer',
                                                   'backToProposedToAdministrativeReviewer',
                                                   'proposeToDirector', ])
        # give advice
        self.do(item, 'askAdvicesByInternalReviewer')
        # pmAdviser1 is adviser for developers
        self.changeUser('pmAdviser1')
        createContentInContainer(item,
                                 'meetingadvice',
                                 **{'advice_group': 'developers',
                                    'advice_type': u'positive',
                                    'advice_comment': RichTextValue(u'My comment developers')})
        # item may be proposed directly to director
        # from state 'proposed_to_internal_reviewer_waiting_advices'
        self.changeUser('pmInternalReviewer1')
        self.do(item, 'proposeToDirector')

    def _setupFinanceGroups(self):
        '''Configure finance groups.'''
        groupsTool = getToolByName(self.portal, 'portal_groups')
        # add pmFinController, pmFinReviewer and pmFinManager to advisers and to their respective finance group
        groupsTool.addPrincipalToGroup('pmFinController', '%s_advisers' % FINANCE_GROUP_IDS[0])
        groupsTool.addPrincipalToGroup('pmFinReviewer', '%s_advisers' % FINANCE_GROUP_IDS[0])
        groupsTool.addPrincipalToGroup('pmFinManager', '%s_advisers' % FINANCE_GROUP_IDS[0])
        groupsTool.addPrincipalToGroup('pmFinController', '%s_financialcontrollers' % FINANCE_GROUP_IDS[0])
        groupsTool.addPrincipalToGroup('pmFinReviewer', '%s_financialreviewers' % FINANCE_GROUP_IDS[0])
        groupsTool.addPrincipalToGroup('pmFinManager', '%s_financialmanagers' % FINANCE_GROUP_IDS[0])

    def test_subproduct_CollegeProcessWithFinancesAdvices(self):
        '''How does the process behave when some 'finances' advices is asked.'''
        self.changeUser('admin')
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # add finance groups
        _createFinanceGroups(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # by default, an item with no selected archivingRef does
        # not need a finances advice
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='The first item')
        self.assertTrue(not item.adapted().getFinanceGroupIdsForItem())
        self.assertTrue(not item.adviceIndex)
        # finances advice is an automatic advice aksed depending on the
        # selected archivingRef.  In self.meetingConfig.archivingRefs,
        # we define which finances group has to give advice for a given archiving ref
        # ask 'df-contrale' advice
        item.setArchivingRef('012')
        item.at_post_edit_script()
        self.assertTrue(item.adapted().getFinanceGroupIdsForItem() == FINANCE_GROUP_IDS[0])
        self.assertTrue(FINANCE_GROUP_IDS[0] in item.adviceIndex)
        # now that it is asked, the item will have to be proposed to the finances
        # pmManager is member of every sub-groups of 'developers'
        self.proposeItem(item)
        # now the item is 'proposed_to_director' it can not be validated
        # the step 'proposed_to_finances' is required
        self.assertTrue(item.queryState() == 'proposed_to_director')
        # from here, we can not validate the item, it can only be sent
        # to the finances or back to the internal reviewer
        self.assertTrue(self.transitions(item) == ['backToProposedToInternalReviewer',
                                                   'proposeToFinance'])
        # for now, advisers of the FINANCE_GROUP_IDS[0] can not give the advice
        self.assertTrue(not item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_addable'])
        # proposeToFinance, advice will be giveable
        self.do(item, 'proposeToFinance')
        self.assertTrue(item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_addable'])
        self._cleanRamCacheFor('Products.PloneMeeting.ToolPloneMeeting.getGroupsForUser')
        # pmFinController may add advice for FINANCE_GROUP_IDS[0]
        self.changeUser('pmFinController')
        toAdd, toEdit = item.getAdvicesGroupsInfosForUser()
        self.assertTrue(toAdd[0][0] == FINANCE_GROUP_IDS[0])
        # he may also return the item to the internal reviewer if he considers
        # that the completeness of the item is 'incomplete'
        # for now, completeness not evaluated, the item has no available transitions
        self.assertTrue(not self.transitions(item))
        # set the item to "incomplete"
        item.setCompleteness('completeness_incomplete')
        self.assertTrue(self.transitions(item) == ['backToProposedToInternalReviewer'])
        # set item as "complete"
        item.setCompleteness('completeness_complete')
        self.assertTrue(not self.transitions(item))
        # give the advice
        advice = createContentInContainer(item,
                                          'meetingadvice',
                                          **{'advice_group': FINANCE_GROUP_IDS[0],
                                             'advice_type': u'positive_finance',
                                             'advice_comment': RichTextValue(u'My comment finance')})
        # when created, a finance advice is automatically set to 'proposed_to_financial_controller'
        self.assertTrue(advice.queryState() == 'proposed_to_financial_controller')
        # when a financial advice is added, advice_hide_during_redaction
        # is True, no matter MeetingConfig.defaultAdviceHiddenDuringRedaction
        # it is automatically set to False when advice will be "signed" (aka "published")
        self.assertTrue(advice.advice_hide_during_redaction)
        self.assertTrue(self.hasPermission(View, advice))
        self.assertTrue(self.hasPermission(ModifyPortalContent, advice))
        # the advice can be proposed to the financial reviewer
        self.assertTrue(self.transitions(advice) == ['proposeToFinancialReviewer'])
        self.do(advice, 'proposeToFinancialReviewer')
        # can no more edit, but still view
        self.assertTrue(self.hasPermission(View, advice))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, advice))
        # log as finance reviewer
        self.changeUser('pmFinReviewer')
        # may view and edit
        self.assertTrue(advice.queryState() == 'proposed_to_financial_reviewer')
        self.assertTrue(self.hasPermission(View, advice))
        self.assertTrue(self.hasPermission(ModifyPortalContent, advice))
        # may return to finance controller, send to finance manager or sign the advice
        self.assertTrue(self.transitions(advice) == ['backToProposedToFinancialController',
                                                     'proposeToFinancialManager',
                                                     'signFinancialAdvice'])
        # finance reviewer may sign (publish) advice because the advice_type
        # is not "negative", if negative, it is the finance manager that will
        # be able to sign the advice
        advice.advice_type = u'negative_finance'
        self.assertTrue(self.transitions(advice) == ['backToProposedToFinancialController',
                                                     'proposeToFinancialManager'])
        # propose to financial manager that will sign the advice
        self.do(advice, 'proposeToFinancialManager')
        self.assertTrue(self.hasPermission(View, advice))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, advice))
        # log as finance manager
        self.changeUser('pmFinManager')
        # may view and edit
        self.assertTrue(advice.queryState() == 'proposed_to_financial_manager')
        self.assertTrue(self.hasPermission(View, advice))
        self.assertTrue(self.hasPermission(ModifyPortalContent, advice))
        # the financial manager may either sign the advice
        # or send it back to the financial reviewer or controller
        self.assertTrue(self.transitions(advice) == ['backToProposedToFinancialController',
                                                     'backToProposedToFinancialReviewer',
                                                     'signFinancialAdvice'])
        # if a financial manager sign a negative advice, the linked item will
        # be automatically sent back to the director, the advice is no more editable
        # moreover, when signed, the advice is automatically set to advice_hide_during_redaction=False
        self.assertTrue(advice.advice_hide_during_redaction)
        self.do(advice, 'signFinancialAdvice')
        self.assertTrue(item.queryState() == 'proposed_to_director')
        self.assertTrue(advice.queryState() == 'advice_given')
        self.assertTrue(not advice.advice_hide_during_redaction)
        # now an item with a negative financial advice back to the director
        # can be validated by the director, he takes the responsibility to validate
        # an item with a negative is able to propose the item again to the financial group
        # or it can validate the item
        self.changeUser('pmReviewer1')
        self.assertTrue(self.transitions(item) == ['backToProposedToInternalReviewer',
                                                   'proposeToFinance',
                                                   'validate'])
        # it can send it again to the finance and finance can adapt the advice
        self.do(item, 'proposeToFinance')
        self.assertTrue(item.queryState() == 'proposed_to_finance')
        # advice is available to the financial controller
        self.assertTrue(advice.queryState() == 'proposed_to_financial_controller')
        # and is hidden again
        self.assertTrue(advice.advice_hide_during_redaction)
        # now he will change the advice_type to 'positive_finance'
        # and the financial reviewer will sign it
        self.changeUser('pmFinController')
        advice.advice_type = u'positive_finance'
        # advice may only be sent to the financial reviewer
        self.assertTrue(self.transitions(advice) == ['proposeToFinancialReviewer'])
        self.do(advice, 'proposeToFinancialReviewer')
        self.changeUser('pmFinReviewer')
        # financial reviewer may sign a positive advice or send it to the finance manager
        self.assertTrue(self.transitions(advice) == ['backToProposedToFinancialController',
                                                     'proposeToFinancialManager',
                                                     'signFinancialAdvice'])
        self.do(advice, 'signFinancialAdvice')
        # this time, the item has been validated automatically
        self.assertTrue(item.queryState() == 'validated')
        # and the advice is visible to everybody
        self.assertTrue(not advice.advice_hide_during_redaction)
        # the trick is that as item state is still in itemAdviceStates,
        # the advice is not 'advice_given' but in a state 'financial_advice_signed'
        # where nobody can change anything neither...
        financeGrp = getattr(self.tool, FINANCE_GROUP_IDS[0])
        self.assertTrue('%s__state__validated' % self.meetingConfig.getId() in financeGrp.getItemAdviceStates())
        self.assertTrue('%s__state__validated' % self.meetingConfig.getId() in financeGrp.getItemAdviceEditStates())
        self.assertTrue(advice.queryState() == 'financial_advice_signed')
        # item.adviceIndex is coherent also, the 'addable'/'editable' data is correct
        self.assertTrue(not item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_editable'])
        self.assertTrue(not item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_addable'])
        # advice is viewable
        # but is no more editable by any financial role
        # not for financial reviewer
        self.assertTrue(self.hasPermission(View, advice))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, advice))
        # not for financial controller
        self.changeUser('pmFinController')
        self.assertTrue(self.hasPermission(View, advice))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, advice))
        # no more for financial manager
        self.changeUser('pmFinManager')
        self.assertTrue(self.hasPermission(View, advice))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, advice))
        # if the advice is no more editable, it's state switched to 'advice_given'
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date='2014/01/01 09:00:00')
        # close the meeting, the advice will be set to 'advice_given'
        # the advice could still be given if not already in state 'presented' and 'itemfrozen'
        self.presentItem(item)
        self.closeMeeting(meeting)
        self.assertTrue(meeting.queryState() == 'closed')
        self.assertTrue(advice.queryState() == 'advice_given')

    def test_subproduct_IndexAdvisersIsCorrectAfterAdviceTransition(self):
        '''Test that when a transition is triggered on a meetingadvice
           using finance workflow, the indexAdvisers index is always correct.'''
        self.changeUser('admin')
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # add finance groups
        _createFinanceGroups(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # by default, an item with no selected archivingRef does
        # not need a finances advice
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='The first item')
        item.setArchivingRef('012')
        item.at_post_edit_script()
        # the finance advice is asked
        self.assertTrue(item.adapted().getFinanceGroupIdsForItem() == FINANCE_GROUP_IDS[0])
        self.assertTrue(FINANCE_GROUP_IDS[0] in item.adviceIndex)
        # send item to finance
        self.proposeItem(item)
        self.assertTrue(item.queryState() == 'proposed_to_director')
        self.do(item, 'proposeToFinance')
        # give the advice
        self.changeUser('pmFinController')
        advice = createContentInContainer(item,
                                          'meetingadvice',
                                          **{'advice_group': FINANCE_GROUP_IDS[0],
                                             'advice_type': u'positive_finance',
                                             'advice_comment': RichTextValue(u'My comment finance')})
        # now play advice finance workflow and check catalog indexAdvisers is correct
        catalog = getToolByName(self.portal, 'portal_catalog')
        itemPath = item.absolute_url_path()
        # when created, a finance advice is automatically set to 'proposed_to_financial_controller'
        self.assertTrue(advice.queryState() == 'proposed_to_financial_controller')
        self.assertTrue(indexAdvisers(item)() == catalog.getIndexDataForUID(itemPath)['indexAdvisers'])
        # as finance controller
        self.do(advice, 'proposeToFinancialReviewer')
        self.assertTrue(advice.queryState() == 'proposed_to_financial_reviewer')
        self.assertTrue(indexAdvisers(item)() == catalog.getIndexDataForUID(itemPath)['indexAdvisers'])
        # as finance reviewer
        self.changeUser('pmFinReviewer')
        advice.advice_type = u'negative_finance'
        self.do(advice, 'proposeToFinancialManager')
        self.assertTrue(advice.queryState() == 'proposed_to_financial_manager')
        self.assertTrue(indexAdvisers(item)() == catalog.getIndexDataForUID(itemPath)['indexAdvisers'])
        # log as finance manager
        self.changeUser('pmFinManager')
        self.do(advice, 'signFinancialAdvice')
        # item was sent back to director
        self.assertTrue(item.queryState() == 'proposed_to_director')
        self.assertTrue(advice.queryState() == 'advice_given')
        self.assertTrue(indexAdvisers(item)() == catalog.getIndexDataForUID(itemPath)['indexAdvisers'])
        # send item again to finance
        self.changeUser('pmReviewer1')
        self.do(item, 'proposeToFinance')
        self.assertTrue(item.queryState() == 'proposed_to_finance')
        self.assertTrue(indexAdvisers(item)() == catalog.getIndexDataForUID(itemPath)['indexAdvisers'])
        # advice is available to the financial controller
        self.changeUser('pmFinController')
        self.assertTrue(advice.queryState() == 'proposed_to_financial_controller')
        advice.advice_type = u'positive_finance'
        self.do(advice, 'proposeToFinancialReviewer')
        self.assertTrue(advice.queryState() == 'proposed_to_financial_reviewer')
        self.assertTrue(indexAdvisers(item)() == catalog.getIndexDataForUID(itemPath)['indexAdvisers'])
        self.changeUser('pmFinReviewer')
        self.do(advice, 'signFinancialAdvice')
        # this time, the item has been validated automatically
        self.assertTrue(item.queryState() == 'validated')
        self.assertTrue(advice.queryState() == 'financial_advice_signed')
        self.assertTrue(indexAdvisers(item)() == catalog.getIndexDataForUID(itemPath)['indexAdvisers'])

    def test_subproduct_call_RemoveObjects(self):
        """
            Tests objects removal (items, meetings, annexes...).
        """
        # we do the test for the college config
        self.meetingConfig = getattr(self.tool, 'meeting-config-college')
        self.test_pm_RemoveObjects()
        # items are validated by default for the council config
        # so are not removable by item creators/reviewers
        #self.meetingConfig = getattr(self.tool, 'meeting-config-council')
        #self.test_pm_RemoveObjects()


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testWorkflows, prefix='test_subproduct_'))
    return suite
