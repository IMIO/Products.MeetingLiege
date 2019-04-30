# -*- coding: utf-8 -*-

from copy import deepcopy
from Products.PloneMeeting.profiles.testing import import_data as pm_import_data
from Products.PloneMeeting.config import DEFAULT_LIST_TYPES
from Products.PloneMeeting.profiles import MeetingConfigDescriptor
from Products.PloneMeeting.profiles import UserDescriptor


# Users and groups -------------------------------------------------------------
pmFinController = UserDescriptor('pmFinController', [])
pmFinControllerCompta = UserDescriptor('pmFinControllerCompta', [])
pmFinReviewer = UserDescriptor('pmFinReviewer', [])
pmFinManager = UserDescriptor('pmFinManager', [])
pmMeetingManagerBG = UserDescriptor('pmMeetingManagerBG', [], email="pm_mm_bg@plone.org", fullname='M. PMMMBG')
pmAdminReviewer1 = UserDescriptor('pmAdminReviewer1', [])
pmInternalReviewer1 = UserDescriptor('pmInternalReviewer1', [])

developers = pm_import_data.developers
pmManager = pm_import_data.pmManager
pmReviewerLevel1 = pm_import_data.pmReviewerLevel1
developers.administrativereviewers.append(pmAdminReviewer1)
developers.administrativereviewers.append(pmManager)
developers.administrativereviewers.append(pmReviewerLevel1)
developers.internalreviewers.append(pmInternalReviewer1)
developers.internalreviewers.append(pmManager)

# Meeting configurations -------------------------------------------------------
collegeMeeting = deepcopy(pm_import_data.meetingPma)
collegeMeeting.id = 'meeting-config-college'
collegeMeeting.Title = 'Collège Communal'
collegeMeeting.folderTitle = 'Collège Communal'
collegeMeeting.shortName = 'meeting-config-college'
collegeMeeting.id = 'meeting-config-college'
collegeMeeting.isDefault = True
collegeMeeting.shortName = 'College'
collegeMeeting.usedItemAttributes = ['budgetInfos',
                                     'detailedDescription',
                                     'observations',
                                     'toDiscuss',
                                     'completeness',
                                     'labelForCouncil',
                                     'otherMeetingConfigsClonableToPrivacy',
                                     'archivingRef',
                                     'motivation',
                                     'textCheckList',
                                     'itemIsSigned']
collegeMeeting.itemWorkflow = 'meetingitemcollegeliege_workflow'
collegeMeeting.meetingWorkflow = 'meetingcollegeliege_workflow'
collegeMeeting.itemConditionsInterface = 'Products.MeetingLiege.interfaces.IMeetingItemCollegeLiegeWorkflowConditions'
collegeMeeting.itemActionsInterface = 'Products.MeetingLiege.interfaces.IMeetingItemCollegeLiegeWorkflowActions'
collegeMeeting.meetingConditionsInterface = 'Products.MeetingLiege.interfaces.IMeetingCollegeLiegeWorkflowConditions'
collegeMeeting.meetingActionsInterface = 'Products.MeetingLiege.interfaces.IMeetingCollegeLiegeWorkflowActions'
collegeMeeting.transitionsForPresentingAnItem = ('proposeToAdministrativeReviewer',
                                                 'proposeToInternalReviewer',
                                                 'proposeToDirector',
                                                 'validate',
                                                 'present', )
collegeMeeting.itemAutoSentToOtherMCStates = ('sent_to_council_emergency',
                                              'accepted',
                                              'accepted_but_modified',
                                              'accepted_and_returned',)
collegeMeeting.itemDecidedStates = ['accepted', 'delayed', 'accepted_but_modified', 'pre_accepted']
collegeMeeting.itemPositiveDecidedStates = ['accepted', 'accepted_but_modified']
collegeMeeting.onMeetingTransitionItemTransitionToTrigger = ({'meeting_transition': 'freeze',
                                                              'item_transition': 'itemfreeze'},

                                                             {'meeting_transition': 'decide',
                                                              'item_transition': 'itemfreeze'},

                                                             {'meeting_transition': 'close',
                                                              'item_transition': 'itemfreeze'},
                                                             {'meeting_transition': 'close',
                                                              'item_transition': 'accept'},

                                                             {'meeting_transition': 'backToCreated',
                                                              'item_transition': 'backToPresented'},)
