# -*- coding: utf-8 -*-
#
# File: testWorkflows.py
#
# GNU General Public License (GPL)
#

from AccessControl import Unauthorized
from collective.compoundcriterion.interfaces import ICompoundCriterionFilter
from collective.contact.plonegroup.utils import get_plone_group
from collective.contact.plonegroup.utils import get_plone_group_id
from collective.iconifiedcategory.utils import get_categorized_elements
from collective.iconifiedcategory.utils import get_config_root
from collective.iconifiedcategory.utils import get_group
from datetime import datetime
from imio.helpers.cache import cleanRamCacheFor
from imio.helpers.content import richtextval
from imio.history.interfaces import IImioHistory
from imio.history.utils import getLastAction
from imio.history.utils import getLastWFAction
from plone import api
from plone.app.querystring import queryparser
from plone.dexterity.utils import createContentInContainer
from plone.memoize.instance import Memojito
from Products.CMFCore.permissions import DeleteObjects
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.permissions import View
from Products.MeetingLiege.config import FINANCE_ADVICE_HISTORIZE_COMMENTS
from Products.MeetingLiege.config import ITEM_MAIN_INFOS_HISTORY
from Products.MeetingLiege.config import TREASURY_GROUP_ID
from Products.MeetingLiege.setuphandlers import _configureCollegeCustomAdvisers
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.PloneMeeting.config import ADVICE_GIVEN_HISTORIZED_COMMENT
from Products.PloneMeeting.config import HISTORY_COMMENT_NOT_VIEWABLE
from Products.PloneMeeting.indexes import indexAdvisers
from Products.PloneMeeting.indexes import reviewProcessInfo
from Products.PloneMeeting.utils import get_annexes
from Products.PloneMeeting.utils import main_item_data
from Products.PloneMeeting.utils import org_id_to_uid
from zope.component import getAdapter
from zope.component import getMultiAdapter
from zope.event import notify
from zope.i18n import translate
from zope.lifecycleevent import ObjectModifiedEvent


COUNCIL_LABEL = '<p>Label for Council.</p>'


