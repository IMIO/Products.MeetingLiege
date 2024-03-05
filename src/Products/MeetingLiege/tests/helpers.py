# -*- coding: utf-8 -*-

from collective.contact.plonegroup.utils import select_org_for_function
from imio.helpers.cache import cleanForeverCache
from imio.helpers.content import richtextval
from plone.dexterity.utils import createContentInContainer
from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.config import PROJECTNAME
from Products.MeetingLiege.profiles.liege import import_data as liege_import_data
from Products.MeetingLiege.setuphandlers import _configureCollegeCustomAdvisers
from Products.PloneMeeting.exportimport.content import ToolInitializer
from Products.PloneMeeting.tests.helpers import PloneMeetingTestingHelpers


class MeetingLiegeTestingHelpers(PloneMeetingTestingHelpers):
    '''Override some values of PloneMeetingTestingHelpers.'''

    TRANSITIONS_FOR_PROPOSING_ITEM_1 = ('proposeToAdministrativeReviewer',
                                        'proposeToInternalReviewer',
                                        'proposeToDirector',)
    TRANSITIONS_FOR_PROPOSING_ITEM_2 = ('proposeToDirector', )
    TRANSITIONS_FOR_PREVALIDATING_ITEM_1 = TRANSITIONS_FOR_PREVALIDATING_ITEM_2 = ('proposeToAdministrativeReviewer',
                                                                                   'proposeToInternalReviewer',
                                                                                   'proposeToDirector')
    TRANSITIONS_FOR_VALIDATING_ITEM_1 = ('proposeToAdministrativeReviewer',
                                         'proposeToInternalReviewer',
                                         'proposeToDirector',
                                         'validate', )
    TRANSITIONS_FOR_VALIDATING_ITEM_2 = ('proposeToDirector',
                                         'validate', )
    TRANSITIONS_FOR_PROPOSING_ITEM_FIRST_LEVEL_1 = TRANSITIONS_FOR_PROPOSING_ITEM_FIRST_LEVEL_2 = (
        'proposeToAdministrativeReviewer', )
    TRANSITIONS_FOR_PRESENTING_ITEM_1 = ('proposeToAdministrativeReviewer',
                                         'proposeToInternalReviewer',
                                         'proposeToDirector',
                                         'validate',
                                         'present', )
    TRANSITIONS_FOR_PRESENTING_ITEM_2 = ('proposeToDirector',
                                         'validate',
                                         'present', )
    BACK_TO_WF_PATH_1 = {
        # MeetingItem
        'itemcreated': ('backToItemFrozen',
                        'backToPresented',
                        'backToValidated',
                        'backToProposedToDirector',
                        'backToProposedToInternalReviewer',
                        'backToProposedToAdministrativeReviewer',
                        'backToItemCreated', ),
        'proposed_to_director': ('backToItemFrozen',
                                 'backToPresented',
                                 'backToValidated',
                                 'backToProposedToDirector',
                                 'backToProposedToInternalReviewer',
                                 'backToProposedToAdministrativeReviewer', ),
        'validated': ('backToItemFrozen',
                      'backToPresented',
                      'backToValidated', )}
    BACK_TO_WF_PATH_2 = {
        'itemcreated': ('backToItemFrozen',
                        'backToPresented',
                        'backToValidated',
                        'backToProposedToDirector',
                        'backToItemCreated', ),
        'validated': ('backToItemFrozen',
                      'backToPresented',
                      'backToValidated', )}

    WF_ITEM_STATE_NAME_MAPPINGS_1 = {'itemcreated': 'itemcreated',
                                     'proposed_first_level': 'proposed_to_director',
                                     'proposed': 'proposed_to_director',
                                     'prevalidated': 'proposed_to_administrative_reviewer',
                                     'validated': 'validated',
                                     'presented': 'presented',
                                     'itemfrozen': 'itemfrozen'}
    WF_ITEM_STATE_NAME_MAPPING_2 = WF_ITEM_STATE_NAME_MAPPINGS_1

    # in which state an item must be after an particular meeting transition?
    ITEM_WF_STATE_AFTER_MEETING_TRANSITION = {'publish_decisions': 'accepted',
                                              'close': 'accepted'}

    def _setupFinanceGroups(self):
        '''Configure finance groups.'''
        # add pmFinController, pmFinReviewer and pmFinManager to advisers and
        # to their respective finance group
        financial_group_uids = self.tool.finance_group_uids()
        self._addPrincipalToGroup('pmFinController', '{0}_advisers'.format(financial_group_uids[0]))
        self._addPrincipalToGroup('pmFinReviewer', '{0}_advisers'.format(financial_group_uids[0]))
        self._addPrincipalToGroup('pmFinManager', '{0}_advisers'.format(financial_group_uids[0]))
        self._addPrincipalToGroup('pmFinController', '{0}_financialcontrollers'.format(financial_group_uids[0]))
        self._addPrincipalToGroup('pmFinReviewer', '{0}_financialreviewers'.format(financial_group_uids[0]))
        self._addPrincipalToGroup('pmFinManager', '{0}_financialmanagers'.format(financial_group_uids[0]))
        self.meetingConfig.setKeepAccessToItemWhenAdvice('is_given')

    def _giveFinanceAdvice(self, item, adviser_group_id):
        """Given an p_item in state 'proposed_to_finance_waiting_advices', give the p_adviser_group_id advice on it."""
        originalUserId = self.member.getId()
        self.changeUser('pmFinController')
        changeCompleteness = item.restrictedTraverse('@@change-item-completeness')
        self.request.set('new_completeness_value', 'completeness_complete')
        self.request.form['form.submitted'] = True
        changeCompleteness()
        advice = createContentInContainer(
            item,
            'meetingadvicefinances',
            **{'advice_group': adviser_group_id,
               'advice_type': u'positive_finance',
               'advice_comment': richtextval(u'<p>My comment finance</p>'),
               'advice_observations': richtextval(u'<p>My observation finance</p>')})
        self.do(advice, 'proposeToFinancialReviewer', comment='My financial controller comment')
        # as finance reviewer
        self.changeUser('pmFinReviewer')
        self.do(advice, 'proposeToFinancialManager', comment='My financial reviewer comment')
        # as finance manager
        self.changeUser('pmFinManager')
        self.do(advice, 'signFinancialAdvice', comment='My financial manager comment')
        self.changeUser(originalUserId)
        return advice

    def _setupCollegeItemWithFinanceAdvice(self, ):
        """Setup, create a College item and give finance advice on it."""
        self.changeUser('admin')
        # add finance groups
        self._createFinanceGroups()
        # configure customAdvisers for 'meeting-config-college'
        _configureCollegeCustomAdvisers(self.portal)
        # define relevant users for finance groups
        self._setupFinanceGroups()

        # first 'return' an item and test
        self.changeUser('pmManager')
        item = self.create('MeetingItem', title='An item with finance advice')
        # ask finance advice and give it
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
            'meetingadvicefinances',
            **{'advice_group': financial_group_uids[0],
               'advice_type': u'positive_finance',
               'advice_comment': richtextval(u'<p>My comment finance</p>'),
               'advice_observations': richtextval(u'<p>My observation finance</p>')})
        self.do(advice, 'proposeToFinancialReviewer', comment='My financial controller comment')
        # as finance reviewer
        self.changeUser('pmFinReviewer')
        self.do(advice, 'proposeToFinancialManager', comment='My financial reviewer comment')
        # as finance manager
        self.changeUser('pmFinManager')
        self.do(advice, 'signFinancialAdvice', comment='My financial manager comment')
        return item, advice

    def _createFinanceGroups(self):
        """
           Create the finance groups.
        """
        context = self.portal.portal_setup._getImportContext('Products.MeetingLiege:testing')
        initializer = ToolInitializer(context, PROJECTNAME)
        org_descriptors = (liege_import_data.dfcompta,
                           liege_import_data.dfcontrol,
                           liege_import_data.dftresor)
        orgs, active_orgs, savedOrgsData = initializer.addOrgs(org_descriptors, defer_data=False)
        for org in orgs:
            org_uid = org.UID()
            self._select_organization(org_uid)
            if org.getId() in FINANCE_GROUP_IDS:
                select_org_for_function(org_uid, 'financialcontrollers')
                select_org_for_function(org_uid, 'financialmanagers')
                select_org_for_function(org_uid, 'financialreviewers')
        # configure especially advisersConfig
        initializer.profileData.advisersConfig = liege_import_data.data.advisersConfig
        initializer._init_tool(force=True)
        # clean forever cache on utils finance_group_uids
        cleanForeverCache()

    def _createRHGroups(self):
        """
           Create the RH groups.
        """
        context = self.portal.portal_setup._getImportContext('Products.MeetingLiege:testing')
        initializer = ToolInitializer(context, PROJECTNAME)
        org_descriptors = (liege_import_data.rhrecr,
                           liege_import_data.rhgestadmin)
        orgs, active_orgs, savedOrgsData = initializer.addOrgs(org_descriptors, defer_data=False)
        for org in orgs:
            org_uid = org.UID()
            self._select_organization(org_uid)
            self._addPrincipalToGroup('pmManager', '{0}_creators'.format(org_uid))
            self._addPrincipalToGroup('pmManager', '{0}_reviewers'.format(org_uid))
        # clean forever cache on utils rh_group_uids
        cleanForeverCache()

    def _setItemToWaitingAdvices(self, item, transition):
        """Setup item so advice may be asked."""
        # "proposed_to_director_waiting_advices" is actually named "proposed_to_finance_waiting_advices"
        values = list(self.vendors.get_item_advice_states())
        if not values:
            # path on MeetingConfig
            values = list(self.meetingConfig.getItemAdviceStates())
            values[0] = values[0].replace('director', 'finance')
            self.meetingConfig.setItemAdviceStates(values)
        else:
            values[0] = values[0].replace('director', 'finance')
            self.vendors.item_advice_states = tuple(values)
        self.do(item, 'wait_advices_from_proposed_to_director')