collegeMeeting.itemAdviceStates = ('proposed_to_director')
collegeMeeting.itemAdviceEditStates = ('proposed_to_director', 'validated')
collegeMeeting.itemCopyGroupsStates = ['validated']
collegeMeeting.usedAdviceTypes = ('positive_finance', 'positive_with_remarks_finance',
                                  'negative_finance', 'not_required_finance',
                                  'positive', 'positive_with_remarks', 'negative', 'nil')
# Conseil communal
councilMeeting = deepcopy(pm_import_data.meetingPga)
councilMeeting.id = 'meeting-config-council'
councilMeeting.Title = 'Conseil Communal'
councilMeeting.folderTitle = 'Conseil Communal'
councilMeeting.shortName = 'meeting-config-council'
councilMeeting.id = 'meeting-config-council'
councilMeeting.isDefault = False
councilMeeting.shortName = 'Council'
councilMeeting.usedItemAttributes = ['budgetInfos',
                                     'labelForCouncil',
                                     'observations',
                                     'privacy',
                                     'motivation',
                                     'itemIsSigned']
councilMeeting.itemWorkflow = 'meetingitemcouncilliege_workflow'
councilMeeting.meetingWorkflow = 'meetingcouncilliege_workflow'
councilMeeting.itemConditionsInterface = 'Products.MeetingLiege.interfaces.IMeetingItemCouncilLiegeWorkflowConditions'
councilMeeting.itemActionsInterface = 'Products.MeetingLiege.interfaces.IMeetingItemCouncilLiegeWorkflowActions'
councilMeeting.meetingConditionsInterface = 'Products.MeetingLiege.interfaces.IMeetingCouncilLiegeWorkflowConditions'
councilMeeting.meetingActionsInterface = 'Products.MeetingLiege.interfaces.IMeetingCouncilLiegeWorkflowActions'
councilMeeting.transitionsForPresentingAnItem = ('present', )
councilMeeting.itemDecidedStates = collegeMeeting.itemDecidedStates
councilMeeting.itemPositiveDecidedStates = collegeMeeting.itemPositiveDecidedStates
councilMeeting.onMeetingTransitionItemTransitionToTrigger = ({'meeting_transition': 'freeze',
                                                              'item_transition': 'itemfreeze'},

                                                             {'meeting_transition': 'decide',
                                                              'item_transition': 'itemfreeze'},

                                                             {'meeting_transition': 'close',
                                                              'item_transition': 'itemfreeze'},
                                                             {'meeting_transition': 'close',
                                                              'item_transition': 'accept'},

                                                             {'meeting_transition': 'backToCreated',
                                                              'item_transition': 'backToPresented'},)
councilMeeting.onTransitionFieldTransforms = (
    {'transition': 'present',
     'field_name': 'MeetingItem.decisionEnd',
     'tal_expression': 'python: here.adapted().adaptCouncilItemDecisionEnd()'},)
councilMeeting.itemAdviceStates = ()
councilMeeting.itemAdviceEditStates = ()
councilMeeting.itemAdviceViewStates = ()
councilMeeting.listTypes = DEFAULT_LIST_TYPES + [{'identifier': 'addendum',
                                                  'label': 'Addendum',
                                                  'used_in_inserting_method': ''}, ]
councilMeeting.itemCopyGroupsStates = ['validated']

# Bourgmestre
bourgmestreMeeting = MeetingConfigDescriptor(
    'meeting-config-bourgmestre', 'Bourgmestre', 'Bourgmestre')
bourgmestreMeeting.meetingManagers = ('pmManager', 'pmMeetingManagerBG')
bourgmestreMeeting.assembly = 'Default assembly'
bourgmestreMeeting.signatures = 'Default signatures'
bourgmestreMeeting.certifiedSignatures = [
    {'signatureNumber': '1',
     'name': u'Name1 Name1',
     'function': u'Function1',
     'date_from': '',
     'date_to': ''},
    {'signatureNumber': '2',
     'name': u'Name3 Name4',
     'function': u'Function2',
     'date_from': '',
     'date_to': '',
     }]
