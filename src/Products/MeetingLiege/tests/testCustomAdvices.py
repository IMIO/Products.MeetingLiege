# -*- coding: utf-8 -*-
#
# File: testAdvices.py
#
# GNU General Public License (GPL)
#

from imio.helpers.content import richtextval
from plone import api
from plone.dexterity.utils import createContentInContainer
from Products.MeetingLiege.events import _everyAdvicesAreGivenFor
from Products.MeetingLiege.setuphandlers import _configureCollegeCustomAdvisers
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from zope.component import queryUtility
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.interfaces import IVocabularyFactory


class testCustomAdvices(MeetingLiegeTestCase):
    '''Tests various aspects of advices management.
       Advices are enabled for PloneGov Assembly, not for PloneMeeting Assembly.'''

    def test_FinancialManagerMayChangeAdviceDelayWhenAddableOrEditable(self):
        '''Check that a financial manager may still change advice asked to his financial
           group while the advice is still addable or editable.'''
        self.changeUser('admin')
        # add finance groups
        self._createFinanceGroups()
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # ask finance advice and ask advice (set item to 'proposed_to_finance_waiting_advices')
        # not need a finances advice
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='The first item')
        financial_group_uids = self.tool.finance_group_uids()
        item.setFinanceAdvice(financial_group_uids[0])
        item._update_after_edit()
        self.assertTrue(financial_group_uids[0] in item.adviceIndex)
        self.proposeItem(item)
        self.do(item, 'wait_advices_from_proposed_to_director')
        item.setCompleteness('completeness_complete')
        item._update_after_edit()
        # ok, now advice can be given
        # a financial manager may change delays
        self.changeUser('pmFinManager')
        delayView = item.restrictedTraverse('@@advice-available-delays')
        # advice has been asked automatically
        financial_group_uids = self.tool.finance_group_uids()
        isAutomatic = not bool(item.adviceIndex[financial_group_uids[0]]['optional'])
        # advice is addable, delays may be changed
        self.assertTrue(delayView._mayEditDelays(isAutomatic=isAutomatic))
        # add the advice, delay still changeable as advice is editable
        advice = createContentInContainer(
            item,
            'meetingadvicefinances',
            **{'advice_group': financial_group_uids[0],
               'advice_type': u'positive_finance',
               'advice_comment': richtextval(u'My comment finance')})
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
        self.assertFalse(item.adviceIndex[financial_group_uids[0]]['advice_editable'])
        self.assertFalse(delayView._mayEditDelays(isAutomatic=isAutomatic))

    def test_ItemSentBackToAskerWhenEveryAdvicesGiven(self):
        '''Check that, when every advices are given, the item is automatically sent back to 'itemcreated'
           of 'proposed_to_internal_reviewer' depending on which 'waiting advices' state it is.'''
        cfg = self.meetingConfig
        self.changeUser('admin')
        cfg.setUsedAdviceTypes(cfg.getUsedAdviceTypes() + ('asked_again', ))
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
        self._createFinanceGroups()
        _configureCollegeCustomAdvisers(self.portal)
        self._setupFinanceGroups()

        # ask finance advice and vendors advice
        # finance advice is not considered in the case we test here
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem', title='The item')
        financial_group_uids = self.tool.finance_group_uids()
        item.setFinanceAdvice(financial_group_uids[0])
        item.setOptionalAdvisers((self.vendors_uid, ))
        item._update_after_edit()
        self.assertTrue(financial_group_uids[0] in item.adviceIndex)
        self.assertTrue(self.vendors_uid in item.adviceIndex)

        # check when item is 'itemcreated_waiting_advices'
        self._checkItemSentBackToServiceWhenEveryAdvicesGiven(
            item,
            askAdvicesTr='wait_advices_from_itemcreated',
            availableBackTr='backTo_itemcreated_from_waiting_advices',
            returnState='itemcreated')
        # Give to pmInternalReviewer1 the creator role to grant him access to
        # items in creation.
        self.changeUser('admin')
        developers_creators = api.group.get(self.developers_creators)
        developers_creators.addMember('pmInternalReviewer1')

        # now check for 'proposed_to_internal_reviewer_waiting_advices'
        # From item created.
        self.deleteAsManager(item.meetingadvice.UID())
        self.changeUser('pmInternalReviewer1')
        self.assertEqual(item.query_state(), 'itemcreated')
        self._checkItemSentBackToServiceWhenEveryAdvicesGiven(
            item,
            askAdvicesTr='wait_advices_from_itemcreated__to__proposed_to_internal_reviewer_waiting_advices',
            availableBackTr='backTo_proposed_to_internal_reviewer_from_waiting_advices',
            returnState='proposed_to_internal_reviewer',
            askAdvicesTr2='wait_advices_from_proposed_to_internal_reviewer')

        # From proposed to administrative reviewer.
        self.deleteAsManager(item.meetingadvice.UID())
        self.changeUser('pmManager')
        self.do(item, 'backToProposedToAdministrativeReviewer')
        self.changeUser('pmInternalReviewer1')
        self._checkItemSentBackToServiceWhenEveryAdvicesGiven(
            item,
            askAdvicesTr='wait_advices_from_proposed_to_administrative_reviewer',
            availableBackTr='backTo_proposed_to_internal_reviewer_from_waiting_advices',
            returnState='proposed_to_internal_reviewer',
            askAdvicesTr2='wait_advices_from_proposed_to_internal_reviewer')

        # From proposed to internal reviewer.
        self.deleteAsManager(item.meetingadvice.UID())
        self.changeUser('pmInternalReviewer1')
        self._checkItemSentBackToServiceWhenEveryAdvicesGiven(
            item,
            askAdvicesTr='wait_advices_from_proposed_to_internal_reviewer',
            availableBackTr='backTo_proposed_to_internal_reviewer_from_waiting_advices',
            returnState='proposed_to_internal_reviewer')

    def test_BourgmestreItemSentBackToAskerWhenEveryAdvicesGiven(self):
        '''Check that, when every advices are given, the item is automatically
           sent back to 'proposed_to_director'.'''
        self.setUpBourgmestreConfig()

        # vendors advice
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem', title='The item')
        item.setOptionalAdvisers((self.vendors_uid, ))
        self.proposeItem(item)
        self.changeUser('pmReviewer1')

        # check when item is 'itemcreated_waiting_advices'
        self._checkItemSentBackToServiceWhenEveryAdvicesGiven(
            item,
            askAdvicesTr='wait_advices_from_proposed_to_director',
            availableBackTr='backTo_proposed_to_director_from_waiting_advices',
            returnState='proposed_to_director')

    def _checkItemSentBackToServiceWhenEveryAdvicesGiven(self,
                                                         item,
                                                         askAdvicesTr,
                                                         availableBackTr,
                                                         returnState,
                                                         askAdvicesTr2=None):
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
                                 **{'advice_group': self.vendors_uid,
                                    'advice_type': u'positive',
                                    'advice_hide_during_redaction': False,
                                    'advice_comment': richtextval(u'My comment')})
        # directly sent back to service
        self.assertEqual(item.query_state(), returnState)
        self.assertTrue(_everyAdvicesAreGivenFor(item))

        # now add advice as vendors and hide it, advice is considered not given
        self.changeUser('siteadmin')
        item.restrictedTraverse('@@delete_givenuid')(item.meetingadvice.UID())
        self.do(item, askAdvicesTr2 or askAdvicesTr)
        self.changeUser('pmReviewer2')
        advice = createContentInContainer(item,
                                          'meetingadvice',
                                          **{'advice_group': self.vendors_uid,
                                             'advice_type': u'positive',
                                             'advice_hide_during_redaction': True,
                                             'advice_comment': richtextval(u'My comment')})
        # still waiting advices
        self.assertEqual(item.query_state(), '{0}_waiting_advices'.format(returnState))
        self.assertFalse(_everyAdvicesAreGivenFor(item))
        # if we just change 'advice_hide_during_redaction', advice is given and item's sent back
        advice.advice_hide_during_redaction = False
        notify(ObjectModifiedEvent(advice))
        self.assertEqual(item.query_state(), returnState)
        self.assertTrue(_everyAdvicesAreGivenFor(item))

        # now test with 'asked_again'
        self.changeUser(adviceAskerUserId)
        advice.restrictedTraverse('@@change-advice-asked-again')()
        self.assertEqual(advice.advice_type, 'asked_again')
        self.do(item, askAdvicesTr2 or askAdvicesTr)
        self.changeUser('pmReviewer2')
        notify(ObjectModifiedEvent(advice))
        # still waiting advices
        self.assertEqual(item.query_state(), '{0}_waiting_advices'.format(returnState))
        self.assertFalse(_everyAdvicesAreGivenFor(item))
        # change advice_type, it will be sent back then
        advice.advice_type = u'positive'
        notify(ObjectModifiedEvent(advice))
        self.assertEqual(item.query_state(), returnState)
        self.assertTrue(_everyAdvicesAreGivenFor(item))

    def test_AdviceTypeVocabulary(self):
        """'Products.PloneMeeting.content.advice.advice_type_vocabulary' was overrided
           to manage values of finance advice."""
        item, finance_advice = self._setupCollegeItemWithFinanceAdvice()
        self.changeUser('pmManager')
        vocab = queryUtility(IVocabularyFactory,
                             "Products.PloneMeeting.content.advice.advice_type_vocabulary")
        # ask 'vendors' advice on item
        item.setOptionalAdvisers((self.vendors_uid, ))
        item._update_after_edit()
        self.do(item, 'backToProposedToDirector')
        vendors_advice = createContentInContainer(
            item,
            'meetingadvice',
            **{'advice_group': self.vendors_uid,
               'advice_type': u'negative',
               'advice_comment': richtextval(u'<p>My comment vendors</p>'),
               'advice_observations': richtextval(u'<p>My observation vendors</p>')})
        finance_keys = vocab(finance_advice).by_value.keys()
        finance_keys.sort()
        self.assertEqual(finance_keys,
                         ['negative_finance', 'not_required_finance',
                          'positive_finance', 'positive_with_remarks_finance'])
        vendors_keys = vocab(vendors_advice).by_value.keys()
        vendors_keys.sort()
        self.assertEqual(vendors_keys,
                         ['negative', 'nil', 'positive', 'positive_with_remarks'])