class testCustomWorkflows(MeetingLiegeTestCase):
    """Tests the default workflows implemented in MeetingLiege."""

    def test_CollegeProcessWithoutAdvices(self):
        '''This test covers the whole decision workflow. It begins with the
           creation of some items, and ends by closing a meeting.
           The usecase here is to test the workflow without normal and finances advice.
           Observers have only access when item is 'validated'.'''
        # pmCreator1 creates an item and proposes it to the administrative reviewer
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem', title='The first item')
        # pmCreator may only 'proposeToAdministrativeReviewer'
        self.assertEqual(self.transitions(item),
                         ['proposeToAdministrativeReviewer'])
        # access for observer
        self.changeUser('pmObserver1')
        self.assertTrue(self.hasPermission(View, item))

        # a MeetingManager is able to validate an item immediatelly, bypassing
        # the entire validation workflow.
        # a director who is able to propose to administrative and internal
        # reviewer can also bypass those 2 transitions and propose the item directly to
        # the direction.
        self.changeUser('pmManager')
        self.assertEqual(self.transitions(item),
                         ['proposeToAdministrativeReviewer',
                          'proposeToDirector',
                          'proposeToInternalReviewer',
                          'validate'])
        # the pmCreator1 send the item to the administrative reviewer
        self.changeUser('pmCreator1')
        self.do(item, 'proposeToAdministrativeReviewer')
        # pmCreator1 can no more edit item but can still view it
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, item))
        # access for observer
        self.changeUser('pmObserver1')
        self.assertTrue(self.hasPermission(View, item))

        self.changeUser('pmAdminReviewer1')
        # pmAdminReviewer1 may access item and edit it
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(self.hasPermission(ModifyPortalContent, item))
        # he may send the item back to the pmCreator1 or send it to the internal reviewer
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'proposeToInternalReviewer'])
        self.do(item, 'proposeToInternalReviewer')
        # pmAdminReviewer1 can no more edit item but can still view it
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, item))
        # access for observer
        self.changeUser('pmObserver1')
        self.assertTrue(self.hasPermission(View, item))

        # pmInternalReviewer1 may access item and edit it
        self.changeUser('pmInternalReviewer1')
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(self.hasPermission(ModifyPortalContent, item))
        # he may send the item back to the administrative reviewer or send it to the reviewer (director)
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'backToProposedToAdministrativeReviewer',
                          'proposeToDirector', ])
        self.do(item, 'proposeToDirector')
        # pmInternalReviewer1 can no more edit item but can still view it
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, item))
        # access for observer
        self.changeUser('pmObserver1')
        self.assertTrue(self.hasPermission(View, item))

        # pmReviewer1 (director) may access item and edit it
        self.changeUser('pmReviewer1')
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(self.hasPermission(ModifyPortalContent, item))
        # he may send the item back to the internal reviewer, validate it
        # or send it back to itemCreated.
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'backToProposedToAdministrativeReviewer',
                          'backToProposedToInternalReviewer',
                          'validate'])
        self.do(item, 'validate')
        self.assertTrue(self.hasPermission(View, item))
        # pmReviewer1 can no more edit item but can still view it
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, item))
        # access for observer
        self.changeUser('pmObserver1')
        self.assertTrue(self.hasPermission(View, item))

        # create a meeting, a MeetingManager will manage it now
        self.changeUser('pmManager')
        # the item can be removed sent back to the reviewer (director) or sent back in 'itemcreated'
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'backToProposedToAdministrativeReviewer',
                          'backToProposedToDirector',
                          'backToProposedToInternalReviewer'])
        meeting = self.create('Meeting')
        # the item is available for the meeting
        availableItemsQuery = queryparser.parseFormquery(meeting, meeting._available_items_query())
        availableItemUids = [brain.UID for brain in self.catalog(availableItemsQuery)]
        self.assertTrue(item.UID() in availableItemUids)
        self.do(item, 'present')
        # access for observer
        self.changeUser('pmObserver1')
        self.assertTrue(self.hasPermission(View, item))
        self.changeUser('pmManager')
        self.assertEqual(item.query_state(), 'presented')
        # the item can be removed from the meeting
        self.assertEqual(self.transitions(item), ['backToValidated', 'return_to_proposing_group'])
        # the meeting can now be frozen then decided
        self.do(meeting, 'freeze')
        # access for observer
        self.changeUser('pmObserver1')
        self.assertTrue(self.hasPermission(View, item))
        self.changeUser('pmManager')
        # the item has been automatically frozen
        self.assertEqual(item.query_state(), 'itemfrozen')
        # but the item can be sent back to 'presented'
        self.assertEqual(self.transitions(item), ['backToPresented', 'return_to_proposing_group'])
        self.do(meeting, 'decide')
        # the item is still frozen but can be decided
        self.assertEqual(item.query_state(), 'itemfrozen')
        self.assertEqual(self.transitions(item),
                         ['accept',
                          'accept_and_return',
                          'accept_but_modify',
                          'backToPresented',
                          'delay',
                          'mark_not_applicable',
                          'pre_accept',
                          'refuse',
                          'return',
                          'return_to_proposing_group'])
        # if we pre_accept an item, we can accept it after
        self.do(item, 'pre_accept')
        # access for observer
        self.changeUser('pmObserver1')
        self.assertTrue(self.hasPermission(View, item))
        self.changeUser('pmManager')
        self.assertEqual(self.transitions(item),
                         ['accept',
                          'accept_but_modify',
                          'backToItemFrozen'])
        # if we decide an item, it may still be set backToItemFrozen until the meeting is closed
        self.do(item, 'accept')
        self.assertEqual(self.transitions(item),
                         ['backToItemFrozen', ])
        # access for observer
        self.changeUser('pmObserver1')
        self.assertTrue(self.hasPermission(View, item))
        self.changeUser('pmManager')
        # the meeting may be closed or back to frozen
        self.assertEqual(self.transitions(meeting),
                         ['backToFrozen', 'close', ])
        self.do(meeting, 'close')
        self.assertFalse(self.transitions(item))

    def test_CollegeProcessWithNormalAdvices(self):
        '''How does the process behave when some 'normal' advices,
           aka not 'finances' advices are aksed.'''
        self.changeUser('admin')
        self._createFinanceGroups()
        cfg = self.meetingConfig
        # normal advices can be given when item in state 'itemcreated_waiting_advices',
        # asked by item creator and when item in state 'proposed_to_internal_reviewer_waiting_advices',
        # asekd by internal reviewer
        cfg.setUsedAdviceTypes(('asked_again', ) + cfg.getUsedAdviceTypes())
        cfg.setItemAdviceStates(('itemcreated_waiting_advices',
                                 'proposed_to_internal_reviewer_waiting_advices'))
        cfg.setItemAdviceEditStates = (('itemcreated_waiting_advices',
                                        'proposed_to_internal_reviewer_waiting_advices'))
        cfg.setItemAdviceViewStates = (('itemcreated_waiting_advices',
                                        'proposed_to_administrative_reviewer',
                                        'proposed_to_internal_reviewer',
                                        'proposed_to_internal_reviewer_waiting_advices',
                                        'proposed_to_director', 'validated', 'presented',
                                        'itemfrozen', 'refused', 'delayed', 'removed',
                                        'pre_accepted', 'accepted', 'accepted_but_modified', ))
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem', title='The first item')
        # if no advice to ask, pmCreator may only 'proposeToAdministrativeReviewer'
        self.assertEqual(self.transitions(item), ['proposeToAdministrativeReviewer', ])
        # the mayAskAdvicesByItemCreator wfCondition returns a 'No' instance
        advice_required_to_ask_advices = translate('advice_required_to_ask_advices',
                                                   domain='PloneMeeting',
                                                   context=self.request)
        self.assertEqual(translate(
            item.wfConditions().mayWait_advices(item.query_state(), None).msg,
            context=self.request), advice_required_to_ask_advices)
        # now ask 'vendors' advice
        item.setOptionalAdvisers((self.vendors_uid, ))
        item._update_after_edit()
        self.assertEqual(self.transitions(item), ['proposeToAdministrativeReviewer',
                                                  'wait_advices_from_itemcreated'])
        # give advice
        self.do(item, 'wait_advices_from_itemcreated')
        # pmReviewer2 is adviser for vendors
        self.changeUser('pmReviewer2')
        advice = createContentInContainer(item,
                                          item.adapted()._advicePortalTypeForAdviser(self.vendors_uid),
                                          **{'advice_group': self.vendors_uid,
                                             'advice_type': u'positive',
                                             'advice_comment': richtextval(u'My comment vendors')})
        # no more advice to give
        self.assertFalse(item.hasAdvices(toGive=True))
        # item may be proposed directly to administrative reviewer
        # from state 'itemcreated_waiting_advices'
        # we continue wf as internal reviewer may also ask advice
        self.changeUser('pmCreator1')
        self.do(item, 'proposeToAdministrativeReviewer')
        self.changeUser('pmAdminReviewer1')
        self.do(item, 'proposeToInternalReviewer')
        self.changeUser('pmInternalReviewer1')
        # no advice to give so not askable
        self.assertEqual(self.transitions(item), ['backToItemCreated',
                                                  'backToProposedToAdministrativeReviewer',
                                                  'proposeToDirector'])
        # advice could be asked again
        self.assertTrue(item.adapted().mayAskAdviceAgain(advice))
        item.setOptionalAdvisers((self.vendors_uid, self.developers_uid))
        item._update_after_edit()
        # now that there is an advice to give (developers)
        # internal reviewer may ask it
        self.assertTrue(self.tool.userIsAmong(['internalreviewers']))
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'backToProposedToAdministrativeReviewer',
                          'proposeToDirector',
                          'wait_advices_from_proposed_to_internal_reviewer'])
        # it is the case for the director as well without being internal reviewer
        self.changeUser('pmReviewer1')
        self.assertFalse(self.tool.userIsAmong(['internalreviewers']))
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'backToProposedToAdministrativeReviewer',
                          'proposeToDirector',
                          'wait_advices_from_proposed_to_internal_reviewer'])
        # ask advice
        self.do(item, 'wait_advices_from_proposed_to_internal_reviewer')
        # pmAdviser1 is adviser for developers
        self.changeUser('pmAdviser1')
        createContentInContainer(item,
                                 item.adapted()._advicePortalTypeForAdviser(self.developers_uid),
                                 **{'advice_group': self.developers_uid,
                                    'advice_type': u'positive',
                                    'advice_comment': richtextval(u'My comment developers')})
        # item may be proposed directly to director
        # from state 'proposed_to_internal_reviewer_waiting_advices'
        self.changeUser('pmInternalReviewer1')
        self.do(item, 'proposeToDirector')

    def test_CollegeProcessWithFinancesAdvices(self):
        '''How does the process behave when some 'finances' advices is asked.'''
        self.changeUser('admin')
        cfg = self.meetingConfig
        cfg.setUsedAdviceTypes(('asked_again', ) + cfg.getUsedAdviceTypes())
        # add finance groups
        self._createFinanceGroups()
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # by default, an item with no selected financeAdvice does
        # not need a finances advice
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='The first item')
        self.assertTrue(not item.adapted().getFinanceGroupUIDForItem())
        self.assertTrue(not item.adviceIndex)
        # finances advice is an automatic advice aksed depending on the
        # selected MeetingItem.financeAdvice
        financial_group_uids = self.tool.finance_group_uids()
        item.setFinanceAdvice(financial_group_uids[0])
        item._update_after_edit()
        self.assertEqual(item.adapted().getFinanceGroupUIDForItem(), financial_group_uids[0])
        self.assertTrue(financial_group_uids[0] in item.adviceIndex)
        # now that it is asked, the item will have to be proposed to the finances
        # pmManager is member of every sub-groups of 'developers'
        self.proposeItem(item)
        # now the item is 'proposed_to_director' it can not be validated
        # the step 'proposed_to_finance_waiting_advices' is required
        self.assertEqual(item.query_state(), 'proposed_to_director')
        # from here, we can not validate the item, it can only be sent
        # to the finances or back to the internal reviewer.
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'backToProposedToAdministrativeReviewer',
                          'backToProposedToInternalReviewer',
                          'wait_advices_from_proposed_to_director'])
        # if emergency is asked, a director may either propose the item to finance or validate it
        item.setEmergency('emergency_asked')
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'backToProposedToAdministrativeReviewer',
                          'backToProposedToInternalReviewer',
                          'validate',
                          'wait_advices_from_proposed_to_director'])
        item.setEmergency('no_emergency')
        # for now, advisers of the FINANCE_GROUP_IDS[0] can not give the advice
        self.assertTrue(not item.adviceIndex[financial_group_uids[0]]['advice_addable'])
        # wait_advices_from_proposed_to_director, advice will not be giveable
        # as item.completeness is not 'completeness_complete'
        self.do(item, 'wait_advices_from_proposed_to_director')
        self.assertTrue(not item.adviceIndex[financial_group_uids[0]]['advice_addable'])
        # delay is not started, it only starts when item is complete
        self.assertTrue(not item.adviceIndex[financial_group_uids[0]]['delay_started_on'])
        # if we _updateAdvices, infos are still ok
        item.update_local_roles()
        # the item can be sent back to the internal reviewer by any finance role
        self.changeUser('pmFinController')
        self.assertEqual(self.transitions(item),
                         ['backTo_proposed_to_internal_reviewer_from_waiting_advices'])
        # set the item to "incomplete"
        self.assertTrue(item.adapted().mayEvaluateCompleteness())
        item.setCompleteness('completeness_incomplete')
        item._update_after_edit()
        self.assertEqual(self.transitions(item),
                         ['backTo_proposed_to_internal_reviewer_from_waiting_advices'])
        # pmFinController may not add advice for FINANCE_GROUP_IDS[0]
        toAdd, toEdit = item.getAdvicesGroupsInfosForUser()
        self.assertTrue(not toAdd and not toEdit)
        # set item as "complete" using itemcompleteness view
        # this way, it checks that current user may actually evaluate completeness
        # and item is updated (_update_after_edit is called)
        changeCompleteness = item.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()
        self.assertEqual(item.getCompleteness(), 'completeness_complete')
        # can be sent back even if considered complete
        self.assertEqual(self.transitions(item),
                         ['backTo_proposed_to_internal_reviewer_from_waiting_advices'])
        # but now, advice is giveable
        self.assertTrue(item.adviceIndex[financial_group_uids[0]]['advice_addable'])
        # and delay to give advice is started
        self.assertTrue(item.adviceIndex[financial_group_uids[0]]['delay_started_on'])
        # back to 'completeness_incomplete', advice can not be given anymore and delay is not started
        self.request.set('new_completeness_value', 'completeness_incomplete')
        changeCompleteness()
        self.assertEqual(item.getCompleteness(), 'completeness_incomplete')
        self.assertTrue(not item.adviceIndex[financial_group_uids[0]]['advice_addable'])
        self.assertTrue(not item.adviceIndex[financial_group_uids[0]]['delay_started_on'])
        # advice can also be given if completeness is 'completeness_evaluation_not_required'
        self.request.set('new_completeness_value', 'completeness_evaluation_not_required')
        changeCompleteness()
        self.assertEqual(item.getCompleteness(), 'completeness_evaluation_not_required')
        self.assertTrue(item.adviceIndex[financial_group_uids[0]]['advice_addable'])
        self.assertTrue(item.adviceIndex[financial_group_uids[0]]['delay_started_on'])
        # now advice may be given
        toAdd, toEdit = item.getAdvicesGroupsInfosForUser()
        self.assertTrue(toAdd and not toEdit)
        # give the advice
        advice = createContentInContainer(
            item,
            item.adapted()._advicePortalTypeForAdviser(financial_group_uids[0]),
            **{'advice_group': financial_group_uids[0],
               'advice_type': u'positive_with_remarks_finance',
               'advice_comment': richtextval(u'<p>My comment finance</p>'),
               'advice_observations': richtextval(u'<p>My observation finance</p>')})
        # once given, still editable
        toAdd, toEdit = item.getAdvicesGroupsInfosForUser()
        self.assertTrue(not toAdd and toEdit)
        # when created, a finance advice is automatically set to 'proposed_to_financial_controller'
        self.assertEqual(advice.query_state(), 'proposed_to_financial_controller')
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
        adapter = getAdapter(advice, IImioHistory, 'advice_given')
        self.assertIsNone(getLastAction(adapter))
        self.do(item, 'backTo_proposed_to_internal_reviewer_from_waiting_advices')
        # finance access is kept when item is sent back to internal reviewer no matter itemAdviceXXXStates
        self.assertTrue(self.hasPermission(View, item))
        self.assertFalse('proposed_to_internal_reviewer' in cfg.getItemAdviceStates())
        self.assertFalse('proposed_to_internal_reviewer' in cfg.getItemAdviceEditStates())
        self.assertFalse('proposed_to_internal_reviewer' in cfg.getItemAdviceViewStates())
        # advice was historized
        adapter = getAdapter(advice, IImioHistory, 'advice_given')
        last_action = getLastAction(adapter)
        self.assertEqual(last_action['comments'], ADVICE_GIVEN_HISTORIZED_COMMENT)
        # in this case, a specific icon is displayed in the prettyLink
        self.assertTrue('wf_down_finances.png' in item.getPrettyLink())
        # advice delay is no more started and advice is no more editable
        self.assertTrue(not item.adviceIndex[financial_group_uids[0]]['advice_addable'])
        self.assertTrue(not item.adviceIndex[financial_group_uids[0]]['advice_editable'])
        self.assertTrue(not item.adviceIndex[financial_group_uids[0]]['delay_started_on'])
        # completeness did not changed
        self.assertEqual(item.getCompleteness(), 'completeness_evaluation_not_required')
        # if item is sent back to the finance, it will not be enabled as
        # completeness was set automatically to 'completeness_evaluation_asked_again'
        self.changeUser('pmReviewer1')
        self.do(item, 'proposeToDirector')
        ask_advice_again = advice.restrictedTraverse('@@change-advice-asked-again')
        ask_advice_again()
        self.do(item, 'wait_advices_from_proposed_to_director')
        # item may be taken back when it is not complete
        self.assertEqual(self.transitions(item), ['backTo_proposed_to_director_from_waiting_advices'])
        self.changeUser('pmFinController')
        # delay did not start
        self.assertTrue(not item.adviceIndex[financial_group_uids[0]]['advice_addable'])
        self.assertTrue(not item.adviceIndex[financial_group_uids[0]]['advice_editable'])
        self.assertTrue(not item.adviceIndex[financial_group_uids[0]]['delay_started_on'])
        # completeness was set automatically to evaluation asked again
        self.assertEqual(item.getCompleteness(), 'completeness_evaluation_asked_again')
        # if pmFinController set completeness to complete, advice can be added
        self.request.set('new_completeness_value', 'completeness_complete')
        changeCompleteness()
        self.assertEqual(item.getCompleteness(), 'completeness_complete')
        self.assertTrue(not item.adviceIndex[financial_group_uids[0]]['advice_addable'])
        self.assertTrue(item.adviceIndex[financial_group_uids[0]]['advice_editable'])
        self.assertTrue(item.adviceIndex[financial_group_uids[0]]['delay_started_on'])
        # item may not be taken back anymore
        self.changeUser('pmReviewer1')
        self.assertEqual(self.transitions(item), [])

        # the advice can be proposed to the financial reviewer
        self.changeUser('pmFinController')
        self.assertEqual(self.transitions(advice), ['proposeToFinancialReviewer'])
        self.do(advice, 'proposeToFinancialReviewer')
        # can no more edit, but still view
        self.assertTrue(self.hasPermission(View, advice))
        self.assertFalse(self.hasPermission(ModifyPortalContent, advice))
        # no more addable/editable
        toAdd, toEdit = item.getAdvicesGroupsInfosForUser()
        self.assertTrue(not toAdd and not toEdit)
        # log as finance reviewer
        self.changeUser('pmFinReviewer')
        # may view and edit
        self.assertEqual(advice.query_state(), 'proposed_to_financial_reviewer')
        self.assertTrue(self.hasPermission(View, advice))
        self.assertTrue(self.hasPermission(ModifyPortalContent, advice))
        toAdd, toEdit = item.getAdvicesGroupsInfosForUser()
        self.assertTrue(not toAdd and toEdit)
        # may return to finance controller, send to finance manager or sign the advice
        self.assertEqual(self.transitions(advice), ['backToProposedToFinancialController',
                                                    'proposeToFinancialManager',
                                                    'signFinancialAdvice'])
        # finance reviewer may sign (publish) advice because the advice_type
        # is not "negative", if negative, it is the finance manager that will
        # be able to sign the advice
        advice.advice_type = u'negative_finance'
        notify(ObjectModifiedEvent(advice))
        self.assertEqual(self.transitions(advice), ['backToProposedToFinancialController',
                                                    'proposeToFinancialManager'])
        # propose to financial manager that will sign the advice
        self.do(advice, 'proposeToFinancialManager')
        self.assertTrue(self.hasPermission(View, advice))
        self.assertTrue(not self.hasPermission(ModifyPortalContent, advice))
        # no more addable/editable
        toAdd, toEdit = item.getAdvicesGroupsInfosForUser()
        self.assertTrue(not toAdd and not toEdit)
        # log as finance manager
        self.changeUser('pmFinManager')
        # may view and edit
        self.assertEqual(advice.query_state(), 'proposed_to_financial_manager')
        self.assertTrue(self.hasPermission(View, advice))
        self.assertTrue(self.hasPermission(ModifyPortalContent, advice))
        # the financial manager may either sign the advice
        # or send it back to the financial reviewer or controller
        self.assertEqual(self.transitions(advice), ['backToProposedToFinancialController',
                                                    'backToProposedToFinancialReviewer',
                                                    'signFinancialAdvice'])
        # if a financial manager sign a negative advice, the linked item will
        # be automatically sent back to the director, the advice is no more editable
        # moreover, when signed, the advice is automatically set to advice_hide_during_redaction=False
        self.assertTrue(advice.advice_hide_during_redaction)
        self.do(advice, 'signFinancialAdvice')
        self.assertEqual(item.query_state(), 'proposed_to_internal_reviewer')
        self.assertEqual(advice.query_state(), 'advice_given')
        self.assertFalse(advice.advice_hide_during_redaction)
        # when an advice is signed, it is automatically historized
        adapter = getAdapter(advice, IImioHistory, 'advice_given')
        last_action_signed1 = getLastAction(adapter)
        self.assertEqual(last_action_signed1['comments'], FINANCE_ADVICE_HISTORIZE_COMMENTS)
        # as there is a finance advice on the item, finance keep read access to the item
        self.assertTrue(self.hasPermission(View, item))
        # now an item with a negative financial advice back to the director
        # as no emergency is asked, the item can not be validated
        self.changeUser('pmReviewer1')
        ask_advice_again()
        self.do(item, 'proposeToDirector')
        self.assertEqual(self.transitions(item), ['backToItemCreated',
                                                  'backToProposedToAdministrativeReviewer',
                                                  'backToProposedToInternalReviewer',
                                                  'wait_advices_from_proposed_to_director'])
        # financial advice is asked_again and can no more be
        self.assertEqual(advice.advice_type, 'asked_again')
        self.assertFalse(item.adapted().mayAskAdviceAgain(advice))
        # a director can send the item back to director or internal reviewer even
        # when advice is on the way by finance.  So send it again to finance and take it back
        self.do(item, 'wait_advices_from_proposed_to_director')
        # completeness was 'completeness_evaluation_asked_again'
        self.assertEqual(item.getCompleteness(), 'completeness_evaluation_asked_again')
        self.assertEqual(item.query_state(), 'proposed_to_finance_waiting_advices')
        self.assertEqual(self.transitions(item), ['backTo_proposed_to_director_from_waiting_advices'])
        # a reviewer can send the item back to the director
        self.do(item, 'backTo_proposed_to_director_from_waiting_advices')
        # ok now the director can send it again to the finance
        # and finance can adapt the advice
        self.do(item, 'wait_advices_from_proposed_to_director')
        self.assertEqual(item.query_state(), 'proposed_to_finance_waiting_advices')
        # advice is available to the financial controller
        self.assertEqual(advice.query_state(), 'proposed_to_financial_controller')
        # and is hidden again
        self.assertTrue(advice.advice_hide_during_redaction)
        # now he will change the advice_type to 'positive_finance'
        # and the financial reviewer will sign it
        self.changeUser('pmFinController')
        advice.advice_type = u'positive_finance'
        notify(ObjectModifiedEvent(advice))
        # advice may only be sent to the financial reviewer
        self.assertEqual(self.transitions(advice), ['proposeToFinancialReviewer'])
        self.do(advice, 'proposeToFinancialReviewer')
        self.changeUser('pmFinReviewer')
        # financial reviewer may sign a positive advice or send it to the finance manager
        self.assertEqual(self.transitions(advice), ['backToProposedToFinancialController',
                                                    'proposeToFinancialManager',
                                                    'signFinancialAdvice'])
        self.do(advice, 'signFinancialAdvice')
        # each time an advice is signed, it is historized in the advice history
        adapter = getAdapter(advice, IImioHistory, 'advice_given')
        last_action_signed2 = getLastAction(adapter)
        self.assertNotEqual(last_action_signed1['time'], last_action_signed2['time'])
        self.assertEqual(last_action_signed2['comments'], FINANCE_ADVICE_HISTORIZE_COMMENTS)

        # this time, the item has been validated automatically
        self.assertEqual(item.query_state(), 'validated')
        # and the advice is visible to everybody
        self.assertFalse(advice.advice_hide_during_redaction)
        self.assertEqual(advice.query_state(), 'advice_given')
        # item.adviceIndex is coherent also, the 'addable'/'editable' data is correct
        self.assertFalse(item.adviceIndex[financial_group_uids[0]]['advice_editable'])
        self.assertFalse(item.adviceIndex[financial_group_uids[0]]['advice_addable'])
        # advice is viewable
        # but is no more editable by any financial role
        # not for financial reviewer
        self.assertTrue(self.hasPermission(View, advice))
        self.assertFalse(self.hasPermission(ModifyPortalContent, advice))
        # not for financial controller
        self.changeUser('pmFinController')
        self.assertTrue(self.hasPermission(View, advice))
        self.assertFalse(self.hasPermission(ModifyPortalContent, advice))
        # no more for financial manager
        self.changeUser('pmFinManager')
        self.assertTrue(self.hasPermission(View, advice))
        self.assertFalse(self.hasPermission(ModifyPortalContent, advice))
        # if the advice is no more editable, it's state switched to 'advice_given'
        self.changeUser('pmManager')
        meeting = self.create('Meeting')
        # freeze the meeting, the advice will be set to 'advice_given'
        # the advice could still be given if not already in state 'presented' and 'itemfrozen'
        self.presentItem(item)
        self.freezeMeeting(meeting)
        self.assertEqual(meeting.query_state(), 'frozen')
        self.assertEqual(item.query_state(), 'itemfrozen')
        self.assertEqual(advice.query_state(), 'advice_given')
        # a finance adviser is able to add decision annexes to the item when it is decided
        self.changeUser('pmFinController')
        adviserGroupId = '%s_advisers' % financial_group_uids[0]
        self.assertEqual(item.__ac_local_roles__[adviserGroupId], ['Reader', ])
        self.assertEqual(item.query_state(), 'itemfrozen')
        self.assertRaises(Unauthorized, self.addAnnex, item, relatedTo='item_decision')
        self.changeUser('pmManager')
        self.decideMeeting(meeting)
        self.do(item, 'accept')
        self.assertEqual(item.query_state(), 'accepted')
        self.changeUser('pmFinController')
        self.assertEqual(item.__ac_local_roles__[adviserGroupId], ['Reader', 'Contributor'])
        self.changeUser('pmFinController')
        self.assertFalse(get_annexes(item, portal_types=['annexDecision']))
        # finance user is able to add a decision annex
        self.addAnnex(item, relatedTo='item_decision')
        self.assertTrue(get_annexes(item, portal_types=['annexDecision']))
        # if we go back to itemfrozen, 'MeetingMember' is not more there
        self.changeUser('pmManager')
        self.do(item, 'backToItemFrozen')
        self.assertEqual(item.query_state(), 'itemfrozen')
        self.assertEqual(item.__ac_local_roles__[adviserGroupId], ['Reader', ])

    def test_CollegeProcessWithFinancesAdvicesWithEmergency(self):
        '''If emergency is asked for an item by director, the item can be sent
           to the meeting (validated) without finance advice, finance advice is still giveable...
           Make sure a MeetingManager is able to present such an item or send back to the director.'''
        self.changeUser('admin')
        # add finance groups
        self._createFinanceGroups()
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # remove pmManager from 'developers' so he will not have the 'MeetingReviewer' role
        # managed by the meetingadviceliege_workflow and giving access to 'Access contents information'
        self.changeUser('pmManager')
        dev_groups = [grp for grp in self.member.getGroups()
                      if grp.startswith(self.developers_uid)]
        self._removePrincipalFromGroups('pmManager', dev_groups)

        self.changeUser('pmCreator1')
        # create an item and ask finance advice
        item = self.create('MeetingItem')
        financial_group_uids = self.tool.finance_group_uids()
        item.setFinanceAdvice(financial_group_uids[0])
        # no emergency for now
        item.setEmergency('no_emergency')
        item._update_after_edit()
        # finance advice is asked
        self.assertEqual(item.adapted().getFinanceGroupUIDForItem(), financial_group_uids[0])
        self.assertTrue(financial_group_uids[0] in item.adviceIndex)
        # propose the item to the director, he will send item to finance
        self.proposeItem(item)
        self.changeUser('pmReviewer1')
        self.do(item, 'wait_advices_from_proposed_to_director')
        # finance will add advice and send item back to the internal reviewer
        self.changeUser('pmFinController')
        changeCompleteness = item.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()
        # give the advice
        advice = createContentInContainer(item,
                                          item.adapted()._advicePortalTypeForAdviser(financial_group_uids[0]),
                                          **{'advice_group': financial_group_uids[0],
                                             'advice_type': u'positive_finance',
                                             'advice_comment': richtextval(u'<p>My comment finance</p>'),
                                             'advice_observations': richtextval(u'<p>My observation finance</p>')})
        self.do(item, 'backTo_proposed_to_internal_reviewer_from_waiting_advices')
        # internal reviewer will send item to the director that will ask emergency
        self.changeUser('pmInternalReviewer1')
        self.do(item, 'proposeToDirector')
        self.changeUser('pmReviewer1')
        # no emergency for now so item can not be validated
        self.assertTrue('validate' not in self.transitions(item))
        # ask emergency
        self.assertTrue(item.adapted().mayAskEmergency())
        item.setEmergency('emergency_asked')
        # now item can be validated
        self.assertTrue('validate' in self.transitions(item))
        self.do(item, 'validate')
        # item has been validated and is viewable by the MeetingManagers
        self.changeUser('pmManager')
        # advice is given
        self.assertEqual(advice.query_state(), 'advice_given')
        # item can be sent back to the director, this will test that advice state
        # can be changed even if advice is not viewable
        self.do(item, 'backToProposedToDirector')
        self.assertEqual(advice.query_state(), 'advice_given')
        # director validate item again
        self.changeUser('pmReviewer1')
        self.do(item, 'validate')
        # create a meeting and make sure it can be frozen, aka it will
        # change not viewable advice state to 'advice_given'
        self.changeUser('pmManager')
        meeting = self.create('Meeting')
        self.do(item, 'present')
        # advice state is still given
        self.assertEqual(advice.query_state(), 'advice_given')
        # if the meeting is frozen, every items are frozen as well
        # and finance advices are no more giveable, so advice will go to 'advice_given'
        self.do(meeting, 'freeze')
        self.assertEqual(advice.query_state(), 'advice_given')

    def test_ItemWithTimedOutAdviceIsAutomaticallyValidated(self):
        '''When an item is 'proposed_to_finance_waiting_advices', it may be validated
           only by finance group or if emergency is asked.  In case the asked
           advice is timed out, it will be automatically validated.'''
        self.changeUser('admin')
        # add finance groups
        self._createFinanceGroups()
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # send item to finance
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='The first item')
        financial_group_uids = self.tool.finance_group_uids()
        item.setFinanceAdvice(financial_group_uids[0])
        item._update_after_edit()
        self.proposeItem(item)
        self.do(item, 'wait_advices_from_proposed_to_director')
        # item is now 'proposed_to_finance_waiting_advices'
        self.assertEqual(item.query_state(), 'proposed_to_finance_waiting_advices')
        # item can not be validated
        self.assertTrue('validate' not in self.transitions(item))

        # now add advice
        self.changeUser('pmFinController')
        # give the advice
        item.setCompleteness('completeness_complete')
        item._update_after_edit()
        advice = createContentInContainer(item,
                                          item.adapted()._advicePortalTypeForAdviser(financial_group_uids[0]),
                                          **{'advice_group': financial_group_uids[0],
                                             'advice_type': u'positive_finance',
                                             'advice_comment': richtextval(u'My comment finance')})
        # sign advice, necessary to test _updateAdvices called in _updateAdvices...
        self.do(advice, 'proposeToFinancialReviewer')
        self.changeUser('pmFinReviewer')
        self.do(advice, 'proposeToFinancialManager')
        self.changeUser('pmFinManager')
        self.do(advice, 'signFinancialAdvice')
        self.assertEqual(advice.query_state(), 'advice_given')
        # can not be validated
        self.changeUser('pmManager')
        self.assertFalse('validate' in self.transitions(item))
        # now does advice timed out
        item.adviceIndex[financial_group_uids[0]]['delay_started_on'] = datetime(2014, 1, 1)
        item.update_local_roles()
        # advice is timed out but as auto validated, it is 'no_more_giveable'
        self.assertEqual(item.adviceIndex[financial_group_uids[0]]['delay_infos']['delay_status'],
                         'no_more_giveable')
        # item has been automatically validated
        self.assertEqual(item.query_state(), 'validated')
        # if item is sent back to director, the director is able to validate it as well as MeetingManagers
        self.do(item, 'backToProposedToDirector')
        self.changeUser('pmReviewer1')
        self.assertTrue('validate' in self.transitions(item))
        self.changeUser('pmManager')
        self.assertTrue('validate' in self.transitions(item))

        # now test that a 'timed_out' advice can be set back to editable
        # by finance advice from no more editable, for this, go to 'itemfrozen'
        # this test a corrected bug where 'delay_infos' key was no more present
        # in the adviceIndex because _updateAdvices is called during _updateAdvices
        self.do(item, 'validate')
        self.changeUser('pmManager')
        meeting = self.create('Meeting')
        self.presentItem(item)
        self.assertEqual(advice.query_state(), 'advice_given')
        self.assertFalse(item.adviceIndex[financial_group_uids[0]]['advice_editable'])
        self.assertEqual(item.adviceIndex[financial_group_uids[0]]['delay_infos']['delay_status'],
                         'no_more_giveable')
        self.freezeMeeting(meeting)
        self.assertEqual(advice.query_state(), 'advice_given')
        self.assertFalse(item.adviceIndex[financial_group_uids[0]]['advice_editable'])
        self.assertEqual(item.adviceIndex[financial_group_uids[0]]['delay_infos']['delay_status'],
                         'no_more_giveable')
        self.assertEqual(item.query_state(), 'itemfrozen')
        # now back to 'presented'
        self.do(item, 'backToPresented')
        self.assertEqual(item.query_state(), 'presented')
        # advice is back to 'presented' but as 'no_more_giveable', no more editable
        self.assertEqual(advice.query_state(), 'advice_given')
        self.assertFalse(item.adviceIndex[financial_group_uids[0]]['advice_editable'])
        self.assertEqual(item.adviceIndex[financial_group_uids[0]]['delay_infos']['delay_status'],
                         'no_more_giveable')

    def test_ReturnCollege(self):
        '''Test behaviour of the 'return' decision transition.
           This will duplicate the item and the new item will be automatically
           validated so it is available for the next meetings.'''
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem', title='An item to return')
        self.changeUser('pmManager')
        meeting = self.create('Meeting')
        # present the item into the meeting
        self.presentItem(item)
        self.decideMeeting(meeting)
        # now the item can be 'returned'
        self.assertTrue('return' in self.transitions(item))
        # no duplicated for now
        self.assertTrue(not item.get_successors())
        self.do(item, 'return')
        self.assertEqual(item.query_state(), 'returned')

        # access for observer
        self.changeUser('pmObserver1')
        self.assertTrue(self.hasPermission(View, item))

        # now that the item is 'returned', it has been duplicated
        # and the new item has been validated
        self.changeUser('pmManager')
        returned = item.get_successors()
        self.assertEqual(len(returned), 1)
        returned = returned[0]
        self.assertEqual(returned.query_state(), 'validated')
        self.assertEqual(returned.portal_type, item.portal_type)
        # original creator was kept
        self.assertEqual(item.Creator(), 'pmCreator1')
        self.assertEqual(returned.Creator(), item.Creator())

    def test_AcceptAndReturnCollege(self):
        '''Test behaviour of the 'accept_and_return' decision transition.
           This will send the item to the council then duplicate the original item (college)
           and automatically validate it so it is available for the next meetings.'''
        cfg = self.meetingConfig
        cfgId = cfg.getId()
        cfg2 = self.meetingConfig2
        cfg2Id = cfg2.getId()
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem', title='An item to return')
        item2 = self.create('MeetingItem', title='An item to return and to send to Council')
        item2.setOtherMeetingConfigsClonableTo((cfg2Id, ))
        # create meetingFolder in cfg2 for pmCreator1
        self.getMeetingFolder(cfg2)
        self.changeUser('pmManager')
        meeting = self.create('Meeting')
        # present the item into the meeting
        self.presentItem(item)
        self.presentItem(item2)
        self.decideMeeting(meeting)
        # the 'accept_and_return' transition is available no matter
        # item is to send to Council or not
        self.assertTrue('accept_and_return' in self.transitions(item))
        self.assertTrue('accept_and_return' in self.transitions(item2))
        # accept_and_return, the items, item2 is send to the meetingConfig2
        # and both are duplicated in current config and set to 'validated'
        self.do(item, 'accept_and_return')
        self.do(item2, 'accept_and_return')
        returned = item.get_successors()
        returned2 = item2.get_successors()
        self.assertEqual(len(returned), 1)
        self.assertEqual(len(returned2), 2)
        returned = returned[0]
        duplicated1, duplicated2 = returned2
        # original creator was kept
        self.assertEqual(item.Creator(), 'pmCreator1')
        self.assertEqual(returned.Creator(), item.Creator())
        self.assertEqual(duplicated1.Creator(), item.Creator())
        self.assertEqual(duplicated2.Creator(), item.Creator())
        self.assertEqual(returned.portal_type, item.portal_type)
        # predecessors are not sorted, so one of both is duplicated to another
        # meetingConfig and the other is duplicated locally...
        # sent to the council
        if duplicated1.portal_type == cfg2.getItemTypeName():
            duplicatedToCfg2 = duplicated1
            duplicatedLocally = duplicated2
        else:
            duplicatedToCfg2 = duplicated2
            duplicatedLocally = duplicated1
        self.assertEqual(duplicatedToCfg2.portal_type, cfg2.getItemTypeName())
        self.assertEqual(duplicatedToCfg2.UID(), item2.getItemClonedToOtherMC(cfg2Id).UID())
        # duplicated locally...
        self.assertEqual(duplicatedLocally.portal_type, item2.portal_type)
        # ... and validated
        self.assertEqual(duplicatedLocally.query_state(), 'validated')
        # informations about "needs to be sent to other mc" is kept
        self.assertEqual(duplicatedLocally.getOtherMeetingConfigsClonableTo(), (cfg2Id, ))
        # now if duplicated item is accepted again, it will not be sent again the council
        meeting2 = self.create('Meeting')
        # present the item into the meeting
        self.presentItem(duplicatedLocally)
        self.decideMeeting(meeting2)
        # it already being considered as sent to the other mc
        self.assertTrue(duplicatedLocally._checkAlreadyClonedToOtherMC(cfg2Id))
        # it will not be considered as sent to the other mc if item
        # that was sent in the council is 'delayed' or 'marked_not_applicable'
        # so insert duplicatedToCfg2 in a meeting and 'delay' it
        self.setMeetingConfig(cfg2Id)
        councilMeeting = self.create('Meeting')
        self.setMeetingConfig(cfgId)
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

        # access for observer
        self.changeUser('pmObserver1')
        self.assertTrue(self.hasPermission(View, item))

        # now, make sure an already duplicated item
        # with an item on the council that is not 'delayed' or 'marked_not_applicable' is
        # not sent again
        self.changeUser('pmManager')
        returned = duplicatedLocally.get_successors()
        newduplicated1, newduplicated2 = returned
        # original creator was kept
        self.assertEqual(newduplicated1.Creator(), item.Creator())
        self.assertEqual(newduplicated2.Creator(), item.Creator())
        if newduplicated1.portal_type == cfg2.getItemTypeName():
            newDuplicatedLocally = newduplicated2
        else:
            newDuplicatedLocally = newduplicated1
        self.assertEqual(newDuplicatedLocally.portal_type, cfg.getItemTypeName())
        meeting3 = self.create('Meeting')
        self.presentItem(newDuplicatedLocally)
        self.decideMeeting(meeting3)
        # it is considered sent, so accepting it will not send it again
        self.assertTrue(newDuplicatedLocally._checkAlreadyClonedToOtherMC(cfg2Id))
        self.do(newDuplicatedLocally, 'accept')
        # it has not be sent again
        self.assertFalse(newDuplicatedLocally.getItemClonedToOtherMC(cfg2Id))

        # make sure an item that is 'Duplicated and keep link' with an item
        # that was 'accepted_and_returned' is sendable to another mc
        self.assertEqual(duplicatedLocally.query_state(), 'accepted_and_returned')
        # publish 'Members' so 'pmManager' can traverse to duplicated item url
        self.changeUser('siteadmin')
        self.do(self.portal.Members, 'publish')

        self.changeUser('pmManager')
        # duplicate and keep link
        form = duplicatedLocally.restrictedTraverse('@@item_duplicate_form').form_instance
        form.update()
        data = {'keep_link': True, 'annex_ids': [], 'annex_decision_ids': []}
        dupLinkedItem = form._doApply(data)
        self.assertEqual(dupLinkedItem.getRawManuallyLinkedItems(), [duplicatedLocally.UID()])
        self.assertTrue(getLastWFAction(dupLinkedItem, 'Duplicate and keep link'))
        self.assertEqual(dupLinkedItem.getOtherMeetingConfigsClonableTo(), (cfg2Id,))
        meeting4 = self.create('Meeting')
        self.presentItem(dupLinkedItem)
        self.decideMeeting(meeting4)
        # once accepted, it has been sent to the council
        self.do(dupLinkedItem, 'accept')
        self.assertTrue(dupLinkedItem.getItemClonedToOtherMC(cfg2Id))

    def test_IndexAdvisersIsCorrectAfterAdviceTransition(self):
        '''Test that when a transition is triggered on a meetingadvice
           using finance workflow, the indexAdvisers index is always correct.'''
        self.changeUser('admin')
        # add finance groups
        self._createFinanceGroups()
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='The first item')
        # ask finance advice
        financial_group_uids = self.tool.finance_group_uids()
        item.setFinanceAdvice(financial_group_uids[0])
        item._update_after_edit()
        # the finance advice is asked
        self.assertEqual(item.adapted().getFinanceGroupUIDForItem(), financial_group_uids[0])
        self.assertTrue(financial_group_uids[0] in item.adviceIndex)
        # send item to finance
        self.proposeItem(item)
        self.assertEqual(item.query_state(), 'proposed_to_director')
        self.do(item, 'wait_advices_from_proposed_to_director')
        # give the advice
        self.changeUser('pmFinController')
        advice = createContentInContainer(item,
                                          item.adapted()._advicePortalTypeForAdviser(financial_group_uids[0]),
                                          **{'advice_group': financial_group_uids[0],
                                             'advice_type': u'positive_finance',
                                             'advice_comment': richtextval(u'My comment finance')})
        # now play advice finance workflow and check catalog indexAdvisers is correct
        catalog = api.portal.get_tool('portal_catalog')
        itemPath = item.absolute_url_path()
        # when created, a finance advice is automatically set to 'proposed_to_financial_controller'
        self.assertEqual(advice.query_state(), 'proposed_to_financial_controller')
        self.assertEqual(indexAdvisers(item)(), catalog.getIndexDataForUID(itemPath)['indexAdvisers'])
        # as finance controller
        self.do(advice, 'proposeToFinancialReviewer')
        self.assertEqual(advice.query_state(), 'proposed_to_financial_reviewer')
        self.assertEqual(indexAdvisers(item)(), catalog.getIndexDataForUID(itemPath)['indexAdvisers'])
        # as finance reviewer
        self.changeUser('pmFinReviewer')
        advice.advice_type = u'negative_finance'
        self.do(advice, 'proposeToFinancialManager')
        self.assertEqual(advice.query_state(), 'proposed_to_financial_manager')
        self.assertEqual(indexAdvisers(item)(), catalog.getIndexDataForUID(itemPath)['indexAdvisers'])
        # log as finance manager
        self.changeUser('pmFinManager')
        self.do(advice, 'signFinancialAdvice')
        # item was sent back to director
        self.assertEqual(item.query_state(), 'proposed_to_internal_reviewer')
        self.assertEqual(advice.query_state(), 'advice_given')
        self.assertEqual(indexAdvisers(item)(), catalog.getIndexDataForUID(itemPath)['indexAdvisers'])
        # send item again to finance
        self.changeUser('pmReviewer1')
        ask_advice_again = advice.restrictedTraverse('@@change-advice-asked-again')
        ask_advice_again()
        self.do(item, 'proposeToDirector')
        self.do(item, 'wait_advices_from_proposed_to_director')
        self.assertEqual(item.query_state(), 'proposed_to_finance_waiting_advices')
        self.assertEqual(indexAdvisers(item)(), catalog.getIndexDataForUID(itemPath)['indexAdvisers'])
        # advice is available to the financial controller
        self.changeUser('pmFinController')
        self.assertEqual(advice.query_state(), 'proposed_to_financial_controller')
        advice.advice_type = u'positive_with_remarks_finance'
        self.do(advice, 'proposeToFinancialReviewer')
        self.assertEqual(advice.query_state(), 'proposed_to_financial_reviewer')
        self.assertEqual(indexAdvisers(item)(), catalog.getIndexDataForUID(itemPath)['indexAdvisers'])
        self.changeUser('pmFinReviewer')
        self.do(advice, 'signFinancialAdvice')
        # this time, the item has been validated automatically
        self.assertEqual(item.query_state(), 'validated')
        self.assertEqual(advice.query_state(), 'advice_given')
        self.assertEqual(indexAdvisers(item)(), catalog.getIndexDataForUID(itemPath)['indexAdvisers'])

    def test_ItemCommentViewability(self):
        '''Test that even when comments are only shown to the proposing group,
           some specific comments are shown to the group the financial advice is asked to.'''
        self.changeUser('admin')
        # add finance groups
        self._createFinanceGroups()
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
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
        financial_group_uids = self.tool.finance_group_uids()
        item.setFinanceAdvice(financial_group_uids[0])
        item._update_after_edit()
        self.proposeItem(item)
        # now director send the item back to the internal reviewer
        # it will use transition 'backToProposedToInternalReviewer' but will
        # not be visible by the finances group
        self.do(item, 'backToProposedToInternalReviewer')
        self.proposeItem(item)
        # send item to finance
        self.do(item, 'wait_advices_from_proposed_to_director', comment='Proposed to finances by director')
        # save event index (position in the history) we will have to check access to
        wf_history_adapter = getAdapter(item, IImioHistory, 'workflow')
        history = wf_history_adapter.getHistory()
        proposedToFinancesViewableIndex = history.index(history[-1])
        # now finance send it back to the internal reviewer
        self.do(item, 'backTo_proposed_to_internal_reviewer_from_waiting_advices')
        # save event
        # clean memoize
        getattr(wf_history_adapter, Memojito.propname).clear()
        history = wf_history_adapter.getHistory()
        proposedToInternalReviewerViewableIndex = history.index(history[-1])

        # ok now, check, the only viewable events for finance group members
        # should be proposedToFinancesViewableIndex and proposedToInternalReviewerViewableIndex
        viewableCommentIndexes = (proposedToFinancesViewableIndex, proposedToInternalReviewerViewableIndex)
        self.changeUser('pmFinController')
        # clean memoize
        getattr(wf_history_adapter, Memojito.propname).clear()
        history = wf_history_adapter.getHistory()
        for event in history:
            if history.index(event) in viewableCommentIndexes:
                # comment is viewable
                self.assertNotEqual(event['comments'], HISTORY_COMMENT_NOT_VIEWABLE)
            else:
                self.assertEqual(event['comments'], HISTORY_COMMENT_NOT_VIEWABLE)

    def test_AdviceCommentViewability(self):
        '''Test that advice comments are only viewable to finance group members and MeetingManagers.
           Except the FINANCE_ADVICE_HISTORIZE_EVENT that is viewable by everyone who may access the advice.'''
        self.changeUser('admin')
        # add finance groups
        self._createFinanceGroups()
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # create an item and ask finance advice
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='The first item')
        financial_group_uids = self.tool.finance_group_uids()
        item.setFinanceAdvice(financial_group_uids[0])
        item._update_after_edit()
        self.proposeItem(item)
        self.do(item, 'wait_advices_from_proposed_to_director')
        # make item completeness complete and add advice
        self.changeUser('pmFinController')
        changeCompleteness = item.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()
        advice = createContentInContainer(
            item,
            item.adapted()._advicePortalTypeForAdviser(financial_group_uids[0]),
            **{'advice_group': financial_group_uids[0],
               'advice_type': u'positive_finance',
               'advice_comment': richtextval(u'<p>My comment finance</p>'),
               'advice_observations': richtextval(u'<p>My observation finance</p>')})
        self.assertEqual(advice.query_state(), 'proposed_to_financial_controller')
        self.do(advice, 'proposeToFinancialReviewer', comment='My financial controller comment')
        # as finance reviewer
        self.changeUser('pmFinReviewer')
        self.do(advice, 'proposeToFinancialManager', comment='My financial reviewer comment')
        # as finance manager
        self.changeUser('pmFinManager')
        self.do(advice, 'signFinancialAdvice', comment='My financial manager comment')
        # now check history comment viewability
        # viewable to pmFinManager and other members of the finance group
        wf_history_adapter = getAdapter(advice, IImioHistory, 'workflow')
        history = wf_history_adapter.getHistory()
        for event in history:
            self.assertNotEqual(event['comments'], HISTORY_COMMENT_NOT_VIEWABLE)
        # not viewable to the pmManager as only Managers may access those comments
        self.changeUser('pmManager')
        # clean memoize
        getattr(wf_history_adapter, Memojito.propname).clear()
        history = wf_history_adapter.getHistory()
        for event in history:
            self.assertEqual(event['comments'], HISTORY_COMMENT_NOT_VIEWABLE)
        # user able to see the advice have same access as a MeetingManager, so only
        # access to the HISTORY_COMMENT_NOT_VIEWABLE
        self.changeUser('pmCreator1')
        # user may not see advice history comments like a MeetingManager
        self.hasPermission(View, advice)
        # clean memoize
        getattr(wf_history_adapter, Memojito.propname).clear()
        history = wf_history_adapter.getHistory()
        for event in history:
            self.assertEqual(event['comments'], HISTORY_COMMENT_NOT_VIEWABLE)

    def test_MeetingManagersMayNotDeleteItems(self):
        '''
          MeetingManagers are not able to Delete an item.
        '''
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        self.validateItem(item)
        self.changeUser('pmManager')
        self.assertFalse(self.hasPermission(DeleteObjects, item))
        meeting = self.create('Meeting')
        self.presentItem(item)
        self.assertEqual(item.query_state(), 'presented')
        self.assertFalse(self.hasPermission(DeleteObjects, item))
        self.freezeMeeting(meeting)
        self.assertEqual(item.query_state(), 'itemfrozen')
        self.assertFalse(self.hasPermission(DeleteObjects, item))
        self.decideMeeting(meeting)
        self.assertEqual(item.query_state(), 'itemfrozen')
        self.assertFalse(self.hasPermission(DeleteObjects, item))
        self.closeMeeting(meeting)
        self.assertEqual(item.query_state(), 'accepted')
        self.assertFalse(self.hasPermission(DeleteObjects, item))

    def test_FinanceAdvisersAccessToAutoLinkedItems(self):
        """Finance adviser have still access to items that were automatically linked to
           an item they give advice on.
           This is the case for 'returned' items and items sent to Council."""
        item, advice = self._setupCollegeItemWithFinanceAdvice()
        # present the item into the meeting
        self.changeUser('pmManager')
        meeting = self.create('Meeting')
        self.presentItem(item)
        self.decideMeeting(meeting)
        self.do(item, 'return')
        self.assertEqual(item.query_state(), 'returned')
        # now that the item is 'returned', it has been duplicated
        # and the finance advisers have access to the newItem
        newItem = item.get_successors()[0]
        financial_group_uids = self.tool.finance_group_uids()
        self.assertEqual(newItem.__ac_local_roles__['{0}_advisers'.format(financial_group_uids[0])],
                         ['Reader', ])
        # right, remove newItem and 'accept_and_return' item
        self.do(item, 'backToItemFrozen')
        self.changeUser('admin')
        newItem.getParentNode().manage_delObjects(ids=[newItem.getId(), ])
        self.changeUser('pmManager')
        item.setOtherMeetingConfigsClonableTo((self.meetingConfig2.getId(), ))
        self.do(item, 'accept_and_return')
        self.assertEqual(item.query_state(), 'accepted_and_returned')
        predecessors = item.get_successors()
        self.assertEqual(len(predecessors), 2)
        self.assertEqual(predecessors[0].__ac_local_roles__['{0}_advisers'.format(financial_group_uids[0])],
                         ['Reader', ])
        self.assertEqual(predecessors[1].__ac_local_roles__['{0}_advisers'.format(financial_group_uids[0])],
                         ['Reader', ])

        # now, corner case
        # first item with given finance advice is 'returned' in a meeting
        # new item is accepted and returned in a second meeting
        # item sent to council should keep advisers access
        self.changeUser('siteadmin')
        predecessors[0].getParentNode().manage_delObjects(ids=[predecessors[0].getId(), ])
        predecessors[1].getParentNode().manage_delObjects(ids=[predecessors[1].getId(), ])
        self.changeUser('pmManager')
        self.do(item, 'backToItemFrozen')
        self.do(item, 'return')
        self.assertEqual(item.query_state(), 'returned')
        newItem = item.get_successors()[0]
        self.assertEqual(newItem.adapted().getItemWithFinanceAdvice(), item)
        # right accept_and_return newItem
        meeting2 = self.create('Meeting')
        self.presentItem(newItem)
        self.decideMeeting(meeting2)
        self.do(newItem, 'accept_and_return')
        self.assertEqual(newItem.query_state(), 'accepted_and_returned')
        predecessors = newItem.get_successors()
        self.assertEqual(len(predecessors), 2)
        self.assertEqual(predecessors[0].__ac_local_roles__['{0}_advisers'.format(financial_group_uids[0])],
                         ['Reader', ])
        self.assertEqual(predecessors[1].__ac_local_roles__['{0}_advisers'.format(financial_group_uids[0])],
                         ['Reader', ])

        # still works after an _updateAdvices
        self.changeUser('siteadmin')
        self.tool.update_all_local_roles()
        self.changeUser('pmManager')
        self.assertEqual(predecessors[0].__ac_local_roles__['{0}_advisers'.format(financial_group_uids[0])],
                         ['Reader', ])
        self.assertEqual(predecessors[1].__ac_local_roles__['{0}_advisers'.format(financial_group_uids[0])],
                         ['Reader', ])

    def test_FinanceAdvisersAccessToManuallyLinkedItems(self):
        """Finance adviser have access to every items that are manually linked
           to an item they give advice on."""
        item, advice = self._setupCollegeItemWithFinanceAdvice()
        # create a new item the finance group has no access to
        self.changeUser('pmCreator1')
        item2 = self.create('MeetingItem')
        # 'pmFinController' may access item but not item2
        self.changeUser('pmFinController')
        self.assertTrue(self.hasPermission(View, item))
        self.assertFalse(self.hasPermission(View, item2))
        # now link item to item2, as finance advice was asked on item, access to item2 is provided
        item.setManuallyLinkedItems([item2.UID(), ])
        item._update_after_edit()
        self.assertEqual(self.request.get('manuallyLinkedItems_newUids'), [item2.UID(), ])
        self.assertEqual(item.getManuallyLinkedItems(), [item2])
        self.assertEqual(item2.getManuallyLinkedItems(), [item])
        self.assertTrue(self.hasPermission(View, item))
        self.assertTrue(self.hasPermission(View, item2))

        # if link to item2 is broken, access also is also removed
        item.setManuallyLinkedItems([])
        item._update_after_edit()
        self.assertEqual(item.getManuallyLinkedItems(), [])
        self.assertEqual(item2.getManuallyLinkedItems(), [])
        self.assertTrue(self.hasPermission(View, item))
        self.assertFalse(self.hasPermission(View, item2))

        # access is shared accross linked items only if finance adviser
        # has really access to an item, aka item was set to proposed_to_finance_waiting_advices once at least
        self.changeUser('pmCreator1')
        item1FinanceNeverAccessed = self.create('MeetingItem')
        financial_group_uids = self.tool.finance_group_uids()
        item1FinanceNeverAccessed.setFinanceAdvice(financial_group_uids[0])
        item1FinanceNeverAccessed._update_after_edit()
        item2FinanceNeverAccessed = self.create('MeetingItem')
        item2FinanceNeverAccessed._update_after_edit()
        self.changeUser('pmFinController')
        self.assertFalse(self.hasPermission(View, item1FinanceNeverAccessed))
        self.assertFalse(self.hasPermission(View, item2FinanceNeverAccessed))
        item1FinanceNeverAccessed.setManuallyLinkedItems([item2FinanceNeverAccessed.UID(), ])
        item1FinanceNeverAccessed._update_after_edit()
        # still not accessible
        self.assertFalse(self.hasPermission(View, item1FinanceNeverAccessed))
        self.assertFalse(self.hasPermission(View, item2FinanceNeverAccessed))
        # right, now propose it to finance
        self.changeUser('pmManager')
        self.proposeItem(item1FinanceNeverAccessed)
        self.do(item1FinanceNeverAccessed, 'wait_advices_from_proposed_to_director')
        # both item are accessible
        self.changeUser('pmFinController')
        self.assertTrue(self.hasPermission(View, item1FinanceNeverAccessed))
        self.assertTrue(self.hasPermission(View, item2FinanceNeverAccessed))

        # complex case, link a third item and unlink item1FinanceNeverAccessed
        self.changeUser('pmCreator1')
        item3 = self.create('MeetingItem')
        item1FinanceNeverAccessed.setManuallyLinkedItems(
            [item2FinanceNeverAccessed.UID(), item3.UID()])
        item1FinanceNeverAccessed._update_after_edit()
        # for now, 3 are accessible
        self.changeUser('pmFinController')
        self.assertTrue(self.hasPermission(View, item1FinanceNeverAccessed))
        self.assertTrue(self.hasPermission(View, item2FinanceNeverAccessed))
        self.assertTrue(self.hasPermission(View, item3))
        # remove item1FinanceNeverAccessed, the only item with finance advice
        item3.setManuallyLinkedItems([item2FinanceNeverAccessed.UID()])
        item3._update_after_edit()
        # item1FinanceNeverAccessed alone
        self.assertEqual(item1FinanceNeverAccessed.getManuallyLinkedItems(), [])
        self.assertEqual(item2FinanceNeverAccessed.getManuallyLinkedItems(), [item3])
        self.assertEqual(item3.getManuallyLinkedItems(), [item2FinanceNeverAccessed])
        # only item1FinanceNeverAccessed remains visible by 'pmFinController'
        self.assertTrue(self.hasPermission(View, item1FinanceNeverAccessed))
        self.assertFalse(self.hasPermission(View, item2FinanceNeverAccessed))
        self.assertFalse(self.hasPermission(View, item3))

        # link all together again and test when removing item3
        item2FinanceNeverAccessed.setManuallyLinkedItems(
            [item1FinanceNeverAccessed.UID(), item3.UID()])
        item2FinanceNeverAccessed._update_after_edit()
        # for now, 3 are accessible
        self.changeUser('pmFinController')
        self.assertTrue(self.hasPermission(View, item1FinanceNeverAccessed))
        self.assertTrue(self.hasPermission(View, item2FinanceNeverAccessed))
        self.assertTrue(self.hasPermission(View, item3))
        item2FinanceNeverAccessed.setManuallyLinkedItems([item1FinanceNeverAccessed.UID()])
        item2FinanceNeverAccessed._update_after_edit()
        self.assertTrue(self.hasPermission(View, item1FinanceNeverAccessed))
        self.assertTrue(self.hasPermission(View, item2FinanceNeverAccessed))
        self.assertFalse(self.hasPermission(View, item3))

        # link item4 to item3 then item3 to item1FinanceNeverAccessed
        # all 4 items should be accessible
        self.changeUser('pmCreator1')
        item4 = self.create('MeetingItem')
        item3.setManuallyLinkedItems(
            [item4.UID()])
        item3._update_after_edit()
        self.changeUser('pmFinController')
        self.assertTrue(self.hasPermission(View, item1FinanceNeverAccessed))
        self.assertTrue(self.hasPermission(View, item2FinanceNeverAccessed))
        self.assertFalse(self.hasPermission(View, item3))
        self.assertFalse(self.hasPermission(View, item4))
        item3.setManuallyLinkedItems(
            [item4.UID(), item1FinanceNeverAccessed.UID()])
        item3._update_after_edit()
        self.assertTrue(self.hasPermission(View, item1FinanceNeverAccessed))
        self.assertTrue(self.hasPermission(View, item2FinanceNeverAccessed))
        self.assertTrue(self.hasPermission(View, item3))
        self.assertTrue(self.hasPermission(View, item4))

    def test_CollegeShortcutProcess(self):
        '''
        The items cannot be send anymore to group without at least one user
        in it. There is also shortcut for the three types of reviewers who
        don't have to do the whole validation process but can send
        directly to the role above.
        '''
        cfg = self.meetingConfig
        cfgId = cfg.getId()
        self._enableField('category')
        pg = self.portal.portal_groups
        darGroup = pg.getGroupById(self.developers_administrativereviewers)
        darMembers = darGroup.getMemberIds()
        dirGroup = pg.getGroupById(self.developers_internalreviewers)
        dirMembers = dirGroup.getMemberIds()
        # Give the creator role to all reviewers as they will have to create items.
        self.changeUser('admin')
        dcGroup = pg.getGroupById(self.developers_creators)
        dcGroup.addMember('pmAdminReviewer1')
        dcGroup.addMember('pmInternalReviewer1')
        dcGroup.addMember('pmReviewer1')

        # pmCreator1 creates an item
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem', title='The first item')
        # pmCreator may only 'proposeToAdministrativeReviewer'
        self.assertEqual(self.transitions(item), ['proposeToAdministrativeReviewer'])
        self._checkItemWithoutCategory(item, item.getCategory())
        # if there is no administrative reviewer, a creator can send the item
        # directly to internal reviewer.
        self._removeAllMembers(darGroup, darMembers)
        self.assertEqual(self.transitions(item), ['proposeToInternalReviewer'])
        self._checkItemWithoutCategory(item, item.getCategory())
        # if there is neither administrative nor internal reviewer, a creator
        # can send the item directly to director.
        self._removeAllMembers(dirGroup, dirMembers)
        self.assertEqual(self.transitions(item), ['proposeToDirector'])
        self._checkItemWithoutCategory(item, item.getCategory())
        # if there is an administrative reviewer but no internal reviewer, the
        # creator may only send the item to administative reviewer.
        self._addAllMembers(darGroup, darMembers)
        self.assertEqual(self.transitions(item), ['proposeToAdministrativeReviewer'])
        self._checkItemWithoutCategory(item, item.getCategory())
        self._addAllMembers(dirGroup, dirMembers)

        # A creator can ask for advices if an advice is required.
        self.vendors.item_advice_states = ('%s__state__itemcreated_waiting_advices' % cfgId, )
        item.setOptionalAdvisers((self.vendors_uid, ))
        item._update_after_edit()
        self.assertEqual(self.transitions(item), ['proposeToAdministrativeReviewer',
                                                  'wait_advices_from_itemcreated'])
        self._checkItemWithoutCategory(item, item.getCategory())
        self.do(item, 'wait_advices_from_itemcreated')
        # The user is not forced to give a normal advice and can propose to
        # administrative reviewer.
        self.assertEqual(self.transitions(item),
                         ['backTo_itemcreated_from_waiting_advices',
                          'backTo_proposed_to_administrative_reviewer_from_waiting_advices'])
        # If there is no administrative reviewer, the user can send the item to
        # internal reviewer.
        self._removeAllMembers(darGroup, darMembers)
        self.assertEqual(self.transitions(item),
                         ['backTo_itemcreated_from_waiting_advices',
                          'backTo_proposed_to_internal_reviewer_from_waiting_advices'])
        # If there are neither administrative nor internal reviewer, allow to
        # send directly to direction.
        self._removeAllMembers(dirGroup, dirMembers)
        self.assertEqual(self.transitions(item),
                         ['backTo_itemcreated_from_waiting_advices',
                          'backTo_proposed_to_director_from_waiting_advices'])
        self._addAllMembers(darGroup, darMembers)
        self._addAllMembers(dirGroup, dirMembers)
        self.do(item, 'backTo_itemcreated_from_waiting_advices')
        # Remove the advice for the tests below.
        item.setOptionalAdvisers(())
        item._update_after_edit()

        # an administrative reviewer can send an item in creation directly to
        # the internal reviewer.
        self.changeUser('pmAdminReviewer1')
        self.assertEqual(self.transitions(item),
                         ['proposeToAdministrativeReviewer',
                          'proposeToInternalReviewer'])
        self._checkItemWithoutCategory(item, item.getCategory())
        # if there is no internal reviewer, an administrative reviewer can only
        # send the item to director.
        self._removeAllMembers(dirGroup, dirMembers)
        self.assertEqual(self.transitions(item),
                         ['proposeToAdministrativeReviewer', 'proposeToDirector'])
        self._checkItemWithoutCategory(item, item.getCategory())
        self._addAllMembers(dirGroup, dirMembers)
        # an item which is proposed to administrative reviewer can be send to
        # internal reviewer by an administrative reviewer.
        self.changeUser('pmCreator1')
        self.do(item, 'proposeToAdministrativeReviewer')
        self.changeUser('pmAdminReviewer1')
        self.assertEqual(self.transitions(item), ['backToItemCreated',
                                                  'proposeToInternalReviewer'])
        # if there is no internal reviewer, an administrative reviewer can only
        # send the item to director.
        self._removeAllMembers(dirGroup, dirMembers)
        self.assertEqual(self.transitions(item), ['backToItemCreated',
                                                  'proposeToDirector'])
        self._addAllMembers(dirGroup, dirMembers)
        self.do(item, 'backToItemCreated')

        # An administrative reviewer can ask for advices if an advice is required.
        item.setOptionalAdvisers((self.vendors_uid, ))
        item._update_after_edit()
        self.assertEqual(self.transitions(item),
                         ['proposeToAdministrativeReviewer',
                          'proposeToInternalReviewer',
                          'wait_advices_from_itemcreated'])
        self._checkItemWithoutCategory(item, item.getCategory())
        self.do(item, 'wait_advices_from_itemcreated')
        # The user is not forced to wait for a normal advice and can propose to
        # internal reviewer.
        self.assertEqual(self.transitions(item),
                         ['backTo_itemcreated_from_waiting_advices',
                          'backTo_proposed_to_administrative_reviewer_from_waiting_advices',
                          'backTo_proposed_to_internal_reviewer_from_waiting_advices'])
        # If there is no internal reviewer, the user can send the item to director.
        self._removeAllMembers(dirGroup, dirMembers)
        self.assertEqual(self.transitions(item),
                         ['backTo_itemcreated_from_waiting_advices',
                          'backTo_proposed_to_administrative_reviewer_from_waiting_advices',
                          'backTo_proposed_to_director_from_waiting_advices'])
        self._addAllMembers(dirGroup, dirMembers)
        self.do(item, 'backTo_itemcreated_from_waiting_advices')
        # Remove the advice for the tests below.
        item.setOptionalAdvisers(())
        item._update_after_edit()

        # an internal reviewer can propose an item in creation directly
        # to the direction.
        self.changeUser('pmInternalReviewer1')
        self.assertEqual(self.transitions(item),
                         ['proposeToAdministrativeReviewer',
                          'proposeToDirector',
                          'proposeToInternalReviewer'])
        self._checkItemWithoutCategory(item, item.getCategory())

        # An internal reviewer can ask for advices if an advice is required.
        item.setOptionalAdvisers((self.vendors_uid, ))
        item._update_after_edit()
        self.assertEqual(self.transitions(item),
                         ['proposeToAdministrativeReviewer',
                          'proposeToDirector',
                          'proposeToInternalReviewer',
                          'wait_advices_from_itemcreated'])
        self._checkItemWithoutCategory(item, item.getCategory())
        self.do(item, 'wait_advices_from_itemcreated')
        # The user is not forced to wait for a normal advice and can propose to
        # director.
        self.assertEqual(self.transitions(item),
                         ['backTo_itemcreated_from_waiting_advices',
                          'backTo_proposed_to_administrative_reviewer_from_waiting_advices',
                          'backTo_proposed_to_director_from_waiting_advices',
                          'backTo_proposed_to_internal_reviewer_from_waiting_advices'])
        self.do(item, 'backTo_itemcreated_from_waiting_advices')
        # Remove the advice for the tests below.
        item.setOptionalAdvisers(())
        item._update_after_edit()

        # An internal reviewer can ask an advice to internal reviewer when the
        # item is in creation.
        self.developers.item_advice_states = (
            '%s__state__proposed_to_internal_reviewer_waiting_advices' % cfgId, )
        item.setOptionalAdvisers((self.developers_uid, ))
        item._update_after_edit()
        self.changeUser('pmInternalReviewer1')
        self.assertIn(
            'wait_advices_from_itemcreated__to__proposed_to_internal_reviewer_waiting_advices',
            self.transitions(item))
        # An internal reviewer can send an item from administrative reviewer to
        # director but can also ask an advice to internal reviewer.
        self.changeUser('pmCreator1')
        self.do(item, 'proposeToAdministrativeReviewer')
        self.changeUser('pmInternalReviewer1')
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'proposeToDirector',
                          'proposeToInternalReviewer',
                          'wait_advices_from_proposed_to_administrative_reviewer'])
        self.do(item, 'backToItemCreated')

        # a reviewer can send an item to director, aka himself
        self.changeUser('pmReviewer1')
        self.assertEqual(self.transitions(item),
                         ['proposeToAdministrativeReviewer',
                          'proposeToDirector',
                          'proposeToInternalReviewer',
                          'wait_advices_from_itemcreated__to__proposed_to_internal_reviewer_waiting_advices'])
        self._checkItemWithoutCategory(item, item.getCategory())

        # A reviewer can ask for advices if an advice is required.
        item.setOptionalAdvisers((self.vendors_uid, ))
        item._update_after_edit()
        self.assertEqual(self.transitions(item),
                         ['proposeToAdministrativeReviewer',
                          'proposeToDirector',
                          'proposeToInternalReviewer',
                          'wait_advices_from_itemcreated'])
        self._checkItemWithoutCategory(item, item.getCategory())
        self.do(item, 'wait_advices_from_itemcreated')
        # The user is not forced to wait for a normal advice and can propose to
        # director.
        self.assertEqual(self.transitions(item),
                         ['backTo_itemcreated_from_waiting_advices',
                          'backTo_proposed_to_administrative_reviewer_from_waiting_advices',
                          'backTo_proposed_to_director_from_waiting_advices',
                          'backTo_proposed_to_internal_reviewer_from_waiting_advices'])
        self.do(item, 'backTo_itemcreated_from_waiting_advices')
        # Remove the advice for the tests below.
        item.setOptionalAdvisers(())
        item._update_after_edit()

        # A director can send an item from administrative reviewer to director.
        self.changeUser('pmCreator1')
        self.do(item, 'proposeToAdministrativeReviewer')
        self.changeUser('pmReviewer1')
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'proposeToDirector',
                          'proposeToInternalReviewer'])
        # A director can send an item from internal reviewer to director.
        self.changeUser('pmAdminReviewer1')
        self.do(item, 'proposeToInternalReviewer')
        self.changeUser('pmReviewer1')
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'backToProposedToAdministrativeReviewer',
                          'proposeToDirector'])
        self.do(item, 'backToProposedToAdministrativeReviewer')
        self.do(item, 'backToItemCreated')

        # A director can validate or send the item back to the first state with
        # user in it. As there is an internal reviewer, the item can be sent
        # back to him.
        self.do(item, 'proposeToDirector')
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'backToProposedToAdministrativeReviewer',
                          'backToProposedToInternalReviewer',
                          'validate'])
        # If there is no internal reviewer, allow to send the item back to
        # administrative reviewer.
        self._removeAllMembers(dirGroup, dirMembers)
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'backToProposedToAdministrativeReviewer',
                          'validate'])
        # If there is neither internal nor administrative reviewer, allow to
        # send the item back to creation.
        self._removeAllMembers(darGroup, darMembers)
        self.assertEqual(self.transitions(item), ['backToItemCreated',
                                                  'validate'])
        self._addAllMembers(darGroup, darMembers)
        self._addAllMembers(dirGroup, dirMembers)
        # Send the item back to internal reviewer.
        self.do(item, 'backToProposedToInternalReviewer')
        # Internal reviewer is able to propose to director, send the item back
        # to creator or to administrative reviewer.
        self.changeUser('pmInternalReviewer1')
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'backToProposedToAdministrativeReviewer',
                          'proposeToDirector'])
        # If there is no administrative reviewer, allow the item to be sent
        # back to creation.
        self._removeAllMembers(darGroup, darMembers)
        self.assertEqual(self.transitions(item), ['backToItemCreated',
                                                  'proposeToDirector'])

    def _checkItemWithoutCategory(self, item, originalCategory):
        '''Make sure that an item without category cannot be sent to anybody.'''
        actions_panel = item.restrictedTraverse('@@actions_panel')
        rendered_actions_panel = actions_panel()
        item.setCategory('')
        item._update_after_edit()
        self.assertTrue(not self.transitions(item))
        actions_panel._transitions = None
        no_category_rendered_actions_panel = actions_panel()
        self.assertNotEqual(no_category_rendered_actions_panel, rendered_actions_panel)
        item.setCategory(originalCategory)

    def test_RestrictedPowerObserversMayNotAccessLateItemsInCouncilUntilDecided(self):
        """Finance adviser have still access to items linked to
           an item they give advice on.
           This is the case for 'returned' items and items sent to Council."""
        # not 'late' items are viewable by restricted power observers
        cfg2 = self.meetingConfig2
        self.setMeetingConfig(cfg2.getId())
        groupId = get_plone_group_id(cfg2.getId(), 'restrictedpowerobservers')
        self.changeUser('pmManager')
        item = self.create('MeetingItem')
        item2 = self.create('MeetingItem')
        meeting = self.create('Meeting')
        self.presentItem(item)
        self.freezeMeeting(meeting)
        item2.setPreferredMeeting(meeting.UID())
        item2._update_after_edit()
        self.presentItem(item2)
        # item is 'normal' and item2 is 'late'
        self.assertEqual(item.getListType(), 'normal')
        self.assertEqual(item2.getListType(), 'late')
        self.assertEqual(item.query_state(), 'itemfrozen')
        self.assertEqual(item2.query_state(), 'itemfrozen')
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

    def test_StateSentToCouncilEmergency(self):
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
        item._update_after_edit()
        self.assertNotIn('sendToCouncilEmergency',
                         self.transitions(item))
        # ask emergency for sending to Council
        item.setOtherMeetingConfigsClonableToEmergency((cfg2Id, ))
        item._update_after_edit()
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
        def _check_access_council_item(councilItem):
            """ """
            self.assertEqual(councilItem.getProposingGroup(), self.developers_uid)
            # users have Contributor role as decision annex are addable in every states
            self.assertEqual(councilItem.__ac_local_roles__[self.developers_creators],
                             ['Reader', 'Contributor'])
            self.assertEqual(councilItem.__ac_local_roles__[self.developers_observers],
                             ['Reader'])
            self.assertEqual(councilItem.__ac_local_roles__[self.developers_administrativereviewers],
                             ['Reader', 'Contributor'])
            self.assertEqual(councilItem.__ac_local_roles__[self.developers_internalreviewers],
                             ['Reader', 'Contributor'])
            self.assertEqual(councilItem.__ac_local_roles__[self.developers_reviewers],
                             ['Reader', 'Contributor'])

        self.changeUser('admin')
        # add finance groups
        self._createFinanceGroups()
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        cfg2 = self.meetingConfig2
        cfg2Id = cfg2.getId()
        self._enableField('category', cfg=cfg2, enable=False)
        cfg = self.meetingConfig
        cfgId = cfg.getId()
        self._enableField('category', cfg=cfg2, enable=False)
        cfg2.setInsertingMethodsOnAddItem(({'insertingMethod': 'on_proposing_groups',
                                            'reverse': '0'},))
        cfg2.setMeetingConfigsToCloneTo(({'meeting_config': cfgId,
                                          'trigger_workflow_transitions_until': '__nothing__'},))
        cfg2.setItemAutoSentToOtherMCStates(('delayed', 'returned', ))

        self.changeUser('pmCreator1')
        # create meetingFolder so item may be sent to Council
        self.getMeetingFolder(cfg2)
        # send a college item to council and delay this council item
        # in the college
        data = {'otherMeetingConfigsClonableToFieldLabelForCouncil': COUNCIL_LABEL,
                'otherMeetingConfigsClonableToPrivacy': ('meeting-config-council', ),
                'otherMeetingConfigsClonableTo': ('meeting-config-council', )}
        collegeItem = self.create('MeetingItem', **data)
        financial_group_uids = self.tool.finance_group_uids()
        collegeItem.setFinanceAdvice(financial_group_uids[0])
        self.proposeItem(collegeItem)

        self.changeUser('pmManager')
        collegeMeeting = self.create('Meeting')
        self.do(collegeItem, 'wait_advices_from_proposed_to_director')
        self._giveFinanceAdvice(collegeItem, financial_group_uids[0])
        self.presentItem(collegeItem)
        self.closeMeeting(collegeMeeting)
        councilItem = collegeItem.getItemClonedToOtherMC(cfg2Id)
        # test that every suffixes have access to the Council item
        _check_access_council_item(councilItem)

        # in the council
        # use groups as categories
        self.setMeetingConfig(cfg2Id)
        councilMeeting = self.create('Meeting')
        self.presentItem(councilItem)
        _check_access_council_item(councilItem)
        self.decideMeeting(councilMeeting)
        _check_access_council_item(councilItem)
        return collegeItem, councilItem, collegeMeeting, councilMeeting

    def test_CouncilItemSentToCollegeWhenDelayed(self):
        """While an item in the council is set to 'delayed', it is sent
           in 'itemcreated' state back to the College and ready to process
           back to the council."""
        self._enableField('otherMeetingConfigsClonableToFieldLabelForCouncil')
        cfg = self.meetingConfig
        cfgId = cfg.getId()
        cfg2 = self.meetingConfig2
        cfg2Id = cfg2.getId()
        collegeItem, councilItem, collegeMeeting, councilMeeting = self._setupCollegeItemSentToCouncil()
        self.do(councilItem, 'delay')

        # access for observer
        self.changeUser('pmObserver1')
        self.assertTrue(self.hasPermission(View, councilItem))

        backCollegeItem = councilItem.getItemClonedToOtherMC(cfgId)
        self.assertEqual(backCollegeItem.getLabelForCouncil(), '')
        self.assertEqual(backCollegeItem.getOtherMeetingConfigsClonableToFieldLabelForCouncil(),
                         COUNCIL_LABEL)
        self.assertEqual(backCollegeItem.getOtherMeetingConfigsClonableTo(),
                         ('meeting-config-council', ))
        self.assertIn(cfg2Id, backCollegeItem.getOtherMeetingConfigsClonableTo())

        # it is sent back in "itemcreated" state and finance advice does not follow
        financial_group_uids = self.tool.finance_group_uids()
        self.assertEqual(backCollegeItem.getFinanceAdvice(), financial_group_uids[0])
        self.assertEqual(backCollegeItem.query_state(), 'itemcreated')
        self.assertEqual(backCollegeItem.adapted().getItemWithFinanceAdvice(), backCollegeItem)

    def test_CouncilItemSentToCollegeWhenReturned(self):
        """While an item in the council is set to 'delayed', it is sent
           in 'validated' state back to the College and ready to process
           back to the council."""
        self._enableField('otherMeetingConfigsClonableToFieldLabelForCouncil')
        cfg = self.meetingConfig
        cfgId = cfg.getId()
        cfg2 = self.meetingConfig2
        cfg2Id = cfg2.getId()
        collegeItem, councilItem, collegeMeeting, councilMeeting = self._setupCollegeItemSentToCouncil()
        # change proposingGroup to 'vendors' so we test that item is correctly validated
        # even if it is not accessible during the process when in it 'itemcreated'
        councilItem.setProposingGroup(self.vendors_uid)
        councilItem._update_after_edit()
        self.do(councilItem, 'return')
        backCollegeItem = councilItem.getItemClonedToOtherMC(cfgId)
        self.assertEqual(backCollegeItem.getLabelForCouncil(), '')
        self.assertEqual(backCollegeItem.getOtherMeetingConfigsClonableToFieldLabelForCouncil(),
                         COUNCIL_LABEL)
        self.assertEqual(backCollegeItem.getOtherMeetingConfigsClonableTo(),
                         ('meeting-config-council', ))
        self.assertIn(cfg2Id, backCollegeItem.getOtherMeetingConfigsClonableTo())

        # it is sent back in "validated" state and finance advice does follow
        financial_group_uids = self.tool.finance_group_uids()
        self.assertEqual(backCollegeItem.getFinanceAdvice(), financial_group_uids[0])
        self.assertEqual(backCollegeItem.query_state(), 'validated')
        self.assertEqual(backCollegeItem.adapted().getItemWithFinanceAdvice(), collegeItem)

    def test_ItemSentToCouncilWhenDuplicatedAndLinkKept(self):
        """Make sure that an item that is 'duplicateAndKeepLink' is sent to Council
           no matter state of linked item, and no matter linked item has already been sent."""
        cfg2 = self.meetingConfig2
        cfg2Id = cfg2.getId()
        self.changeUser('pmManager')
        meeting = self.create('Meeting')
        item = self.create('MeetingItem')
        item.setOtherMeetingConfigsClonableTo((cfg2Id, ))
        self.presentItem(item)
        self.decideMeeting(meeting)
        self.do(item, 'accept_and_return')
        # item has been sent
        self.assertTrue(item.getItemClonedToOtherMC(cfg2Id))

        # now check that a duplicatedAndKeepLink item is sent also
        form = item.restrictedTraverse('@@item_duplicate_form').form_instance
        form.update()
        data = {'keep_link': True, 'annex_ids': [], 'annex_decision_ids': []}
        duplicatedItem = form._doApply(data)
        linkedItems = duplicatedItem.getManuallyLinkedItems()
        self.assertEqual(len(linkedItems), 1)
        self.assertEqual(linkedItems[0].query_state(), 'accepted_and_returned')
        self.backToState(meeting, 'created')
        self.presentItem(duplicatedItem)
        self.decideMeeting(meeting)
        self.do(duplicatedItem, 'accept')
        self.assertTrue(duplicatedItem.getItemClonedToOtherMC(cfg2Id))

    def test_CouncilItemDeletedIfCollegeItemIsNotAccepted(self):
        """As items are sent to Council when 'itemfrozen', if a College item is finally
           not accepted, accepted_but_modified or accepted_and_returned,
           delete the Council item that was sent."""
        cfg = self.meetingConfig
        self._enableField('category', enable=False)
        cfg2 = self.meetingConfig2
        cfg2Id = cfg2.getId()
        cfg.setMeetingConfigsToCloneTo(({'meeting_config': cfg2Id,
                                         'trigger_workflow_transitions_until': '__nothing__'},))
        cfg.setItemAutoSentToOtherMCStates(('accepted', 'accepted_and_returned',
                                            'accepted_but_modified', 'itemfrozen', ))

        self.changeUser('pmManager')
        item = self.create('MeetingItem')
        item.setOtherMeetingConfigsClonableTo((cfg2Id, ))
        item2 = self.create('MeetingItem')
        item2.setOtherMeetingConfigsClonableTo((cfg2Id, ))
        item3 = self.create('MeetingItem')
        item3.setOtherMeetingConfigsClonableTo((cfg2Id, ))
        item4 = self.create('MeetingItem')
        item4.setOtherMeetingConfigsClonableTo((cfg2Id, ))
        item5 = self.create('MeetingItem')
        item5.setOtherMeetingConfigsClonableTo((cfg2Id, ))
        meeting = self.create('Meeting')
        self.presentItem(item)
        self.presentItem(item2)
        self.presentItem(item3)
        self.presentItem(item4)
        self.presentItem(item5)
        self.freezeMeeting(meeting)
        # item was sent to Council
        self.assertTrue(item.getItemClonedToOtherMC(cfg2Id))
        self.assertTrue(item2.getItemClonedToOtherMC(cfg2Id))
        self.decideMeeting(meeting)

        # test transitions that will NOT delete the item in the Council
        for tr in ('accept', 'accept_but_modify', 'accept_and_return'):
            self.do(item, tr)
            # still left in the Council
            self.assertTrue(item.getItemClonedToOtherMC(cfg2Id))
            # back to 'itemfrozen'
            self.do(item, 'backToItemFrozen')

        # delay the College item, it will automatically delete the Council item
        self.do(item2, 'delay')
        self.assertFalse(item2.getItemClonedToOtherMC(cfg2Id))
        # but original delay action was kept, the item was duplicated in the College
        backRefs = item2.get_successors()
        self.assertTrue(len(backRefs) == 1 and backRefs[0].portal_type == item2.portal_type)

        # mark_not_applicable the College item, it will automatically delete the Council item
        self.do(item3, 'mark_not_applicable')
        self.assertFalse(item3.getItemClonedToOtherMC(cfg2Id))
        # no more backRefs
        self.assertFalse(item3.get_successors())

        # refuse the College item, it will automatically delete the Council item
        self.do(item4, 'refuse')
        self.assertFalse(item4.getItemClonedToOtherMC(cfg2Id))
        # no more backRefs
        self.assertFalse(item4.get_successors())

        # return the College item, it will automatically delete the Council item
        self.do(item5, 'return')
        self.assertFalse(item5.getItemClonedToOtherMC(cfg2Id))
        # but original delay action was kept, the item was duplicated in the College
        backRefs = item5.get_successors()
        self.assertTrue(len(backRefs) == 1 and backRefs[0].portal_type == item5.portal_type)

    def test_CreatorMayAskAdviceOnlyIfRelevant(self):
        """MeetingMember may only set item to 'itemcreated_waiting_advices' if there
           are actually advices to ask, so if at least one of the asked advices may be
           given in state 'itemcreated_waiting_advices'."""
        cfg = self.meetingConfig
        cfgId = cfg.getId()
        # advices are giveable in states '_waiting_advices'
        cfg.itemAdviceStates = ('itemcreated_waiting_advices',
                                'proposed_to_internal_reviewer_waiting_advices')
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        item.setOptionalAdvisers((self.vendors_uid, ))
        item._update_after_edit()
        # for now this advice may be asked
        self.assertFalse(self.vendors.item_advice_states)
        self.assertIn('wait_advices_from_itemcreated', self.transitions(item))
        # now restrict 'vendors' item_advice_states to 'proposed_to_internal_reviewer_waiting_advices'
        self.vendors.item_advice_states = (
            '%s__state__proposed_to_internal_reviewer_waiting_advices' % cfgId, )
        notify(ObjectModifiedEvent(self.vendors))
        self.assertNotIn('wait_advices_from_itemcreated', self.transitions(item))
        # if another advice is asked, then the transition shows up
        self.assertFalse(self.developers.item_advice_states)
        item.setOptionalAdvisers((self.vendors_uid, self.developers_uid))
        item._update_after_edit()
        self.assertIn('wait_advices_from_itemcreated', self.transitions(item))

        # now test when item is 'proposed_to_internal_reviewer_waiting_advices'
        self.changeUser('pmReviewer1')
        item.setOptionalAdvisers((self.vendors_uid, ))
        item._update_after_edit()
        self.changeUser('siteadmin')
        self.do(item, 'proposeToAdministrativeReviewer')
        self.do(item, 'proposeToInternalReviewer')
        self.changeUser('pmInternalReviewer1')
        # advice may be asked
        self.assertIn('wait_advices_from_proposed_to_internal_reviewer', self.transitions(item))
        self.vendors.item_advice_states = ('%s__state__itemcreated_waiting_advices' % cfgId, )
        notify(ObjectModifiedEvent(self.vendors))
        # advice may not be asked anymore
        self.assertNotIn('wait_advices_from_proposed_to_internal_reviewer', self.transitions(item))

    def test_TreasuryPowerAdviserMayBeAskedAgain(self):
        """TREASURY_GROUP_ID is power observer and may give advice when the
           item is accepted/accepted_but_modified.  Internal reviewer and directors
           of the proposing group may ask this advice again."""
        self.changeUser('siteadmin')
        self._createFinanceGroups()
        cfg = self.meetingConfig
        # add pmCreator2 to the TREASURY_GROUP_ID_advisers group
        treasury_org = self.own_org.get(TREASURY_GROUP_ID)
        treasury_org_uid = treasury_org.UID()
        group = get_plone_group(treasury_org_uid, 'advisers')
        group.addMember('pmCreator2')
        # make TREASURY_GROUP_ID a power adviser group
        cfg.setPowerAdvisersGroups((treasury_org_uid, ))

        # create an item and make it 'accepted'
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        self.changeUser('pmManager')
        meeting = self.create('Meeting')
        self.presentItem(item)
        self.closeMeeting(meeting)
        self.assertEqual(item.query_state(), 'accepted')
        self.changeUser('pmCreator2')
        advice = createContentInContainer(
            item,
            item.adapted()._advicePortalTypeForAdviser(treasury_org_uid),
            **{'advice_group': treasury_org_uid,
               'advice_type': u'negative',
               'advice_comment': richtextval(u'My negative comment')})
        # ask advice again
        self.changeUser('pmCreator1')
        # not able as not internalreviewer/reviewer
        self.assertFalse(item.adapted().mayAskAdviceAgain(advice))
        self.changeUser('pmInternalReviewer1')
        self.assertTrue(item.adapted().mayAskAdviceAgain(advice))
        self.changeUser('pmReviewer1')
        self.assertTrue(item.adapted().mayAskAdviceAgain(advice))

        # and advice may be actually asked again
        changeView = advice.restrictedTraverse('@@change-advice-asked-again')
        changeView()
        self.assertEqual(advice.advice_type, 'asked_again')

        # advice may be given again
        self.changeUser('pmCreator2')
        self.assertEqual(item.getAdvicesGroupsInfosForUser(),
                         ([], [treasury_org_uid]))
        advice.advice_type = 'positive'
        advice.advice_comment = richtextval(u'My positive comment')
        notify(ObjectModifiedEvent(advice))
        self.assertEqual(item.adviceIndex[treasury_org_uid]['type'], 'positive')

    def test_BourgmestreAdministrativeProcess(self):
        '''This test the Bourgmestre workflows administrative part :
           - itemcreated;
           - proposed_to_administrative_reviewer;
           - proposed_to_internal_reviewer;
           - proposed_to_director;
           - proposed_to_director_waiting_advices.'''
        self.setUpBourgmestreConfig()
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        # pmCreator1 may only propose to administrative reviewer
        self.assertEqual(self.transitions(item),
                         ['proposeToAdministrativeReviewer'])
        self.do(item, 'proposeToAdministrativeReviewer')
        # pmCreator1 can no more edit item but can still view it
        self._check_access(item, write=False)
        self._check_access(item, userIds=['pmObserver1'], read=True, write=False)
        self.changeUser('pmAdminReviewer1')
        # pmAdminReviewer1 may access item and edit it
        self._check_access(item)
        self._check_access(item, userIds=['pmObserver1'], read=True, write=False)
        # he may send the item back to the pmCreator1 or send it to the internal reviewer
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated', 'proposeToInternalReviewer', ])
        self.do(item, 'proposeToInternalReviewer')
        # pmAdminReviewer1 can no more edit item but can still view it
        self._check_access(item, write=False)
        self._check_access(item, userIds=['pmObserver1'], read=True, write=False)
        # pmInternalReviewer1 may access item and edit it
        self.changeUser('pmInternalReviewer1')
        self._check_access(item)
        # he may send the item back to the administrative reviewer or send it to the reviewer (director)
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'backToProposedToAdministrativeReviewer',
                          'proposeToDirector', ])
        self.do(item, 'proposeToDirector')
        # pmInternalReviewer1 can no more edit item but can still view it
        self._check_access(item, write=False)
        self._check_access(item, userIds=['pmObserver1'], read=True, write=False)
        # pmReviewer1 (director) may access item and edit it
        self.changeUser('pmReviewer1')
        self._check_access(item)
        self._check_access(item, userIds=['pmObserver1'], read=True, write=False)
        # he may send the item back to the internal reviewer, or send it to
        # general manager (proposeToGeneralManager).
        # wait_advices_from_proposed_to_director is only available if advices are asked
        self.assertEqual(self.transitions(item),
                         ['backToItemCreated',
                          'backToProposedToAdministrativeReviewer',
                          'backToProposedToInternalReviewer',
                          'proposeToGeneralManager'])
        # ask advices
        item.setOptionalAdvisers((self.vendors_uid, ))
        item._update_after_edit()
        self.do(item, 'wait_advices_from_proposed_to_director')
        self.assertEqual(item.query_state(), 'proposed_to_director_waiting_advices')
        # director may take item back
        self.assertEqual(self.transitions(item), ['backTo_proposed_to_director_from_waiting_advices'])
        self._check_access(item, userIds=['pmObserver1'], read=True, write=False)
        # when item is back to the director, the wf_down_finances icon is not displayed
        # this is only displayed in College
        self.do(item, 'backTo_proposed_to_director_from_waiting_advices')
        self.assertFalse('wf_down_finances.png' in item.getPrettyLink())

    def test_BourgmestreDirectionProcess(self):
        """ """
        '''This test the Bourgmestre workflows direction part :
           - proposed_to_general_manager;
           - proposed_to_cabinet_manager;
           - proposed_to_cabinet_reviewer;
           - validated.'''
        self.setUpBourgmestreConfig()
        self.changeUser('pmManager')
        item = self.create('MeetingItem')
        # unable to trigger proposeToCabinetReviewer
        self.assertEqual(self.transitions(item),
                         ['proposeToAdministrativeReviewer',
                          'proposeToCabinetManager',
                          'proposeToCabinetReviewer',
                          'proposeToDirector',
                          'proposeToGeneralManager',
                          'proposeToInternalReviewer',
                          'validate'])
        # propose to general manager and check access
        self.do(item, 'proposeToAdministrativeReviewer')
        self.do(item, 'proposeToInternalReviewer')
        self.do(item, 'proposeToDirector')
        self.do(item, 'proposeToGeneralManager')
        self.assertEqual(item.query_state(), 'proposed_to_general_manager')

        # here, proposingGroup still have View access and GENERAL_MANAGER_GROUP_ID
        # can manage the item
        self._check_access(
            item, ('pmCreator1', 'pmAdminReviewer1', 'pmInternalReviewer1', 'pmReviewer1'),
            write=False)
        self._check_access(item, userIds=['pmObserver1'], read=False, write=False)

        self.changeUser('generalManager')
        self._check_access(item)

        # propose to cabinet, proposingGroup and GENERAL_MANAGER_GROUP_ID will have read access
        # and BOURGMESTRE_GROUP_ID creators will have modify access
        self.do(item, 'proposeToCabinetManager')
        self.assertEqual(item.query_state(), 'proposed_to_cabinet_manager')
        self._check_access(item, userIds=['pmObserver1'], read=False, write=False)
        # general manager may see, not edit
        self._check_access(item, write=False)
        # proposingGroup may see, not edit
        self.changeUser('pmCreator1')
        self._check_access(item, write=False)
        # bourgmestreManager have view/edit on item
        self.changeUser('bourgmestreManager')
        self._check_access(item)
        # from this point, item may be sent back to director or sent to cabinet reviewer
        self.assertEqual(
            self.transitions(item),
            ['backToProposedToDirector', 'backToProposedToGeneralManager', 'proposeToCabinetReviewer'])

        # propose to cabinet reviewer, bourgmestreReviewer will have read/edit
        # and others (proposingGroup, general manager, bourgmestreManager) will have read access
        self.do(item, 'proposeToCabinetReviewer')
        self.assertFalse(self.transitions(item))
        self.assertEqual(item.query_state(), 'proposed_to_cabinet_reviewer')
        self._check_access(
            item, ('pmCreator1', 'pmAdminReviewer1', 'pmInternalReviewer1',
                   'pmReviewer1', 'generalManager', 'bourgmestreManager'),
            write=False)
        self._check_access(item, userIds=['pmObserver1'], read=False, write=False)
        # bourgmestre reviewer has the hand
        self.changeUser('bourgmestreReviewer')
        self.assertEqual(
            self.transitions(item),
            ['backToProposedToCabinetManager', 'backToProposedToDirector', 'validate'])
        self._check_access(item)

    def test_BourgmestreCreatedItemDirectlySendableToCabinetReviewerByCabinetManager(self):
        """ """
        self.setUpBourgmestreConfig()
        self.changeUser('bourgmestreManager')
        # proposingGroup will be 'bourgmestre'
        item = self.create('MeetingItem')
        self.assertEqual(self.transitions(item), ['proposeToCabinetReviewer', 'proposeToDirector'])
        self.do(item, 'proposeToCabinetReviewer')
        # in this case, bourgmestre group correctly gets access on item
        # actually it will get the 'Reader' role in addition to Meeting roles
        self._check_access(item, ('generalManager', 'bourgmestreManager'), write=False)
        self._check_access(item, ('bourgmestreReviewer', ))

    def test_BourgmestreMeetingProcess(self):
        """ """
        '''This test the Bourgmestre workflows final part :
           - validated;
           - presented;
           - decided.'''
        self.setUpBourgmestreConfig()
        self.changeUser('pmManager')
        item = self.create('MeetingItem')

        # validate item
        self.do(item, 'proposeToAdministrativeReviewer')
        self.do(item, 'proposeToInternalReviewer')
        self.do(item, 'proposeToDirector')
        self.do(item, 'proposeToGeneralManager')
        self.changeUser('generalManager')
        self.do(item, 'proposeToCabinetManager')
        self.changeUser('bourgmestreManager')
        self.do(item, 'proposeToCabinetReviewer')
        self.changeUser('bourgmestreReviewer')
        self.do(item, 'validate')

        # from here, MeetingManagers have the hand and others are looking
        self._check_access(
            item, ('pmCreator1', 'pmAdminReviewer1', 'pmInternalReviewer1',
                   'pmReviewer1', 'generalManager', 'bourgmestreManager',
                   'bourgmestreReviewer'),
            write=False)
        self.changeUser('pmMeetingManagerBG')
        self._check_access(item)
        self._check_access(item, userIds=['pmObserver1'], read=True, write=False)
        self.assertEqual(
            self.transitions(item),
            ['backToProposedToCabinetReviewer', 'backToProposedToDirector'])
        meeting = self.create('Meeting')
        self.do(item, 'present')
        self.assertEqual(meeting.get_items()[0], item)
        self._check_access(
            item, ('pmCreator1', 'pmAdminReviewer1', 'pmInternalReviewer1',
                   'pmReviewer1', 'generalManager', 'bourgmestreManager',
                   'bourgmestreReviewer'),
            write=False)
        self._check_access(item)
        self._check_access(item, userIds=['pmObserver1'], read=True, write=False)

        # only MeetingManager may decide
        for userId in (
                'pmCreator1', 'pmAdminReviewer1', 'pmInternalReviewer1', 'pmReviewer1',
                'generalManager', 'bourgmestreManager', 'bourgmestreReviewer'):
            self.changeUser(userId)
            self.assertFalse(self.transitions(item))

        self.changeUser('pmMeetingManagerBG')
        self.assertEqual(
            self.transitions(item),
            ['accept', 'accept_but_modify', 'backToValidated',
             'delay', 'mark_not_applicable', 'refuse', 'return_to_proposing_group'])
        # if item is delayed, it is duplicated in it's initial_state
        self.do(item, 'delay')
        self._check_access(
            item, ('pmCreator1', 'pmAdminReviewer1', 'pmInternalReviewer1',
                   'pmReviewer1', 'generalManager', 'bourgmestreManager',
                   'bourgmestreReviewer', 'pmMeetingManagerBG'),
            write=False)
        self._check_access(item, userIds=['pmObserver1'], read=True, write=False)
        self.assertEqual(item.query_state(), 'delayed')
        cloned_item = item.get_successors()[0]
        self.assertEqual(cloned_item.query_state(), 'itemcreated')
        # only viewable by proposingGroup members
        self._check_access(
            cloned_item, ('generalManager', 'bourgmestreManager', 'bourgmestreReviewer',
                          'pmAdminReviewer1', 'pmInternalReviewer1'),
            read=False, write=False)
        self._check_access(cloned_item, userIds=('pmCreator1', ))
        self._check_access(cloned_item, userIds=('pmReviewer1', ), read=True, write=False)

    def test_BourgmestreItemDataHistorizedWhenProposedToCabinetManager(self):
        """ """
        self.setUpBourgmestreConfig()
        self.changeUser('pmManager')
        item = self.create('MeetingItem')
        item.setTitle('Sample title')
        item.setDescription('<p>Sample description</p>')
        item.setMotivation('<p>Sample motivation</p>')
        item.setDecision('<p>Sample decision</p>')

        # propose to general manager
        self.do(item, 'proposeToAdministrativeReviewer')
        self.do(item, 'proposeToInternalReviewer')
        self.do(item, 'proposeToDirector')
        self.do(item, 'proposeToGeneralManager')

        self.changeUser('generalManager')
        self.assertFalse(hasattr(item, ITEM_MAIN_INFOS_HISTORY))
        self.do(item, 'proposeToCabinetManager')
        main_infos_history_adapter = getAdapter(item, IImioHistory, 'main_infos')
        last_event = getLastAction(main_infos_history_adapter)
        self.assertEqual(last_event['action'], 'historize_main_infos')
        self.assertEqual(last_event['actor'], self.member.getId())
        self.assertEqual(last_event['comments'], 'historize_main_infos_comments')
        self.assertEqual(last_event['action'], 'historize_main_infos')
        self.assertEqual(last_event['action'], 'historize_main_infos')
        self.assertEqual(last_event['historized_data'], main_item_data(item))
        self.assertEqual(last_event['type'], 'main_infos')

        # the @@main_infos_history_view
        infos_view = getMultiAdapter((item, self.portal.REQUEST), name='main_infos_history_view')
        self.assertTrue(item.Title() in infos_view(int(last_event['time'])))
        self.assertEqual(infos_view.historized_data, last_event['historized_data'])

    def test_BourgmestreMayNotViewRelevantHistoryEvents(self):
        """A user in an administrative group will only see administrative related transitions,
           a user in a cabinet will only see cabinet related transitions."""
        self.setUpBourgmestreConfig()
        self.changeUser('pmManager')
        item = self.create('MeetingItem')
        item.setTitle('Sample title')
        item.setDescription('<p>Sample description</p>')
        item.setMotivation('<p>Sample motivation</p>')
        item.setDecision('<p>Sample decision</p>')
        self.create('Meeting')

        # full WF as siteadmin
        self.changeUser('siteadmin')
        self.do(item, 'proposeToAdministrativeReviewer')
        self.do(item, 'proposeToInternalReviewer')
        self.do(item, 'proposeToDirector')
        self.do(item, 'proposeToGeneralManager')
        self.do(item, 'backToProposedToDirector')
        self.do(item, 'proposeToGeneralManager')
        self.do(item, 'proposeToCabinetManager')
        # special backToProposedToDirector that will be viewable by cabinet members
        self.do(item, 'backToProposedToDirector')
        self.do(item, 'proposeToGeneralManager')
        self.do(item, 'proposeToCabinetManager')
        self.do(item, 'proposeToCabinetReviewer')
        self.do(item, 'validate')
        self.do(item, 'present')
        self.do(item, 'accept')
        view = getMultiAdapter((item, self.request), name='contenthistory')
        actions = [event['action'] for event in view.getHistory()]
        # every actions as siteadmin
        self.assertEqual(
            actions,
            ['accept', 'present', 'validate', 'proposeToCabinetReviewer', 'historize_main_infos',
             'proposeToCabinetManager', 'proposeToGeneralManager', 'backToProposedToDirector', 'historize_main_infos',
             'proposeToCabinetManager', 'proposeToGeneralManager', 'backToProposedToDirector',
             'proposeToGeneralManager', 'proposeToDirector', 'proposeToInternalReviewer',
             'proposeToAdministrativeReviewer', None])
        # as member of the proposingGroup
        self.changeUser('pmCreator1')
        view = getMultiAdapter((item, self.request), name='contenthistory')
        actions = [event['action'] for event in view.getHistory()]
        self.assertEqual(
            actions,
            ['accept', 'present', 'historize_main_infos', 'proposeToGeneralManager', 'backToProposedToDirector',
             'historize_main_infos', 'proposeToGeneralManager', 'backToProposedToDirector', 'proposeToGeneralManager',
             'proposeToDirector', 'proposeToInternalReviewer', 'proposeToAdministrativeReviewer', None])
        # as cabinet mamager/reviewer
        for cabinet_member_id in ('bourgmestreManager', 'bourgmestreReviewer'):
            self.changeUser(cabinet_member_id)
            view = getMultiAdapter((item, self.request), name='contenthistory')
            actions = [event['action'] for event in view.getHistory()]
            self.assertEqual(
                actions,
                ['accept', 'present', 'validate', 'proposeToCabinetReviewer', 'historize_main_infos',
                 'proposeToCabinetManager', 'backToProposedToDirector', 'historize_main_infos',
                 'proposeToCabinetManager', None])

    def test_BourgmestreItemsToValidateSearches(self):
        """Test that items to validate searches work correctly for the BG workflow."""
        self.setUpBourgmestreConfig()
        cfg = self.meetingConfig

        # create items in various reviewer states
        self.changeUser('pmManager')

        item = self.create('MeetingItem')
        self.create('Meeting')

        sc_uid = org_id_to_uid('sc')
        bg_uid = org_id_to_uid('bourgmestre')
        # check reviewProcessInfo
        self.changeUser('pmManager')
        self.assertEqual(reviewProcessInfo(item)(),
                         '{0}__reviewprocess__itemcreated'.format(self.developers_uid))
        self.do(item, 'proposeToAdministrativeReviewer')
        self.assertEqual(reviewProcessInfo(item)(),
                         '{0}__reviewprocess__proposed_to_administrative_reviewer'.format(self.developers_uid))
        self.do(item, 'proposeToInternalReviewer')
        self.assertEqual(reviewProcessInfo(item)(),
                         '{0}__reviewprocess__proposed_to_internal_reviewer'.format(self.developers_uid))
        self.do(item, 'proposeToDirector')
        self.assertEqual(reviewProcessInfo(item)(),
                         '{0}__reviewprocess__proposed_to_director'.format(self.developers_uid))
        self.do(item, 'proposeToGeneralManager')
        self.assertEqual(reviewProcessInfo(item)(),
                         '{0}__reviewprocess__proposed_to_general_manager'.format(sc_uid))
        self.changeUser('generalManager')
        self.do(item, 'proposeToCabinetManager')
        self.assertEqual(reviewProcessInfo(item)(),
                         '{0}__reviewprocess__proposed_to_cabinet_manager'.format(bg_uid))
        self.changeUser('bourgmestreManager')
        self.do(item, 'proposeToCabinetReviewer')
        self.assertEqual(reviewProcessInfo(item)(),
                         '{0}__reviewprocess__proposed_to_cabinet_reviewer'.format(bg_uid))
        self.changeUser('bourgmestreReviewer')
        self.do(item, 'validate')
        self.assertEqual(reviewProcessInfo(item)(),
                         '{0}__reviewprocess__validated'.format(self.developers_uid))
        self.changeUser('pmManager')
        self.do(item, 'present')
        self.assertEqual(reviewProcessInfo(item)(),
                         '{0}__reviewprocess__presented'.format(self.developers_uid))
        self.do(item, 'accept')
        self.assertEqual(reviewProcessInfo(item)(),
                         '{0}__reviewprocess__accepted'.format(self.developers_uid))

        my_reviewer_groups = getAdapter(
            cfg, ICompoundCriterionFilter, name='items-to-validate-of-my-reviewer-groups')
        highest_hierarchic_level = getAdapter(
            cfg, ICompoundCriterionFilter, name='items-to-validate-of-highest-hierarchic-level')
        every_reviewer_levels_and_lower = getAdapter(
            cfg, ICompoundCriterionFilter, name='items-to-validate-of-every-reviewer-levels-and-lower-levels')

        # administrative reviewer
        self.changeUser('pmAdminReviewer1')
        self.assertEqual(
            my_reviewer_groups.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_administrative_reviewer'.format(
                    self.developers_uid)]}})
        self.assertEqual(
            highest_hierarchic_level.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_administrative_reviewer'.format(
                    self.developers_uid)]}})
        # it works because finally the only value taken into account is the
        # ...__reviewprocess__proposed_to_administrative_reviewer the other value will
        # never match as an item with ...__reviewprocess__proposed_to_cabinet_manager
        # the first part is the UID of the BG organization which 'pmAdminReviewer1' is not member of
        self.assertEqual(
            every_reviewer_levels_and_lower.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': [
                    '{0}__reviewprocess__proposed_to_administrative_reviewer'.format(
                        self.developers_uid),
                    '{0}__reviewprocess__proposed_to_cabinet_manager'.format(
                        self.developers_uid), ]}})

        # internal reviewer
        cleanRamCacheFor('Products.PloneMeeting.adapters.query_itemstovalidateofmyreviewergroups')
        cleanRamCacheFor('Products.PloneMeeting.adapters.query_itemstovalidateofhighesthierarchiclevel')
        cleanRamCacheFor('Products.PloneMeeting.adapters.query_itemstovalidateofeveryreviewerlevelsandlowerlevels')
        self.changeUser('pmInternalReviewer1')
        self.assertEqual(
            my_reviewer_groups.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_internal_reviewer'.format(
                    self.developers_uid)]}})
        self.assertEqual(
            highest_hierarchic_level.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_internal_reviewer'.format(
                    self.developers_uid)]}})
        self.assertEqual(
            every_reviewer_levels_and_lower.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': [
                    '{0}__reviewprocess__proposed_to_administrative_reviewer'.format(
                        self.developers_uid),
                    '{0}__reviewprocess__proposed_to_cabinet_manager'.format(
                        self.developers_uid),
                    '{0}__reviewprocess__proposed_to_internal_reviewer'.format(
                        self.developers_uid), ]}})

        # director
        cleanRamCacheFor('Products.PloneMeeting.adapters.query_itemstovalidateofmyreviewergroups')
        cleanRamCacheFor('Products.PloneMeeting.adapters.query_itemstovalidateofhighesthierarchiclevel')
        cleanRamCacheFor('Products.PloneMeeting.adapters.query_itemstovalidateofeveryreviewerlevelsandlowerlevels')
        self.changeUser('pmReviewerLevel2')
        # the searches of a user of a '_reviewers' group will also search for
        # 'developers__reviewprocess__proposed_to_general_manager' and
        # 'developers__reviewprocess__proposed_to_cabinet_reviewer'
        # but this will not match any item as when an item is 'proposed_to_general_manager'
        # the reviewProcessInfo will be 'sc__reviewprocess__proposed_to_general_manager'
        self.assertEqual(
            my_reviewer_groups.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_director'.format(self.developers_uid),
                          '{0}__reviewprocess__proposed_to_general_manager'.format(self.developers_uid),
                          '{0}__reviewprocess__proposed_to_cabinet_reviewer'.format(self.developers_uid),
                          ]}})
        self.assertEqual(
            highest_hierarchic_level.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_director'.format(self.developers_uid),
                          '{0}__reviewprocess__proposed_to_general_manager'.format(self.developers_uid),
                          '{0}__reviewprocess__proposed_to_cabinet_reviewer'.format(self.developers_uid),
                          ]}})
        self.assertEqual(
            every_reviewer_levels_and_lower.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_administrative_reviewer'.format(self.developers_uid),
                          '{0}__reviewprocess__proposed_to_cabinet_manager'.format(self.developers_uid),
                          '{0}__reviewprocess__proposed_to_cabinet_reviewer'.format(self.developers_uid),
                          '{0}__reviewprocess__proposed_to_director'.format(self.developers_uid),
                          '{0}__reviewprocess__proposed_to_general_manager'.format(self.developers_uid),
                          '{0}__reviewprocess__proposed_to_internal_reviewer'.format(self.developers_uid),
                          ]}})

        # general manager
        cleanRamCacheFor('Products.PloneMeeting.adapters.query_itemstovalidateofmyreviewergroups')
        cleanRamCacheFor('Products.PloneMeeting.adapters.query_itemstovalidateofhighesthierarchiclevel')
        cleanRamCacheFor('Products.PloneMeeting.adapters.query_itemstovalidateofeveryreviewerlevelsandlowerlevels')
        self.changeUser('generalManager')
        self.assertEqual(
            my_reviewer_groups.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_director'.format(sc_uid),
                          '{0}__reviewprocess__proposed_to_general_manager'.format(sc_uid),
                          '{0}__reviewprocess__proposed_to_cabinet_reviewer'.format(sc_uid),
                          ]}})
        self.assertEqual(
            highest_hierarchic_level.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_director'.format(sc_uid),
                          '{0}__reviewprocess__proposed_to_general_manager'.format(sc_uid),
                          '{0}__reviewprocess__proposed_to_cabinet_reviewer'.format(sc_uid),
                          ]}})
        self.assertEqual(
            every_reviewer_levels_and_lower.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_administrative_reviewer'.format(sc_uid),
                          '{0}__reviewprocess__proposed_to_cabinet_manager'.format(sc_uid),
                          '{0}__reviewprocess__proposed_to_cabinet_reviewer'.format(sc_uid),
                          '{0}__reviewprocess__proposed_to_director'.format(sc_uid),
                          '{0}__reviewprocess__proposed_to_general_manager'.format(sc_uid),
                          '{0}__reviewprocess__proposed_to_internal_reviewer'.format(sc_uid),
                          ]}})

        # cabinet manager
        cleanRamCacheFor('Products.PloneMeeting.adapters.query_itemstovalidateofmyreviewergroups')
        cleanRamCacheFor('Products.PloneMeeting.adapters.query_itemstovalidateofhighesthierarchiclevel')
        cleanRamCacheFor('Products.PloneMeeting.adapters.query_itemstovalidateofeveryreviewerlevelsandlowerlevels')
        self.changeUser('bourgmestreManager')
        self.assertEqual(
            my_reviewer_groups.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_cabinet_manager'.format(bg_uid)]}})
        self.assertEqual(
            highest_hierarchic_level.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_cabinet_manager'.format(bg_uid)]}})
        self.assertEqual(
            every_reviewer_levels_and_lower.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_cabinet_manager'.format(bg_uid)]}})

        # cabinet reviewer
        cleanRamCacheFor('Products.PloneMeeting.adapters.query_itemstovalidateofmyreviewergroups')
        cleanRamCacheFor('Products.PloneMeeting.adapters.query_itemstovalidateofhighesthierarchiclevel')
        cleanRamCacheFor('Products.PloneMeeting.adapters.query_itemstovalidateofeveryreviewerlevelsandlowerlevels')
        self.changeUser('bourgmestreReviewer')
        self.assertEqual(
            my_reviewer_groups.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_director'.format(bg_uid),
                          '{0}__reviewprocess__proposed_to_general_manager'.format(bg_uid),
                          '{0}__reviewprocess__proposed_to_cabinet_reviewer'.format(bg_uid),
                          ]}})
        self.assertEqual(
            highest_hierarchic_level.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_director'.format(bg_uid),
                          '{0}__reviewprocess__proposed_to_general_manager'.format(bg_uid),
                          '{0}__reviewprocess__proposed_to_cabinet_reviewer'.format(bg_uid),
                          ]}})
        self.assertEqual(
            every_reviewer_levels_and_lower.query,
            {'portal_type': {
                'query': 'MeetingItemBourgmestre'},
             'reviewProcessInfo': {
                'query': ['{0}__reviewprocess__proposed_to_administrative_reviewer'.format(bg_uid),
                          '{0}__reviewprocess__proposed_to_cabinet_manager'.format(bg_uid),
                          '{0}__reviewprocess__proposed_to_cabinet_reviewer'.format(bg_uid),
                          '{0}__reviewprocess__proposed_to_director'.format(bg_uid),
                          '{0}__reviewprocess__proposed_to_general_manager'.format(bg_uid),
                          '{0}__reviewprocess__proposed_to_internal_reviewer'.format(bg_uid),
                          ]}})

    def _check_confidential_annex_access(self, item, userIds=[], access=True):
        """ """
        original_user_id = self.member.getId()
        # no userIds means use current user id
        if not userIds:
            userIds = [original_user_id]
        for userId in userIds:
            self.changeUser(userId)
            if access:
                self.assertTrue(get_categorized_elements(item))
            else:
                self.assertFalse(get_categorized_elements(item))
        self.changeUser(original_user_id)

    def test_BourgmestreConfidentialAnnexes(self):
        """Confidential annexes should be visible by every groups of the validation
           process (proposingGroup, groupManagingItem (DG, BG)."""
        self.setUpBourgmestreConfig()

        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        # enable annex confidentiality
        annex_config = get_config_root(item)
        annex_group = get_group(annex_config, item)
        annex_group.confidentiality_activated = True
        annex = self.addAnnex(item, confidential=True)
        self.assertTrue(annex.confidential)
        self.assertTrue(get_categorized_elements(item)[0]['confidential'])

        # check every access while item evolve in the WF
        self._check_confidential_annex_access(item)
        self.do(item, 'proposeToAdministrativeReviewer')
        self._check_confidential_annex_access(
            item,
            userIds=['pmCreator1', 'pmAdminReviewer1'])
        self.changeUser('pmAdminReviewer1')
        self.do(item, 'proposeToInternalReviewer')
        self._check_confidential_annex_access(
            item,
            userIds=['pmCreator1', 'pmAdminReviewer1', 'pmInternalReviewer1'])

        self.changeUser('pmInternalReviewer1')
        self.do(item, 'proposeToDirector')
        self._check_confidential_annex_access(
            item,
            userIds=['pmCreator1', 'pmAdminReviewer1', 'pmInternalReviewer1',
                     'pmReviewer1'])

        self.changeUser('pmReviewer1')
        self.do(item, 'proposeToGeneralManager')
        self._check_confidential_annex_access(
            item,
            userIds=['pmCreator1', 'pmAdminReviewer1', 'pmInternalReviewer1',
                     'pmReviewer1', 'generalManager'])

        self.changeUser('generalManager')
        self.do(item, 'proposeToCabinetManager')

        self._check_confidential_annex_access(
            item,
            userIds=['pmCreator1', 'pmAdminReviewer1', 'pmInternalReviewer1',
                     'pmReviewer1', 'generalManager', 'bourgmestreManager'])

        self.changeUser('bourgmestreManager')
        self.do(item, 'proposeToCabinetReviewer')
        self._check_confidential_annex_access(
            item,
            userIds=['pmCreator1', 'pmAdminReviewer1', 'pmInternalReviewer1',
                     'pmReviewer1', 'generalManager', 'bourgmestreManager',
                     'bourgmestreReviewer'])

        self.changeUser('bourgmestreReviewer')
        self.do(item, 'validate')
        self._check_confidential_annex_access(
            item,
            userIds=['pmCreator1', 'pmAdminReviewer1', 'pmInternalReviewer1',
                     'pmReviewer1', 'generalManager', 'bourgmestreManager',
                     'bourgmestreReviewer'])