bourgmestreMeeting.categories = councilMeeting.categories
bourgmestreMeeting.shortName = 'Bourgmestre'
bourgmestreMeeting.annexTypes = councilMeeting.annexTypes
bourgmestreMeeting.itemAnnexConfidentialVisibleFor = (
    'configgroup_budgetimpacteditors',
    'reader_advices',
    'reader_copy_groups',
    'reader_groupincharge',
    'configgroup_powerobservers',
    'suffix_proposing_group_prereviewers',
    'suffix_proposing_group_internalreviewers',
    'suffix_proposing_group_observers',
    'suffix_proposing_group_reviewers',
    'suffix_proposing_group_creators',
    'suffix_proposing_group_administrativereviewers')

bourgmestreMeeting.itemWorkflow = 'meetingitembourgmestre_workflow'
bourgmestreMeeting.meetingWorkflow = 'meetingbourgmestre_workflow'
bourgmestreMeeting.itemConditionsInterface = \
    'Products.MeetingLiege.interfaces.IMeetingItemBourgmestreWorkflowConditions'
bourgmestreMeeting.itemActionsInterface = \
    'Products.MeetingLiege.interfaces.IMeetingItemBourgmestreWorkflowActions'
bourgmestreMeeting.meetingConditionsInterface = \
    'Products.MeetingLiege.interfaces.IMeetingBourgmestreWorkflowConditions'
bourgmestreMeeting.meetingActionsInterface = \
    'Products.MeetingLiege.interfaces.IMeetingBourgmestreWorkflowActions'
bourgmestreMeeting.transitionsForPresentingAnItem = (
    u'proposeToAdministrativeReviewer',
    u'proposeToInternalReviewer',
    u'proposeToDirector',
    u'proposeToGeneralManager',
    u'proposeToCabinetManager',
    u'proposeToCabinetReviewer',
    u'validate',
    u'present')
bourgmestreMeeting.onMeetingTransitionItemTransitionToTrigger = (
    {'meeting_transition': 'close',
     'item_transition': 'accept'}, )
bourgmestreMeeting.transitionsToConfirm = []
bourgmestreMeeting.meetingTopicStates = ('created', )
bourgmestreMeeting.decisionTopicStates = ('closed', )
bourgmestreMeeting.itemAdviceStates = ('proposed_to_director_waiting_advices', )
bourgmestreMeeting.recordItemHistoryStates = []
bourgmestreMeeting.maxShownMeetings = 5
bourgmestreMeeting.maxDaysDecisions = 60
bourgmestreMeeting.usedItemAttributes = [
    'budgetInfos',
    'observations',
    'privacy',
    'motivation',
    'itemIsSigned']
bourgmestreMeeting.insertingMethodsOnAddItem = (
    {'insertingMethod': 'at_the_end',
     'reverse': '0'}, )
bourgmestreMeeting.useGroupsAsCategories = False
bourgmestreMeeting.useAdvices = True
bourgmestreMeeting.selectableAdvisers = []
bourgmestreMeeting.itemAdviceStates = []
bourgmestreMeeting.itemAdviceEditStates = []
bourgmestreMeeting.itemAdviceViewStates = []
bourgmestreMeeting.itemDecidedStates = [
    'accepted', 'refused', 'delayed', 'marked_not_applicable']
bourgmestreMeeting.itemPowerObserversStates = (
    'presented', 'accepted', 'refused', 'delayed', 'marked_not_applicable')
bourgmestreMeeting.itemRestrictedPowerObserversStates = (
    'presented', 'accepted', 'refused', 'delayed', 'marked_not_applicable')
bourgmestreMeeting.useCopies = True
bourgmestreMeeting.useVotes = False
bourgmestreMeeting.recurringItems = []
bourgmestreMeeting.itemTemplates = []

data = deepcopy(pm_import_data.data)
data.meetingConfigs = (collegeMeeting, councilMeeting, bourgmestreMeeting)
# necessary for testSetup.test_pm_ToolAttributesAreOnlySetOnFirstImportData
data.restrictUsers = False
data.usersOutsideGroups = data.usersOutsideGroups + [pmFinController, pmFinReviewer, pmFinManager, pmMeetingManagerBG]
