# -*- coding: utf-8 -*-

from copy import deepcopy
from Products.MeetingLiege.profiles.liege import import_data as ml_import_data
from Products.MeetingLiege.profiles.zbourgmestre import import_data as bg_import_data
from Products.PloneMeeting.config import DEFAULT_LIST_TYPES
from Products.PloneMeeting.profiles import MeetingConfigDescriptor
from Products.PloneMeeting.profiles import UserDescriptor
from Products.PloneMeeting.profiles.testing import import_data as pm_import_data


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
collegeMeeting.title = 'Collège Communal'
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
                                     'otherMeetingConfigsClonableToPrivacy',
                                     'motivation',
                                     'textCheckList',
                                     'itemIsSigned']
collegeMeeting.itemConditionsInterface = ml_import_data.collegeMeeting.itemConditionsInterface
collegeMeeting.itemActionsInterface = ml_import_data.collegeMeeting.itemActionsInterface
collegeMeeting.meetingConditionsInterface = ml_import_data.collegeMeeting.meetingConditionsInterface
collegeMeeting.meetingActionsInterface = ml_import_data.collegeMeeting.meetingActionsInterface
collegeMeeting.transitionsForPresentingAnItem = ml_import_data.collegeMeeting.transitionsForPresentingAnItem
collegeMeeting.itemWFValidationLevels = ml_import_data.collegeMeeting.itemWFValidationLevels
collegeMeeting.workflowAdaptations = ml_import_data.collegeMeeting.workflowAdaptations
collegeMeeting.itemAutoSentToOtherMCStates = ('sent_to_council_emergency',
                                              'accepted',
                                              'accepted_but_modified',
                                              'accepted_and_returned',)
collegeMeeting.itemDecidedStates = ['accepted', 'delayed', 'accepted_but_modified', 'pre_accepted']
collegeMeeting.itemPositiveDecidedStates = ['accepted', 'accepted_but_modified']
collegeMeeting.itemAdviceStates = ('proposed_to_director')
collegeMeeting.itemAdviceEditStates = ('proposed_to_director', 'validated')
collegeMeeting.itemCopyGroupsStates = ['validated']
collegeMeeting.usedAdviceTypes = ('positive', 'positive_with_remarks', 'negative', 'nil')
# Conseil communal
councilMeeting = deepcopy(pm_import_data.meetingPga)
councilMeeting.id = 'meeting-config-council'
councilMeeting.title = 'Conseil Communal'
councilMeeting.folderTitle = 'Conseil Communal'
councilMeeting.shortName = 'meeting-config-council'
councilMeeting.id = 'meeting-config-council'
councilMeeting.isDefault = False
councilMeeting.shortName = 'Council'
councilMeeting.usedItemAttributes = ['budgetInfos',
                                     'category',
                                     'labelForCouncil',
                                     'observations',
                                     'privacy',
                                     'motivation',
                                     'itemIsSigned',
                                     'copyGroups']
councilMeeting.itemConditionsInterface = ml_import_data.councilMeeting.itemConditionsInterface
councilMeeting.itemActionsInterface = ml_import_data.councilMeeting.itemActionsInterface
councilMeeting.meetingConditionsInterface = ml_import_data.councilMeeting.meetingConditionsInterface
councilMeeting.meetingActionsInterface = ml_import_data.councilMeeting.meetingActionsInterface
councilMeeting.transitionsForPresentingAnItem = ml_import_data.councilMeeting.transitionsForPresentingAnItem
councilMeeting.itemWFValidationLevels = ml_import_data.councilMeeting.itemWFValidationLevels
councilMeeting.workflowAdaptations = ml_import_data.councilMeeting.workflowAdaptations
councilMeeting.itemDecidedStates = collegeMeeting.itemDecidedStates
councilMeeting.itemPositiveDecidedStates = collegeMeeting.itemPositiveDecidedStates
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
councilMeeting.powerObservers[0]['item_states'] = ('presented', 'itemfrozen', 'accepted', 'delayed', 'refused')
councilMeeting.powerObservers[1]['item_states'] = ('presented', 'itemfrozen', 'accepted', 'delayed', 'refused')
councilMeeting.powerObservers[1]['item_access_on'] = \
    u"python: item.getListType() not in ('late', ) or " \
    u"item.query_state() not in ('presented', 'itemfrozen', 'returned_to_proposing_group')"

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
bourgmestreMeeting.categories = deepcopy(councilMeeting.categories)
# remove usingGroups for subproducts category
bourgmestreMeeting.categories[-1].using_groups = ()
bourgmestreMeeting.shortName = 'Bourgmestre'
bourgmestreMeeting.annexTypes = councilMeeting.annexTypes
bourgmestreMeeting.itemAnnexConfidentialVisibleFor = \
    bg_import_data.bourgmestreMeeting.itemAnnexConfidentialVisibleFor
