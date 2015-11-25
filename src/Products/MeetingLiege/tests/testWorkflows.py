# -*- coding: utf-8 -*-
#
# File: testWorkflows.py
#
# Copyright (c) 2015 by Imio.be
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

from datetime import datetime

from DateTime import DateTime

from AccessControl import Unauthorized
from zope.i18n import translate
from plone.app.textfield.value import RichTextValue
from plone.app.querystring import queryparser
from plone.dexterity.utils import createContentInContainer

from Products.CMFCore.permissions import DeleteObjects
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName

from Products.PloneMeeting.config import HISTORY_COMMENT_NOT_VIEWABLE
from Products.PloneMeeting.config import RESTRICTEDPOWEROBSERVERS_GROUP_SUFFIX
from Products.PloneMeeting.indexes import indexAdvisers
from Products.PloneMeeting.interfaces import IAnnexable
from Products.PloneMeeting.utils import getLastEvent

from Products.MeetingLiege.config import FINANCE_ADVICE_HISTORIZE_COMMENTS
from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.setuphandlers import _configureCollegeCustomAdvisers
from Products.MeetingLiege.setuphandlers import _createFinanceGroups
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.MeetingCommunes.tests.testWorkflows import testWorkflows as mctw

COUNCIL_LABEL = '<p>Label for Council.</p>'
COUNCIL_PRIVACY = 'secret'


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
        # a MeetingManager is able to validate an item immediatelly, bypassing
        # the entire validation workflow.
        # a director who is able to propose to administrative and internal
        # reviewer can also bypass those 2 transitions and propose the item directly to
        # the direction.
        self.changeUser('pmManager')
        self.assertTrue(self.transitions(item) == ['proposeToAdministrativeReviewer',
                                                   'proposeToDirector',
                                                   'proposeToInternalReviewer',
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
        # he may send the item back to the internal reviewer, validate it
        # or send it back to itemCreated.
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
        availableItemsQuery = queryparser.parseFormquery(meeting, meeting.adapted()._availableItemsQuery())
        availableItemUids = [brain.UID for brain in self.portal.portal_catalog(availableItemsQuery)]
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
                                                   'refuse',
                                                   'return'])
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
        self.meetingConfig.setUsedAdviceTypes(('asked_again', ) + self.meetingConfig.getUsedAdviceTypes())
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
        advice = createContentInContainer(item,
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
        # advice could be asked again
        self.assertTrue(item.adapted().mayAskAdviceAgain(advice))
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

    def test_subproduct_CollegeProcessWithFinancesAdvices(self):
        '''How does the process behave when some 'finances' advices is asked.'''
        self.changeUser('admin')
        self.meetingConfig.setUsedAdviceTypes(('asked_again', ) + self.meetingConfig.getUsedAdviceTypes())
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # add finance groups
        _createFinanceGroups(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # by default, an item with no selected financeAdvice does
        # not need a finances advice
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='The first item')
        self.assertTrue(not item.adapted().getFinanceGroupIdsForItem())
        self.assertTrue(not item.adviceIndex)
        # finances advice is an automatic advice aksed depending on the
        # selected MeetingItem.financeAdvice
        item.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        item.at_post_edit_script()
        self.assertTrue(item.adapted().getFinanceGroupIdsForItem() == FINANCE_GROUP_IDS[0])
        self.assertTrue(FINANCE_GROUP_IDS[0] in item.adviceIndex)
        # now that it is asked, the item will have to be proposed to the finances
        # pmManager is member of every sub-groups of 'developers'
        self.proposeItem(item)
        # now the item is 'proposed_to_director' it can not be validated
        # the step 'proposed_to_finance' is required
        self.assertTrue(item.queryState() == 'proposed_to_director')
        # from here, we can not validate the item, it can only be sent
        # to the finances or back to the internal reviewer.
        self.assertTrue(self.transitions(item) == ['backToProposedToInternalReviewer',
                                                   'proposeToFinance'])
        # if emergency is asked, a director may either propose the item to finance or validate it
        item.setEmergency('emergency_asked')
        self.assertTrue(self.transitions(item) == ['backToProposedToInternalReviewer',
                                                   'proposeToFinance',
                                                   'validate', ])
        item.setEmergency('no_emergency')
        # for now, advisers of the FINANCE_GROUP_IDS[0] can not give the advice
        self.assertTrue(not item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_addable'])
        # proposeToFinance, advice will not be giveable as item.completeness is not 'completeness_complete'
        self.do(item, 'proposeToFinance')
        self.assertTrue(not item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_addable'])
        # delay is not started, it only starts when item is complete
        self.assertTrue(not item.adviceIndex[FINANCE_GROUP_IDS[0]]['delay_started_on'])
        # if we updateAdvices, infos are still ok
        item.updateAdvices()
        # the item can be sent back to the internal reviewer by any finance role
        self.changeUser('pmFinController')
        self.assertTrue(self.transitions(item) == ['backToProposedToInternalReviewer'])
        # set the item to "incomplete"
        self.assertTrue(item.adapted().mayEvaluateCompleteness())
        item.setCompleteness('completeness_incomplete')
        item.at_post_edit_script()
        self.assertTrue(self.transitions(item) == ['backToProposedToInternalReviewer'])
        # pmFinController may not add advice for FINANCE_GROUP_IDS[0]
        toAdd, toEdit = item.getAdvicesGroupsInfosForUser()
        self.assertTrue(not toAdd and not toEdit)
        # set item as "complete" using itemcompleteness view
        # this way, it checks that current user may actually evaluate completeness
        # and item is updated (at_post_edit_script is called)
        changeCompleteness = item.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()
        self.assertTrue(item.getCompleteness() == 'completeness_complete')
        # can be sent back even if considered complete
        self.assertTrue(self.transitions(item) == ['backToProposedToInternalReviewer'])
        # but now, advice is giveable
        self.assertTrue(item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_addable'])
        # and delay to give advice is started
        self.assertTrue(item.adviceIndex[FINANCE_GROUP_IDS[0]]['delay_started_on'])
        # back to 'completeness_incomplete', advice can not be given anymore and delay is not started
        self.request.set('new_completeness_value', 'completeness_incomplete')
        changeCompleteness()
        self.assertTrue(item.getCompleteness() == 'completeness_incomplete')
        self.assertTrue(not item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_addable'])
        self.assertTrue(not item.adviceIndex[FINANCE_GROUP_IDS[0]]['delay_started_on'])
        # advice can also be given if completeness is 'completeness_evaluation_not_required'
        self.request.set('new_completeness_value', 'completeness_evaluation_not_required')
        changeCompleteness()
        self.assertTrue(item.getCompleteness() == 'completeness_evaluation_not_required')
        self.assertTrue(item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_addable'])
        self.assertTrue(item.adviceIndex[FINANCE_GROUP_IDS[0]]['delay_started_on'])
        # give the advice
        advice = createContentInContainer(item,
                                          'meetingadvice',
                                          **{'advice_group': FINANCE_GROUP_IDS[0],
                                             'advice_type': u'positive_finance',
                                             'advice_comment': RichTextValue(u'<p>My comment finance</p>'),
                                             'advice_observations': RichTextValue(u'<p>My observation finance</p>')})
        # when created, a finance advice is automatically set to 'proposed_to_financial_controller'
        self.assertTrue(advice.queryState() == 'proposed_to_financial_controller')
        # when a financial advice is added, advice_hide_during_redaction
        # is True, no matter MeetingConfig.defaultAdviceHiddenDuringRedaction
        # it is automatically set to False when advice will be "signed" (aka "published")
        self.assertTrue(advice.advice_hide_during_redaction)
        self.assertTrue(self.hasPermission(View, advice))
        self.assertTrue(self.hasPermission(ModifyPortalContent, advice))

        # the item can be sent back to the internal reviewer, in this case, advice delay
        # is stopped, and when item is sent back to the finance, advice delay does not
        # start immediatelly because item completeness is automatically set to 'evaluate again'
        # for now delay is started and advice is editable
        self.do(item, 'backToProposedToInternalReviewer')
        # advice delay is no more started and advice is no more editable
        self.assertTrue(not item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_addable'])
        self.assertTrue(not item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_editable'])
        self.assertTrue(not item.adviceIndex[FINANCE_GROUP_IDS[0]]['delay_started_on'])
        # completeness did not changed
        self.assertTrue(item.getCompleteness() == 'completeness_evaluation_not_required')
        # if item is sent back to the finance, it will not be enabled as
        # completeness was set automatically to 'completeness_evaluation_asked_again'
        self.changeUser('pmManager')
        self.do(item, 'proposeToDirector')
        self.do(item, 'proposeToFinance')
        self.changeUser('pmFinController')
        # delay did not start
        self.assertTrue(not item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_addable'])
        self.assertTrue(not item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_editable'])
        self.assertTrue(not item.adviceIndex[FINANCE_GROUP_IDS[0]]['delay_started_on'])
        # completeness was set automatically to evaluation asked again
        self.assertTrue(item.getCompleteness() == 'completeness_evaluation_asked_again')
        # if pmFinController set completeness to complete, advice can be added
        self.request.set('new_completeness_value', 'completeness_complete')
        changeCompleteness()
        self.assertTrue(item.getCompleteness() == 'completeness_complete')
        self.assertTrue(not item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_addable'])
        self.assertTrue(item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_editable'])
        self.assertTrue(item.adviceIndex[FINANCE_GROUP_IDS[0]]['delay_started_on'])

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
        # when an advice is signed, it is automatically versioned
        pr = self.portal.portal_repository
        retrievedAdvice = pr.getHistoryMetadata(advice).retrieve(0)
        self.assertTrue(retrievedAdvice['metadata']['sys_metadata']['comment'] == FINANCE_ADVICE_HISTORIZE_COMMENTS)
        # as there is a finance advice on the item, finance keep read access to the item
        self.assertTrue(self.hasPermission(View, item))
        # now an item with a negative financial advice back to the director
        # as no emergency is asked, the item can not be validated
        self.changeUser('pmReviewer1')
        self.assertTrue(self.transitions(item) == ['backToProposedToInternalReviewer',
                                                   'proposeToFinance'])
        # a financial advice can not be 'asked_again'
        self.assertFalse(item.adapted().mayAskAdviceAgain(advice))
        # a director can send the item back to director or internal reviewer even
        # when advice is on the way by finance.  So send it again to finance and take it back
        self.do(item, 'proposeToFinance')
        # completeness was 'completeness_evaluation_asked_again'
        self.assertEquals(item.getCompleteness(), 'completeness_evaluation_asked_again')
        self.assertTrue(item.queryState() == 'proposed_to_finance')
        self.assertTrue(self.transitions(item) == ['backToProposedToDirector',
                                                   'backToProposedToInternalReviewer'])
        # a reviewer can send the item back to the director
        self.do(item, 'backToProposedToDirector')
        # ok now the director can send it again to the finance
        # and finance can adapt the advice
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
        # each time an advice is signed, it is historized in the advice history
        retrievedAdvice = pr.getHistoryMetadata(advice).retrieve(1)
        self.assertTrue(retrievedAdvice['metadata']['sys_metadata']['comment'] == FINANCE_ADVICE_HISTORIZE_COMMENTS)

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
        self.freezeMeeting(meeting)
        self.assertTrue(meeting.queryState() == 'frozen')
        self.assertTrue(item.queryState() == 'itemfrozen')
        self.assertTrue(advice.queryState() == 'advice_given')

        # item could go back to 'presented', in this case, advice is editable again
        self.do(item, 'backToPresented')
        self.assertTrue(item.queryState() == 'presented')
        self.assertTrue(advice.queryState() == 'proposed_to_financial_controller')

        # a finance adviser is able to add decision annexes to the item when it is decided
        self.changeUser('pmFinController')
        adviserGroupId = '%s_advisers' % FINANCE_GROUP_IDS[0]
        self.assertEquals(item.__ac_local_roles__[adviserGroupId], ['Reader', ])
        self.assertEquals(item.queryState(), 'presented')
        self.assertRaises(Unauthorized, self.addAnnex, item, relatedTo='item_decision')
        self.changeUser('pmManager')
        self.decideMeeting(meeting)
        self.do(item, 'accept')
        self.assertTrue(item.queryState() == 'accepted')
        self.changeUser('pmFinController')
        self.assertEquals(item.__ac_local_roles__[adviserGroupId], ['Reader', 'MeetingFinanceEditor'])
        self.changeUser('pmFinController')
        self.assertFalse(IAnnexable(item).getAnnexes('item_decision'))
        # finance user is able to add a decision annex
        self.addAnnex(item, relatedTo='item_decision')
        self.assertTrue(IAnnexable(item).getAnnexes('item_decision'))
        # if we go back to itemfrozen, 'MeetingFinanceEditor' is removed
        self.changeUser('pmManager')
        self.do(item, 'backToItemFrozen')
        self.assertTrue(item.queryState() == 'itemfrozen')
        self.assertEquals(item.__ac_local_roles__[adviserGroupId], ['Reader', ])

    def test_subproduct_CollegeProcessWithFinancesAdvicesWithEmergency(self):
        '''If emergency is asked for an item by director, the item can be sent
           to the meeting (validated) without finance advice, finance advice is still giveable...
           Make sure a MeetingManager is able to present such an item or send back to the director.'''
        self.changeUser('admin')
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # add finance groups
        _createFinanceGroups(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # remove pmManager from 'developers' so he will not have the 'MeetingReviewer' role
        # managed by the meetingadviceliege_workflow and giving access to 'Access contents information'
        for group in self.portal.portal_membership.getMemberById('pmManager').getGroups():
            if group.startswith('developers_'):
                self.portal.portal_groups.removePrincipalFromGroup('pmManager', group)

        self.changeUser('pmCreator1')
        # create an item and ask finance advice
        item = self.create('MeetingItem')
        item.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        # no emergency for now
        item.setEmergency('no_emergency')
        item.at_post_edit_script()
        # finance advice is asked
        self.assertTrue(item.adapted().getFinanceGroupIdsForItem() == FINANCE_GROUP_IDS[0])
        self.assertTrue(FINANCE_GROUP_IDS[0] in item.adviceIndex)
        # propose the item to the director, he will send item to finance
        self.proposeItem(item)
        self.changeUser('pmReviewer1')
        self.do(item, 'proposeToFinance')
        # finance will add advice and send item back to the internal reviewer
        self.changeUser('pmFinController')
        changeCompleteness = item.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()
        # give the advice
        advice = createContentInContainer(item,
                                          'meetingadvice',
                                          **{'advice_group': FINANCE_GROUP_IDS[0],
                                             'advice_type': u'positive_finance',
                                             'advice_comment': RichTextValue(u'<p>My comment finance</p>'),
                                             'advice_observations': RichTextValue(u'<p>My observation finance</p>')})
        self.do(item, 'backToProposedToInternalReviewer')
        # internal reviewer will send item to the director that will ask emergency
        self.changeUser('pmInternalReviewer1')
        self.do(item, 'proposeToDirector')
        self.changeUser('pmReviewer1')
        # no emergency for now so item can not be validated
        self.assertTrue(not 'validate' in self.transitions(item))
        # ask emergency
        self.assertTrue(item.adapted().mayAskEmergency())
        item.setEmergency('emergency_asked')
        # now item can be validated
        self.assertTrue('validate' in self.transitions(item))
        self.do(item, 'validate')
        # item has been validated and is viewable by the MeetingManagers
        self.changeUser('pmManager')
        # for now, advice is still proposed to the financial controller
        self.assertTrue(advice.queryState() == 'proposed_to_financial_controller')
        # item can be sent back to the director, this will test that advice state
        # can be changed even if advice is not viewable
        self.do(item, 'backToProposedToDirector')
        self.assertTrue(advice.queryState() == 'advice_given')
        # director validate item again
        self.changeUser('pmReviewer1')
        self.do(item, 'validate')
        # create a meeting and make sure it can be frozen, aka it will
        # change not viewable advice state to 'advice_given'
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date='2014/01/01 09:00:00')
        self.do(item, 'present')
        # advice state is still 'proposed_to_financial_controller'
        self.assertTrue(advice.queryState() == 'proposed_to_financial_controller')
        # if the meeting is frozen, every items are frozen as well
        # and finance advices are no more giveable, so advice will go to 'advice_given'
        self.do(meeting, 'freeze')
        self.assertTrue(advice.queryState() == 'advice_given')

    def test_subproduct_ItemWithTimedOutAdviceIsAutomaticallyValidated(self):
        '''When an item is 'proposed_to_finance', it may be validated
           only by finance group or if emergency is asked.  In case the asked
           advice is timed out, it will be automatically validated.'''
        self.changeUser('admin')
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # add finance groups
        _createFinanceGroups(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # send item to finance
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='The first item')
        item.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        item.at_post_edit_script()
        self.proposeItem(item)
        self.do(item, 'proposeToFinance')
        # item is now 'proposed_to_finance'
        self.assertTrue(item.queryState() == 'proposed_to_finance')
        # item can not be validated
        self.assertTrue(not 'validate' in self.transitions(item))

        # now add advice
        self.changeUser('pmFinController')
        # give the advice
        item.setCompleteness('completeness_complete')
        item.at_post_edit_script()
        advice = createContentInContainer(item,
                                          'meetingadvice',
                                          **{'advice_group': FINANCE_GROUP_IDS[0],
                                             'advice_type': u'positive_finance',
                                             'advice_comment': RichTextValue(u'My comment finance')})
        # sign advice, necessary to test updateAdvices called in updateAdvices...
        self.do(advice, 'proposeToFinancialReviewer')
        self.changeUser('pmFinReviewer')
        self.do(advice, 'proposeToFinancialManager')
        self.changeUser('pmFinManager')
        self.do(advice, 'signFinancialAdvice')
        self.assertTrue(advice.queryState() == 'financial_advice_signed')
        # can not be validated
        self.changeUser('pmManager')
        self.assertTrue(not 'validate' in self.transitions(item))
        # now does advice timed out
        item.adviceIndex[FINANCE_GROUP_IDS[0]]['delay_started_on'] = datetime(2014, 1, 1)
        item.updateAdvices()
        # advice is timed out
        self.assertTrue(item.adviceIndex[FINANCE_GROUP_IDS[0]]['delay_infos']['delay_status'] == 'timed_out')
        # item has been automatically validated
        self.assertTrue(item.queryState() == 'validated')
        # if item is sent back to director, the director is able to validate it as well as MeetingManagers
        self.do(item, 'backToProposedToDirector')
        self.changeUser('pmReviewer1')
        self.assertTrue('validate' in self.transitions(item))
        self.changeUser('pmManager')
        self.assertTrue('validate' in self.transitions(item))

        # now test that a 'timed_out' advice can be set back to editable
        # by finance advice from no more editable, for this, go to 'itemfrozen'
        # this test a corrected bug where 'delay_infos' key was no more present
        # in the adviceIndex because updateAdvices is called during updateAdvices
        self.do(item, 'validate')
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date='2015/05/05')
        self.presentItem(item)
        self.assertTrue(advice.queryState() == 'advice_given')
        self.assertFalse(item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_editable'])
        self.assertTrue(item.adviceIndex[FINANCE_GROUP_IDS[0]]['delay_infos']['delay_status'] == 'timed_out')
        self.freezeMeeting(meeting)
        self.assertTrue(advice.queryState() == 'advice_given')
        self.assertFalse(item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_editable'])
        self.assertTrue(item.adviceIndex[FINANCE_GROUP_IDS[0]]['delay_infos']['delay_status'] == 'no_more_giveable')
        self.assertTrue(item.queryState() == 'itemfrozen')
        # now back to 'presented'
        self.do(item, 'backToPresented')
        self.assertTrue(item.queryState() == 'presented')
        # advice is back to 'presented' but as 'timed_out', no more editable
        self.assertEquals(advice.queryState(), 'advice_given')
        self.assertFalse(item.adviceIndex[FINANCE_GROUP_IDS[0]]['advice_editable'])
        self.assertTrue(item.adviceIndex[FINANCE_GROUP_IDS[0]]['delay_infos']['delay_status'] == 'timed_out')

    def test_subproduct_ReturnCollege(self):
        '''Test behaviour of the 'return' decision transition.
           This will duplicate the item and the new item will be automatically
           validated so it is available for the next meetings.'''
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='An item to return')
        meeting = self.create('Meeting', date='2014/01/01 09:00:00')
        # present the item into the meeting
        self.presentItem(item)
        self.decideMeeting(meeting)
        # now the item can be 'returned'
        self.assertTrue('return' in self.transitions(item))
        # no duplicated for now
        self.assertTrue(not item.getBRefs('ItemPredecessor'))
        self.do(item, 'return')
        self.assertTrue(item.queryState() == 'returned')
        # now that the item is 'returned', it has been duplicated
        # and the new item has been validated
        predecessor = item.getBRefs('ItemPredecessor')
        self.assertTrue(len(predecessor) == 1)
        predecessor = predecessor[0]
        self.assertTrue(predecessor.queryState() == 'validated')
        self.assertTrue(predecessor.portal_type == item.portal_type)

    def test_subproduct_AcceptAndReturnCollege(self):
        '''Test behaviour of the 'accept_and_return' decision transition.
           This will send the item to the council then duplicate the original item (college)
           and automatically validate it so it is available for the next meetings.'''
        cfg2Id = self.meetingConfig2.getId()
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='An item to return')
        meeting = self.create('Meeting', date='2014/01/01 09:00:00')
        # present the item into the meeting
        self.presentItem(item)
        self.decideMeeting(meeting)
        # as item is not to send to council, the 'accept_and_return' transition is not available
        self.assertTrue(not 'accept_and_return' in self.transitions(item))
        # make it to send to council
        item.setOtherMeetingConfigsClonableTo((cfg2Id, ))
        # now the transition 'accept_and_return' is available
        self.assertTrue('accept_and_return' in self.transitions(item))
        # accept_and_return, the item is send to the meetingConfig2
        # and is duplicated in current config and set to 'validated'
        self.do(item, 'accept_and_return')
        predecessors = item.getBRefs('ItemPredecessor')
        self.assertTrue(len(predecessors) == 2)
        duplicated1, duplicated2 = predecessors
        # predecessors are not sorted, so one of both is duplicated to another
        # meetingConfig and the other is duplicated locally...
        # sent to the council
        if duplicated1.portal_type == self.meetingConfig2.getItemTypeName():
            duplicatedToCfg2 = duplicated1
            duplicatedLocally = duplicated2
        else:
            duplicatedToCfg2 = duplicated2
            duplicatedLocally = duplicated1
        self.assertTrue(duplicatedToCfg2.portal_type == self.meetingConfig2.getItemTypeName())
        self.assertTrue(duplicatedToCfg2.UID() == item.getItemClonedToOtherMC(cfg2Id).UID())
        # duplicated locally...
        self.assertTrue(duplicatedLocally.portal_type == item.portal_type)
        #... and validated
        self.assertTrue(duplicatedLocally.queryState() == 'validated')
        # informations about "needs to be sent to other mc" is kept
        self.assertTrue(duplicatedLocally.getOtherMeetingConfigsClonableTo() == (self.meetingConfig2.getId(), ))
        # now if duplicated item is accepted again, it will not be sent again the council
        meeting2 = self.create('Meeting', date='2014/02/02 09:00:00')
        # present the item into the meeting
        self.presentItem(duplicatedLocally)
        self.decideMeeting(meeting2)
        # it already being considered as sent to the other mc
        self.assertTrue(duplicatedLocally._checkAlreadyClonedToOtherMC(self.meetingConfig2.getId()))
        # it will not be considered as sent to the other mc if item
        # that was sent in the council is 'delayed' or 'marked_not_applicable'
        # so insert duplicatedToCfg2 in a meeting and 'delay' it
        councilMeeting = self.create('Meeting', date='2015/01/15 09:00:00', meetingConfig=self.meetingConfig2)
        # meetingConfig2 is using categories
        duplicatedToCfg2.setCategory('deployment')
        self.presentItem(duplicatedToCfg2)
        self.decideMeeting(councilMeeting)
        self.do(duplicatedToCfg2, 'delay')
        # now that item duplicated to council is delayed, item in college is no more
        # considered as being send, deciding it will send it again to the council
        self.assertFalse(duplicatedLocally._checkAlreadyClonedToOtherMC(cfg2Id))
        # accept and return it again, it will be sent again to the council
        self.do(duplicatedLocally, 'accept_and_return')
        self.assertTrue(duplicatedLocally.getItemClonedToOtherMC(cfg2Id))

        # now, make sure an already duplicated item
        # with an item on the council that is not 'delayed' or 'marked_not_applicable' is
        # not sent again
        predecessors = duplicatedLocally.getBRefs('ItemPredecessor')
        newduplicated1, newduplicated2 = predecessors
        if newduplicated1.portal_type == self.meetingConfig2.getItemTypeName():
            newDuplicatedLocally = newduplicated2
        else:
            newDuplicatedLocally = newduplicated1
        self.assertTrue(newDuplicatedLocally.portal_type == self.meetingConfig.getItemTypeName())
        meeting3 = self.create('Meeting', date='2014/02/02 09:00:00')
        self.presentItem(newDuplicatedLocally)
        self.decideMeeting(meeting3)
        # it is considered sent, so accepting it will not send it again
        self.assertTrue(newDuplicatedLocally._checkAlreadyClonedToOtherMC(cfg2Id))
        self.do(newDuplicatedLocally, 'accept')
        # it has not be sent again
        self.assertFalse(newDuplicatedLocally.getItemClonedToOtherMC(cfg2Id))

        # make sure an item that is 'Duplicated and keep link' with an item
        # that was 'accepted_and_returned' is sendable to another mc
        self.assertEquals(duplicatedLocally.queryState(), 'accepted_and_returned')
        dupLinkedItemURL = duplicatedLocally.onDuplicateAndKeepLink()
        dupLinkedItem = duplicatedLocally.getParentNode().restrictedTraverse(dupLinkedItemURL.split('/')[-1])
        self.assertEquals(dupLinkedItem.getPredecessor(), duplicatedLocally)
        self.assertTrue(getLastEvent(dupLinkedItem, 'Duplicate and keep link'))
        self.assertEquals(dupLinkedItem.getOtherMeetingConfigsClonableTo(),
                          (cfg2Id,))
        meeting4 = self.create('Meeting', date='2014/03/03 09:00:00')
        self.presentItem(dupLinkedItem)
        self.decideMeeting(meeting4)
        # once accepted, it has been sent to the council
        self.do(dupLinkedItem, 'accept')
        self.assertTrue(dupLinkedItem.getItemClonedToOtherMC(cfg2Id))

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

        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='The first item')
        # ask finance advice
        item.setFinanceAdvice(FINANCE_GROUP_IDS[0])
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

    def test_subproduct_ItemCommentViewability(self):
        '''Test that even when comments are only shown to the proposing group,
           some specific comments are shown to the group the financial advice is asked to.'''
        self.changeUser('admin')
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # add finance groups
        _createFinanceGroups(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()
        # enable comments hidden to members outside proposing group
        self.meetingConfig.setHideItemHistoryCommentsToUsersOutsideProposingGroup(True)

        # add an item and do what necessary for different cases to appear in it's workflow_history
        # create it, send it to director :
        # - send it back to internal review : from the director, the comment should not be visible to finances;
        # - send it from director to finances : comment should be visible;
        # - send it from finances to internal reviewer : comment should be visible.
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='The first item')
        item.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        item.at_post_edit_script()
        self.proposeItem(item)
        # now director send the item back to the internal reviewer
        # it will use transition 'backToProposedToInternalReviewer' but will
        # not be visible by the finances group
        self.do(item, 'backToProposedToInternalReviewer')
        self.proposeItem(item)
        # send item to finance
        self.do(item, 'proposeToFinance', comment='Proposed to finances by director')
        # save event index (position in the history) we will have to check access to
        history = item.getHistory()
        proposedToFinancesViewableIndex = history.index(history[-1])
        # now finance send it back to the internal reviewer
        self.do(item, 'backToProposedToInternalReviewer')
        # save event
        history = item.getHistory()
        proposedToInternalReviewerViewableIndex = history.index(history[-1])

        # ok now, check, the only viewable events for finance grou members
        # should be proposedToFinancesViewableIndex and proposedToInternalReviewerViewableIndex
        viewableCommentIndexes = (proposedToFinancesViewableIndex, proposedToInternalReviewerViewableIndex)
        self.changeUser('pmFinController')
        history = item.getHistory()
        for event in history:
            if history.index(event) in viewableCommentIndexes:
                # comment is viewable
                self.assertTrue(not event['comments'] == HISTORY_COMMENT_NOT_VIEWABLE)
            else:
                self.assertTrue(event['comments'] == HISTORY_COMMENT_NOT_VIEWABLE)

    def test_subproduct_AdviceCommentViewability(self):
        '''Test that advice comments are only viewable to finance group members and MeetingManagers.
           Except the FINANCE_ADVICE_HISTORIZE_EVENT that is viewable by everyone who may access the advice.'''
        self.changeUser('admin')
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # add finance groups
        _createFinanceGroups(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # create an item and ask finance advice
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='The first item')
        item.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        item.at_post_edit_script()
        self.proposeItem(item)
        self.do(item, 'proposeToFinance')
        # make item completeness complete and add advice
        self.changeUser('pmFinController')
        changeCompleteness = item.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()
        advice = createContentInContainer(item,
                                          'meetingadvice',
                                          **{'advice_group': FINANCE_GROUP_IDS[0],
                                             'advice_type': u'positive_finance',
                                             'advice_comment': RichTextValue(u'<p>My comment finance</p>'),
                                             'advice_observations': RichTextValue(u'<p>My observation finance</p>')})
        self.do(advice, 'proposeToFinancialReviewer', comment='My financial controller comment')
        # as finance reviewer
        self.changeUser('pmFinReviewer')
        self.do(advice, 'proposeToFinancialManager', comment='My financial reviewer comment')
        # as finance manager
        self.changeUser('pmFinManager')
        self.do(advice, 'signFinancialAdvice', comment='My financial manager comment')
        # now check history comment viewability
        # viewable to pmFinManager and other members of the finance group
        history = advice.getHistory()
        for event in history:
            self.assertTrue(not event['comments'] == HISTORY_COMMENT_NOT_VIEWABLE)
        # not viewable to the pmManager as only Managers may access those comments
        self.changeUser('pmManager')
        history = advice.getHistory()
        for event in history:
            self.assertTrue(event['comments'] == HISTORY_COMMENT_NOT_VIEWABLE)
        # user able to see the advice have same access as a MeetingManager, so only
        # access to the HISTORY_COMMENT_NOT_VIEWABLE
        self.changeUser('pmCreator1')
        # user may not see advice history comments like a MeetingManager
        self.hasPermission(View, advice)
        history = advice.getHistory()
        for event in history:
            self.assertTrue(event['comments'] == HISTORY_COMMENT_NOT_VIEWABLE)

    def test_subproduct_MeetingManagersMayNotDeleteItems(self):
        '''
          MeetingManagers are not able to Delete an item.
        '''
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        self.validateItem(item)
        self.changeUser('pmManager')
        self.assertFalse(self.hasPermission(DeleteObjects, item))
        meeting = self.create('Meeting', date='2015/01/01')
        self.presentItem(item)
        self.assertTrue(item.queryState() == 'presented')
        self.assertFalse(self.hasPermission(DeleteObjects, item))
        self.freezeMeeting(meeting)
        self.assertTrue(item.queryState() == 'itemfrozen')
        self.assertFalse(self.hasPermission(DeleteObjects, item))
        self.decideMeeting(meeting)
        self.assertTrue(item.queryState() == 'itemfrozen')
        self.assertFalse(self.hasPermission(DeleteObjects, item))
        self.closeMeeting(meeting)
        self.assertTrue(item.queryState() == 'accepted')
        self.assertFalse(self.hasPermission(DeleteObjects, item))

    def test_subproduct_FinanceAdvisersAccessToLinkedItems(self):
        """Finance adviser have still access to items linked to
           an item they give advice on.
           This is the case for 'returned' items and items sent to Council."""
        self.changeUser('admin')
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # add finance groups
        _createFinanceGroups(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # first 'return' an item and test
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='An item to return')
        meeting = self.create('Meeting', date='2014/01/01 09:00:00')
        # ask finance advice and give it
        item.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        item.at_post_edit_script()
        self.proposeItem(item)
        self.do(item, 'proposeToFinance')
        # make item completeness complete and add advice
        self.changeUser('pmFinController')
        changeCompleteness = item.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()
        advice = createContentInContainer(item,
                                          'meetingadvice',
                                          **{'advice_group': FINANCE_GROUP_IDS[0],
                                             'advice_type': u'positive_finance',
                                             'advice_comment': RichTextValue(u'<p>My comment finance</p>'),
                                             'advice_observations': RichTextValue(u'<p>My observation finance</p>')})
        self.do(advice, 'proposeToFinancialReviewer', comment='My financial controller comment')
        # as finance reviewer
        self.changeUser('pmFinReviewer')
        self.do(advice, 'proposeToFinancialManager', comment='My financial reviewer comment')
        # as finance manager
        self.changeUser('pmFinManager')
        self.do(advice, 'signFinancialAdvice', comment='My financial manager comment')

        # present the item into the meeting
        self.changeUser('pmManager')
        self.presentItem(item)
        self.decideMeeting(meeting)
        self.do(item, 'return')
        self.assertTrue(item.queryState() == 'returned')
        # now that the item is 'returned', it has been duplicated
        # and the finance advisers have access to the newItem
        newItem = item.getBRefs('ItemPredecessor')[0]
        self.assertTrue(newItem.__ac_local_roles__['{0}_advisers'.format(FINANCE_GROUP_IDS[0])] == ['Reader', ])
        # right, remove newItem and 'accept_and_return' item
        self.do(item, 'backToItemFrozen')
        self.changeUser('admin')
        newItem.getParentNode().manage_delObjects(ids=[newItem.getId(), ])
        self.changeUser('pmManager')
        item.setOtherMeetingConfigsClonableTo((self.meetingConfig2.getId(), ))
        self.do(item, 'accept_and_return')
        self.assertEquals(item.queryState(), 'accepted_and_returned')
        predecessors = item.getBRefs('ItemPredecessor')
        self.assertEquals(len(predecessors), 2)
        self.assertTrue(predecessors[0].__ac_local_roles__['{0}_advisers'.format(FINANCE_GROUP_IDS[0])] == ['Reader', ])
        self.assertTrue(predecessors[1].__ac_local_roles__['{0}_advisers'.format(FINANCE_GROUP_IDS[0])] == ['Reader', ])

        # now, corner case
        # first item with given finance advice is 'returned' in a meeting
        # new item is accepted and returned in a second meeting
        # item sent to council should keep advisers access
        self.changeUser('admin')
        predecessors[0].getParentNode().manage_delObjects(ids=[predecessors[0].getId(), ])
        predecessors[1].getParentNode().manage_delObjects(ids=[predecessors[1].getId(), ])
        self.changeUser('pmManager')
        self.do(item, 'backToItemFrozen')
        self.do(item, 'return')
        self.assertTrue(item.queryState() == 'returned')
        newItem = item.getBRefs('ItemPredecessor')[0]
        self.assertEquals(newItem.adapted().getItemWithFinanceAdvice(), item)
        # right accept_and_return newItem
        meeting2 = self.create('Meeting', date='2015/01/01 09:00:00')
        self.presentItem(newItem)
        self.decideMeeting(meeting2)
        self.do(newItem, 'accept_and_return')
        self.assertEquals(newItem.queryState(), 'accepted_and_returned')
        predecessors = newItem.getBRefs('ItemPredecessor')
        self.assertEquals(len(predecessors), 2)
        self.assertTrue(predecessors[0].__ac_local_roles__['{0}_advisers'.format(FINANCE_GROUP_IDS[0])] == ['Reader', ])
        self.assertTrue(predecessors[1].__ac_local_roles__['{0}_advisers'.format(FINANCE_GROUP_IDS[0])] == ['Reader', ])

    def test_subproduct_CollegeShortcutProcess(self):
        '''
        The items cannot be send anymore to group without at least one user
        in it. There is also shortcut for the three types of reviewers who
        don't have to do the whole validation process but can send
        directly to the role above.
        '''
        cfg = self.meetingConfig
        cfg.setUseGroupsAsCategories(False)
        pg = self.portal.portal_groups
        darGroup = pg.getGroupById('developers_administrativereviewers')
        darMembers = darGroup.getMemberIds()
        dirGroup = pg.getGroupById('developers_internalreviewers')
        dirMembers = dirGroup.getMemberIds()
        # Give the creator role to all reviewers as they will have to create items.
        self.changeUser('admin')
        dcGroup = pg.getGroupById('developers_creators')
        dcGroup.addMember('pmAdminReviewer1')
        dcGroup.addMember('pmInternalReviewer1')
        dcGroup.addMember('pmReviewer1')

        # pmCreator1 creates an item
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem', title='The first item')
        # pmCreator may only 'proposeToAdministrativeReviewer'
        self.assertTrue(self.transitions(item) == ['proposeToAdministrativeReviewer', ])
        self._checkItemWithoutCategory(item, item.getCategory())
        # if there is no administrative reviewer, a creator can send the item
        # directly to internal reviewer.
        self._removeAllMembers(darGroup, darMembers)
        self.assertTrue(self.transitions(item) == ['proposeToInternalReviewer', ])
        self._checkItemWithoutCategory(item, item.getCategory())
        # if there is neither administrative nor internal reviewer, a creator
        # can send the item directly to director.
        self._removeAllMembers(dirGroup, dirMembers)
        self.assertTrue(self.transitions(item) == ['proposeToDirector', ])
        self._checkItemWithoutCategory(item, item.getCategory())
        # if there is an administrative reviewer but no internal reviewer, the
        # creator may only send the item to administative reviewer.
        self._addAllMembers(darGroup, darMembers)
        self.assertTrue(self.transitions(item) == ['proposeToAdministrativeReviewer', ])
        self._checkItemWithoutCategory(item, item.getCategory())
        self._addAllMembers(dirGroup, dirMembers)

        # A creator can ask for advices if an advice is required.
        item.setOptionalAdvisers(('vendors', ))
        item.at_post_edit_script()
        self.assertTrue(self.transitions(item) == ['askAdvicesByItemCreator',
                                                   'proposeToAdministrativeReviewer', ])
        self._checkItemWithoutCategory(item, item.getCategory())
        self.do(item, 'askAdvicesByItemCreator')
        # The user is not forced to give a normal advice and can propose to
        # administrative reviewer.
        self.assertTrue(self.transitions(item) == ['backToItemCreated',
                                                   'proposeToAdministrativeReviewer', ])
        # If there is no administrative reviewer, the user can send the item to
        # internal reviewer.
        self._removeAllMembers(darGroup, darMembers)
        self.assertTrue(self.transitions(item) == ['backToItemCreated',
                                                   'proposeToInternalReviewer', ])
        # If there are neither administrative nor internal reviewer, allow to
        # send directly to direction.
        self._removeAllMembers(dirGroup, dirMembers)
        self.assertTrue(self.transitions(item) == ['backToItemCreated',
                                                   'proposeToDirector', ])
        self._addAllMembers(darGroup, darMembers)
        self._addAllMembers(dirGroup, dirMembers)
        self.do(item, 'backToItemCreated')
        # Remove the advice for the tests below.
        item.setOptionalAdvisers(())
        item.at_post_edit_script()

        # an administrative reviewer can send an item in creation directly to
        # the internal reviewer.
        self.changeUser('pmAdminReviewer1')
        self.assertTrue(self.transitions(item) == ['proposeToInternalReviewer', ])
        self._checkItemWithoutCategory(item, item.getCategory())
        # if there is no internal reviewer, an administrative reviewer can only
        # send the item to director.
        self._removeAllMembers(dirGroup, dirMembers)
        self.assertTrue(self.transitions(item) == ['proposeToDirector', ])
        self._checkItemWithoutCategory(item, item.getCategory())
        self._addAllMembers(dirGroup, dirMembers)
        # an item which is proposed to administrative reviewer can be send to
        # internal reviewer by an administrative reviewer.
        self.changeUser('pmCreator1')
        self.do(item, 'proposeToAdministrativeReviewer')
        self.changeUser('pmAdminReviewer1')
        self.assertTrue(self.transitions(item) == ['backToItemCreated',
                                                   'proposeToInternalReviewer', ])
        # if there is no internal reviewer, an administrative reviewer can only
        # send the item to director.
        self._removeAllMembers(dirGroup, dirMembers)
        self.assertTrue(self.transitions(item) == ['backToItemCreated',
                                                   'proposeToDirector', ])
        self._addAllMembers(dirGroup, dirMembers)
        self.do(item, 'backToItemCreated')

        # An administrative reviewer can ask for advices if an advice is required.
        item.setOptionalAdvisers(('vendors', ))
        item.at_post_edit_script()
        self.assertTrue(self.transitions(item) == ['askAdvicesByItemCreator',
                                                   'proposeToInternalReviewer', ])
        self._checkItemWithoutCategory(item, item.getCategory())
        self.do(item, 'askAdvicesByItemCreator')
        # The user is not forced to wait for a normal advice and can propose to
        # internal reviewer.
        self.assertTrue(self.transitions(item) == ['backToItemCreated',
                                                   'proposeToInternalReviewer', ])
        # If there is no internal reviewer, the user can send the item to
        # director.
        self._removeAllMembers(dirGroup, dirMembers)
        self.assertTrue(self.transitions(item) == ['backToItemCreated',
                                                   'proposeToDirector', ])
        self._addAllMembers(dirGroup, dirMembers)
        self.do(item, 'backToItemCreated')
        # Remove the advice for the tests below.
        item.setOptionalAdvisers(())
        item.at_post_edit_script()

        # an internal reviewer can propose an item in creation directly
        # to the direction.
        self.changeUser('pmInternalReviewer1')
        self.assertTrue(self.transitions(item) == ['proposeToDirector', ])
        self._checkItemWithoutCategory(item, item.getCategory())

        # An internal reviewer can ask for advices if an advice is required.
        item.setOptionalAdvisers(('vendors', ))
        item.at_post_edit_script()
        self.assertTrue(self.transitions(item) == ['askAdvicesByItemCreator',
                                                   'proposeToDirector', ])
        self._checkItemWithoutCategory(item, item.getCategory())
        self.do(item, 'askAdvicesByItemCreator')
        # The user is not forced to wait for a normal advice and can propose to
        # director.
        self.assertTrue(self.transitions(item) == ['backToItemCreated',
                                                   'proposeToDirector', ])
        self.do(item, 'backToItemCreated')
        # Remove the advice for the tests below.
        item.setOptionalAdvisers(())
        item.at_post_edit_script()

        # a director has the same prerogative of an internal reviewer.
        self.changeUser('pmReviewer1')
        self.assertTrue(self.transitions(item) == ['proposeToDirector', ])
        self._checkItemWithoutCategory(item, item.getCategory())

        # A reviewer can ask for advices if an advice is required.
        item.setOptionalAdvisers(('vendors', ))
        item.at_post_edit_script()
        self.assertTrue(self.transitions(item) == ['askAdvicesByItemCreator',
                                                   'proposeToDirector', ])
        self._checkItemWithoutCategory(item, item.getCategory())
        self.do(item, 'askAdvicesByItemCreator')
        # The user is not forced to wait for a normal advice and can propose to
        # director.
        self.assertTrue(self.transitions(item) == ['backToItemCreated',
                                                   'proposeToDirector', ])
        self.do(item, 'backToItemCreated')
        # Remove the advice for the tests below.
        item.setOptionalAdvisers(())
        item.at_post_edit_script()

        # A director can validate or send the item back to the first state with
        # user in it. As there is an internal reviewer, the item can be sent
        # back to him.
        self.do(item, 'proposeToDirector')
        self.assertTrue(self.transitions(item) == ['backToProposedToInternalReviewer',
                                                   'validate', ])
        # If there is no internal reviewer, allow to send the item back to
        # administrative reviewer.
        self._removeAllMembers(dirGroup, dirMembers)
        self.assertTrue(self.transitions(item) == ['backToProposedToAdministrativeReviewer',
                                                   'validate', ])
        # If there is neither internal nor administrative reviewer, allow to
        # send the item back to creation.
        self._removeAllMembers(darGroup, darMembers)
        self.assertTrue(self.transitions(item) == ['backToItemCreated',
                                                   'validate', ])
        self._addAllMembers(darGroup, darMembers)
        self._addAllMembers(dirGroup, dirMembers)
        # Send the item back to internal reviewer.
        self.do(item, 'backToProposedToInternalReviewer')
        # Internal reviewer is able to propose to director, send the item back
        # to creator or to administrative reviewer.
        self.changeUser('pmInternalReviewer1')
        self.assertTrue(self.transitions(item) == ['backToProposedToAdministrativeReviewer',
                                                   'proposeToDirector', ])
        # If there is no administrative reviewer, allow the item to be sent
        # back to creation.
        self._removeAllMembers(darGroup, darMembers)
        self.assertTrue(self.transitions(item) == ['backToItemCreated',
                                                   'proposeToDirector', ])

    def _checkItemWithoutCategory(self, item, originalCategory):
        '''Make sure that an item without category cannot be sent to anybody.'''
        actions_panel = item.restrictedTraverse('@@actions_panel')
        rendered_actions_panel = actions_panel()
        item.setCategory('')
        item.at_post_edit_script()
        self.assertTrue(not self.transitions(item))
        no_category_rendered_actions_panel = actions_panel()
        self.assertTrue(not no_category_rendered_actions_panel ==
                        rendered_actions_panel)
        item.setCategory(originalCategory)

    def test_subproduct_RestrictedPowerObserversMayNotAccessLateItemsInCouncilUntilDecided(self):
        """Finance adviser have still access to items linked to
           an item they give advice on.
           This is the case for 'returned' items and items sent to Council."""
        # not 'late' items are viewable by restricted power observers
        cfg2 = self.meetingConfig2
        self.setMeetingConfig(cfg2.getId())
        groupId = "%s_%s" % (cfg2.getId(), RESTRICTEDPOWEROBSERVERS_GROUP_SUFFIX)
        self.changeUser('pmManager')
        item = self.create('MeetingItem')
        item2 = self.create('MeetingItem')
        meeting = self.create('Meeting', date=DateTime())
        self.presentItem(item)
        self.freezeMeeting(meeting)
        item2.setPreferredMeeting(meeting.UID())
        item2.at_post_edit_script()
        self.presentItem(item2)
        # item is 'normal' and item2 is 'late'
        self.assertEquals(item.getListType(), 'normal')
        self.assertEquals(item2.getListType(), 'late')
        self.assertEquals(item.queryState(), 'itemfrozen')
        self.assertEquals(item2.queryState(), 'itemfrozen')
        # so item is viewable by 'restricted power observers' but not item2
        self.assertTrue(groupId in item.__ac_local_roles__)
        self.assertFalse(groupId in item2.__ac_local_roles__)
        # change item to 'late', no more viewable
        view = item.restrictedTraverse('@@change-item-listtype')
        view('late')
        self.assertFalse(groupId in item.__ac_local_roles__)

        # decide items, it will be viewable
        self.decideMeeting(meeting)
        self.do(item, 'accept')
        self.do(item2, 'accept')
        self.assertTrue(groupId in item.__ac_local_roles__)
        self.assertTrue(groupId in item2.__ac_local_roles__)

    def test_subproduct_StateSentToCouncilEmergency(self):
        """When 'emergency' is aksed to send an item to Council,
           an item may be set to 'sent_to_council_emergency' so
           it is in a final state and it is sent to council.  It keeps
           a link to a College item and a Council item even if college item
           is not in a meeting."""
        # transition is only available if emergency asked for sending item to council
        # when set to this state, item is sent to Council and is in a final state (no more editable)
        cfg2 = self.meetingConfig2
        cfg2Id = cfg2.getId()
        self.changeUser('pmManager')
        item = self.create('MeetingItem')
        self.validateItem(item)
        item.setOtherMeetingConfigsClonableTo((cfg2Id, ))
        item.at_post_edit_script()
        self.assertNotIn('sendToCouncilEmergency',
                         self.transitions(item))
        # ask emergency for sending to Council
        item.setOtherMeetingConfigsClonableToEmergency((cfg2Id, ))
        item.at_post_edit_script()
        self.assertIn('sendToCouncilEmergency',
                      self.transitions(item))
        # when it is 'sendToCouncilEmergency', it is cloned to the Council
        self.assertIsNone(item.getItemClonedToOtherMC(cfg2Id))
        self.do(item, 'sendToCouncilEmergency')
        self.assertTrue(item.getItemClonedToOtherMC(cfg2Id))
        # no more editable even for a MeetingManager
        self.assertFalse(self.transitions(item))
        self.assertFalse(self.hasPermission(ModifyPortalContent, item))

    def _setupCollegeItemSentToCouncil(self):
        """Send an item from College to Council just before the Council item is decided."""
        self.changeUser('admin')
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # add finance groups
        _createFinanceGroups(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        cfg2 = self.meetingConfig2
        cfg2Id = cfg2.getId()
        cfg2.setUseGroupsAsCategories(True)
        cfg = self.meetingConfig
        cfgId = cfg.getId()
        cfg2.setUseGroupsAsCategories(True)
        cfg2.setInsertingMethodsOnAddItem(({'insertingMethod': 'on_proposing_groups',
                                            'reverse': '0'},))
        cfg2.setMeetingConfigsToCloneTo(({'meeting_config': cfgId,
                                          'trigger_workflow_transitions_until': '__nothing__'},))
        cfg2.setItemAutoSentToOtherMCStates(('delayed', 'returned', ))

        self.changeUser('pmManager')
        # send a college item to council and delay this council item
        # in the college
        collegeMeeting = self.create('Meeting', date=DateTime('2015/11/11'))
        data = {'labelForCouncil': COUNCIL_LABEL,
                'privacyForCouncil': COUNCIL_PRIVACY,
                'otherMeetingConfigsClonableTo': ('meeting-config-council', )}
        collegeItem = self.create('MeetingItem', **data)

        # ask and give finance advice
        collegeItem.setFinanceAdvice(FINANCE_GROUP_IDS[0])
        self.proposeItem(collegeItem)
        self.do(collegeItem, 'proposeToFinance')
        self._giveFinanceAdvice(collegeItem, FINANCE_GROUP_IDS[0])
        self.presentItem(collegeItem)
        self.closeMeeting(collegeMeeting)
        councilItem = collegeItem.getItemClonedToOtherMC(cfg2Id)

        # in the council
        # use groups as categories
        self.setMeetingConfig(cfg2Id)
        councilMeeting = self.create('Meeting', date=DateTime('2015/11/11'))
        self.presentItem(councilItem)
        self.decideMeeting(councilMeeting)
        return collegeItem, councilItem, collegeMeeting, councilMeeting

    def test_subproduct_CouncilItemSentToCollegeWhenDelayed(self):
        """While an item in the council is set to 'delayed', it is sent
           in 'itemcreated' state back to the College and ready to process
           back to the council."""
        cfgId = 'meeting-config-college'
        cfg2Id = 'meeting-config-council'
        collegeItem, councilItem, collegeMeeting, councilMeeting = self._setupCollegeItemSentToCouncil()
        self.do(councilItem, 'delay')
        backCollegeItem = councilItem.getItemClonedToOtherMC(cfgId)
        self.assertEquals(backCollegeItem.getLabelForCouncil(), COUNCIL_LABEL)
        self.assertEquals(backCollegeItem.getPrivacyForCouncil(), COUNCIL_PRIVACY)
        self.assertIn(cfg2Id, backCollegeItem.getOtherMeetingConfigsClonableTo())

        # it is sent back in "itemcreated" state and finance advice does not follow
        self.assertEquals(backCollegeItem.getFinanceAdvice(), FINANCE_GROUP_IDS[0])
        self.assertEquals(backCollegeItem.queryState(), 'itemcreated')
        self.assertEquals(backCollegeItem.adapted().getItemWithFinanceAdvice(), backCollegeItem)

    def test_subproduct_CouncilItemSentToCollegeWhenReturned(self):
        """While an item in the council is set to 'delayed', it is sent
           in 'itemcreated' state back to the College and ready to process
           back to the council."""
        cfgId = 'meeting-config-college'
        cfg2Id = 'meeting-config-council'
        collegeItem, councilItem, collegeMeeting, councilMeeting = self._setupCollegeItemSentToCouncil()
        self.do(councilItem, 'return')
        backCollegeItem = councilItem.getItemClonedToOtherMC(cfgId)
        self.assertEquals(backCollegeItem.getLabelForCouncil(), COUNCIL_LABEL)
        self.assertEquals(backCollegeItem.getPrivacyForCouncil(), COUNCIL_PRIVACY)
        self.assertIn(cfg2Id, backCollegeItem.getOtherMeetingConfigsClonableTo())

        # it is sent back in "validated" state and finance advice does follow
        self.assertEquals(backCollegeItem.getFinanceAdvice(), FINANCE_GROUP_IDS[0])
        self.assertEquals(backCollegeItem.queryState(), 'validated')
        self.assertEquals(backCollegeItem.adapted().getItemWithFinanceAdvice(), collegeItem)

    def test_subproduct_ItemSentToCouncilWhenDuplicatedAndLinkKept(self):
        """Make sure that an item that is 'duplicateAndKeepLink' is sent to Council
           no matter state of linked item."""
        cfg2 = self.meetingConfig2
        cfg2Id = cfg2.getId()
        self.changeUser('pmManager')
        meeting = self.create('Meeting', date=DateTime('2015/11/11'))
        item = self.create('MeetingItem')
        item.setOtherMeetingConfigsClonableTo((cfg2Id, ))
        self.presentItem(item)
        self.decideMeeting(meeting)
        self.do(item, 'accept_and_return')
        # item has been sent
        self.assertTrue(item.getItemClonedToOtherMC(cfg2Id))

        # now check that a duplicatedAndKeepLink item is sent also
        duplicatedItemURL = item.onDuplicateAndKeepLink()
        duplicatedItem = getattr(item.getParentNode(),
                                 duplicatedItemURL.split('/')[-1])
        self.backToState(meeting, 'created')
        self.presentItem(duplicatedItem)
        self.decideMeeting(meeting)
        self.do(duplicatedItem, 'accept')
        self.assertTrue(duplicatedItem.getItemClonedToOtherMC(cfg2Id))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testWorkflows, prefix='test_subproduct_'))
    return suite