bourgmestreMeeting.itemWFValidationLevels = bg_import_data.bourgmestreMeeting.itemWFValidationLevels
bourgmestreMeeting.itemConditionsInterface = bg_import_data.bourgmestreMeeting.itemConditionsInterface
bourgmestreMeeting.itemActionsInterface = bg_import_data.bourgmestreMeeting.itemActionsInterface
bourgmestreMeeting.meetingConditionsInterface = bg_import_data.bourgmestreMeeting.meetingConditionsInterface
bourgmestreMeeting.meetingActionsInterface = bg_import_data.bourgmestreMeeting.meetingActionsInterface
bourgmestreMeeting.itemDecidedStates = bg_import_data.bourgmestreMeeting.itemDecidedStates
bourgmestreMeeting.transitionsForPresentingAnItem = \
    bg_import_data.bourgmestreMeeting.transitionsForPresentingAnItem
bourgmestreMeeting.onMeetingTransitionItemActionToExecute = ()
bourgmestreMeeting.transitionsToConfirm = []
bourgmestreMeeting.itemPreferredMeetingStates = bg_import_data.bourgmestreMeeting.itemPreferredMeetingStates
bourgmestreMeeting.workflowAdaptations = bg_import_data.bourgmestreMeeting.workflowAdaptations
bourgmestreMeeting.meetingTopicStates = ('created', )
bourgmestreMeeting.decisionTopicStates = ('closed', )
bourgmestreMeeting.itemAdviceStates = ('proposed_to_director_waiting_advices', )
bourgmestreMeeting.recordItemHistoryStates = []
bourgmestreMeeting.maxShownMeetings = 5
bourgmestreMeeting.maxDaysDecisions = 60
bourgmestreMeeting.usedItemAttributes = [
    'category',
    'budgetInfos',
    'observations',
    'privacy',
    'motivation',
    'itemIsSigned',
    'copyGroups']
bourgmestreMeeting.insertingMethodsOnAddItem = (
    {'insertingMethod': 'at_the_end',
     'reverse': '0'}, )
bourgmestreMeeting.useAdvices = True
bourgmestreMeeting.selectableAdvisers = []
bourgmestreMeeting.itemAdviceStates = []
bourgmestreMeeting.itemAdviceEditStates = []
bourgmestreMeeting.itemAdviceViewStates = []
bourgmestreMeeting.itemDecidedStates = [
    'accepted', 'refused', 'delayed', 'marked_not_applicable']
bourgmestreMeeting.useVotes = False
bourgmestreMeeting.recurringItems = []
bourgmestreMeeting.itemTemplates = []

data = deepcopy(pm_import_data.data)
data.meetingConfigs = (collegeMeeting, councilMeeting, bourgmestreMeeting)
# necessary for testSetup.test_pm_ToolAttributesAreOnlySetOnFirstImportData
data.restrictUsers = False
data.usersOutsideGroups = data.usersOutsideGroups + \
    [pmFinController, pmFinReviewer, pmFinManager, pmMeetingManagerBG]
