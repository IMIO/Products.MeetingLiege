# -*- coding: utf-8 -*-

from DateTime import DateTime
from Products.MeetingLiege.config import BOURGMESTRE_GROUP_ID
from Products.MeetingLiege.config import GENERAL_MANAGER_GROUP_ID
from Products.PloneMeeting.profiles import AnnexTypeDescriptor
from Products.PloneMeeting.profiles import ItemAnnexTypeDescriptor
from Products.PloneMeeting.profiles import MeetingConfigDescriptor
from Products.PloneMeeting.profiles import OrgDescriptor
from Products.PloneMeeting.profiles import PloneMeetingConfiguration
from Products.PloneMeeting.profiles import UserDescriptor


today = DateTime().strftime('%Y/%m/%d')

# File types -------------------------------------------------------------------
annexe = ItemAnnexTypeDescriptor('annexe', 'Annexe', u'attach.png')
annexeDecision = ItemAnnexTypeDescriptor('annexeDecision', 'Annexe à la décision',
                                         u'attach.png', relatedTo='item_decision')
annexeAvis = AnnexTypeDescriptor('annexeAvis', 'Annexe à un avis',
                                 u'attach.png', relatedTo='advice')
annexeSeance = AnnexTypeDescriptor('annexe', 'Annexe',
                                   u'attach.png', relatedTo='meeting')

# No Categories -------------------------------------------------------------------
categories = []

# No Pod templates ----------------------------------------------------------------

bourgmestreTemplates = []

# Users and groups -------------------------------------------------------------
generalManager = UserDescriptor(
    'generalManager', [], email="general_manager@plonemeeting.org", fullname='M. GeneralManager')
bourgmestreManager = UserDescriptor(
    'bourgmestreManager', [], email="bourgmestre_manager@plonemeeting.org",
    fullname='M. Bourgmestre Manager')
bourgmestreReviewer = UserDescriptor(
    'bourgmestreReviewer', [], email="bourgmestre_reviewer@plonemeeting.org",
    fullname='M. Bourgmestre Reviewer')
general_manager_group = OrgDescriptor(GENERAL_MANAGER_GROUP_ID, u'General Managers', u'GMs')
general_manager_group.reviewers.append(generalManager)
bourgmestre_group = OrgDescriptor(BOURGMESTRE_GROUP_ID, u'Bourgmestre', u'BG')
bourgmestre_group.creators.append(bourgmestreManager)
bourgmestre_group.reviewers.append(bourgmestreReviewer)
orgs = [general_manager_group, bourgmestre_group]

# Meeting configurations -------------------------------------------------------
# Bourgmestre
bourgmestreMeeting = MeetingConfigDescriptor(
    'meeting-config-bourgmestre', 'Bourgmestre',
    'Bourgmestre')
bourgmestreMeeting.meetingManagers = ['pmManager']
bourgmestreMeeting.assembly = 'A compléter...'
bourgmestreMeeting.certifiedSignatures = [
    {'signatureNumber': '1',
     'name': u'Vraiment Présent',
     'function': u'Le Directeur général',
     'date_from': '',
     'date_to': '',
     },
    {'signatureNumber': '2',
     'name': u'Charles Exemple',
     'function': u'Le Bourgmestre',
     'date_from': '',
     'date_to': '',
     },
]
bourgmestreMeeting.places = ''
bourgmestreMeeting.categories = categories
bourgmestreMeeting.shortName = 'Bourgmestre'
bourgmestreMeeting.annexTypes = [annexe, annexeDecision, annexeAvis, annexeSeance]
bourgmestreMeeting.itemAnnexConfidentialVisibleFor = (
    'configgroup_budgetimpacteditors',
    'reader_advices',
    'reader_copy_groups',
    'reader_groupsincharge',
    'suffix_proposing_group_internalreviewers',
    'suffix_proposing_group_observers',
    'suffix_proposing_group_reviewers',
    'suffix_proposing_group_creators',
    'suffix_proposing_group_administrativereviewers')
bourgmestreMeeting.usedItemAttributes = ['observations', 'copyGroups']
bourgmestreMeeting.usedMeetingAttributes = ['signatures', 'assembly', 'observations', ]
bourgmestreMeeting.recordMeetingHistoryStates = []
bourgmestreMeeting.xhtmlTransformFields = ()
bourgmestreMeeting.xhtmlTransformTypes = ()
bourgmestreMeeting.hideCssClassesTo = ('powerobservers', 'restrictedpowerobservers')
bourgmestreMeeting.itemConditionsInterface = \
    'Products.MeetingLiege.interfaces.IMeetingItemBourgmestreWorkflowConditions'
bourgmestreMeeting.itemActionsInterface = \
    'Products.MeetingLiege.interfaces.IMeetingItemBourgmestreWorkflowActions'
bourgmestreMeeting.meetingConditionsInterface = \
    'Products.MeetingLiege.interfaces.IMeetingBourgmestreWorkflowConditions'
bourgmestreMeeting.meetingActionsInterface = \
    'Products.MeetingLiege.interfaces.IMeetingBourgmestreWorkflowActions'
bourgmestreMeeting.itemWFValidationLevels = (
    {'state': 'itemcreated',
     'state_title': 'itemcreated',
     'leading_transition': '-',
     'leading_transition_title': '-',
     'back_transition': 'backToItemCreated',
     'back_transition_title': 'backToItemCreated',
     'suffix': 'creators',
     # only creators may manage itemcreated item
     'extra_suffixes': [],
     'enabled': '1',
     },
    {'state': 'proposed_to_administrative_reviewer',
     'state_title': 'proposed_to_administrative_reviewer',
     'leading_transition': 'proposeToAdministrativeReviewer',
     'leading_transition_title': 'proposeToAdministrativeReviewer',
     'back_transition': 'backToProposedToAdministrativeReviewer',
     'back_transition_title': 'backToProposedToAdministrativeReviewer',
     'suffix': 'administrativereviewers',
     'extra_suffixes': [u'internalreviewers', u'reviewers'],
     'enabled': '1',
     },
    {'state': 'proposed_to_internal_reviewer',
     'state_title': 'proposed_to_internal_reviewer',
     'leading_transition': 'proposeToInternalReviewer',
     'leading_transition_title': 'proposeToInternalReviewer',
     'back_transition': 'backToProposedToInternalReviewer',
     'back_transition_title': 'backToProposedToInternalReviewer',
     'suffix': 'internalreviewers',
     'enabled': '1',
     'extra_suffixes': [u'reviewers'],
     },
    {'state': 'proposed_to_director',
     'state_title': 'proposed_to_director',
     'leading_transition': 'proposeToDirector',
     'leading_transition_title': 'proposeToDirector',
     'back_transition': 'backToProposedToDirector',
     'back_transition_title': 'backToProposedToDirector',
     'suffix': 'reviewers',
     'enabled': '1',
     'extra_suffixes': [],
     },
    {'state': 'proposed_to_general_manager',
     'state_title': 'proposed_to_general_manager',
     'leading_transition': 'proposeToGeneralManager',
     'leading_transition_title': 'proposeToGeneralManager',
     'back_transition': 'backToProposedToGeneralManager',
     'back_transition_title': 'backToProposedToGeneralManager',
     'suffix': 'reviewers',
     'enabled': '1',
     'extra_suffixes': [],
     },
    {'state': 'proposed_to_cabinet_manager',
     'state_title': 'proposed_to_cabinet_manager',
     'leading_transition': 'proposeToCabinetManager',
     'leading_transition_title': 'proposeToCabinetManager',
     'back_transition': 'backToProposedToCabinetManager',
     'back_transition_title': 'backToProposedToCabinetManager',
     'suffix': 'creators',
     'enabled': '1',
     'extra_suffixes': ['reviewers'],
     },
    {'state': 'proposed_to_cabinet_reviewer',
     'state_title': 'proposed_to_cabinet_reviewer',
     'leading_transition': 'proposeToCabinetReviewer',
     'leading_transition_title': 'proposeToCabinetReviewer',
     'back_transition': 'backToProposedToCabinetReviewer',
     'back_transition_title': 'backToProposedToCabinetReviewer',
     'suffix': 'reviewers',
     'enabled': '1',
     'extra_suffixes': [],
     },
)
bourgmestreMeeting.transitionsToConfirm = ['MeetingItem.delay', ]
bourgmestreMeeting.itemPreferredMeetingStates = ()
bourgmestreMeeting.meetingTopicStates = ('created', )
bourgmestreMeeting.decisionTopicStates = ('closed', )
bourgmestreMeeting.enforceAdviceMandatoriness = False
bourgmestreMeeting.insertingMethodsOnAddItem = ({'insertingMethod': 'on_proposing_groups',
                                                 'reverse': '0'}, )
bourgmestreMeeting.recordItemHistoryStates = []
bourgmestreMeeting.maxShownMeetings = 5
bourgmestreMeeting.maxDaysDecisions = 60
bourgmestreMeeting.meetingAppDefaultView = 'searchmyitems'
bourgmestreMeeting.useAdvices = True
bourgmestreMeeting.itemAdviceStates = ('validated',)
bourgmestreMeeting.itemAdviceEditStates = ('validated',)
bourgmestreMeeting.keepAccessToItemWhenAdvice = 'is_given'
bourgmestreMeeting.usedAdviceTypes = ['positive', 'positive_with_remarks', 'negative', 'nil', ]
bourgmestreMeeting.enableAdviceInvalidation = False
bourgmestreMeeting.itemAdviceInvalidateStates = []
bourgmestreMeeting.customAdvisers = []
bourgmestreMeeting.powerObservers = (
    {'item_access_on': '',
     'item_states': ['accepted',
                     'accepted_but_modified',
                     'delayed',
                     'refused',
                     'validated'],
     'label': 'Super observateurs',
     'meeting_access_on': '',
     'meeting_states': ('created', ),
     'row_id': 'powerobservers'},
    {'item_access_on': '',
     'item_states': ['accepted',
                     'accepted_but_modified',
                     'delayed',
                     'refused',
                     'returned_to_proposing_group',
                     'marked_not_applicable',
                     'validated'],
     'label': 'Super observateurs restreints',
     'meeting_access_on': '',
     'meeting_states': (),
     'row_id': 'restrictedpowerobservers'},
    # police administrative
    {'item_access_on': 'python:item.getProposingGroup() in [pm_utils.org_id_to_uid("bpa-arraata-c-s")]',
     'item_states': ['accepted',
                     'accepted_but_modified'],
     'label': 'Super observateurs Police administrative',
     'meeting_access_on': '',
     'meeting_states': (),
     'row_id': 'adminpolicepowerobservers'},
    # Juristes Urbanisme
    {'item_access_on': 'python:item.getProposingGroup() in ' \
        '[pm_utils.org_id_to_uid("urba-gestion-administrative"), ' \
        'pm_utils.org_id_to_uid("urba-service-de-lurbanisme"), ' \
        'pm_utils.org_id_to_uid("bpa-permis-environnement")]',
     'item_states': ['accepted',
                     'accepted_but_modified'],
     'label': 'Super observateurs Juristes Urbanisme',
     'meeting_access_on': '',
     'meeting_states': (),
     'row_id': 'jururbapowerobservers'},
    # Juristes Sécurité publique
    {'item_access_on': 'python:item.getProposingGroup() in [pm_utils.org_id_to_uid("bpa-sa-c-curita-c-publique")]',
     'item_states': ['accepted',
                     'accepted_but_modified'],
     'label': 'Super observateurs Juristes Sécurité publique',
     'meeting_access_on': '',
     'meeting_states': (),
     'row_id': 'jursecpubpowerobservers'},
)
bourgmestreMeeting.itemDecidedStates = ['accepted', 'refused', 'delayed', 'marked_not_applicable']
bourgmestreMeeting.workflowAdaptations = (
    'accepted_but_modified',
    'mark_not_applicable',
    'refused',
    'delayed',
    'no_publication',
    'item_validation_shortcuts',
    'item_validation_no_validate_shortcuts',
    'no_decide',
    'no_freeze',
    'only_creator_may_delete',
    'return_to_proposing_group',
    'waiting_advices',
    'waiting_advices_proposing_group_send_back')

bourgmestreMeeting.transitionsForPresentingAnItem = (
    u'proposeToAdministrativeReviewer',
    u'proposeToInternalReviewer',
    u'proposeToDirector',
    u'proposeToGeneralManager',
    u'proposeToCabinetManager',
    u'proposeToCabinetReviewer',
    u'validate',
    u'present')
bourgmestreMeeting.onTransitionFieldTransforms = (
    ({'transition': 'delay',
      'field_name': 'MeetingItem.decision',
      'tal_expression': "string:<p>Le bourgmestre décide de reporter le point.</p>"},))
bourgmestreMeeting.onMeetingTransitionItemActionToExecute = (
    {'meeting_transition': 'close',
     'item_action': 'accept',
     'tal_expression': ''}, )
bourgmestreMeeting.meetingPowerObserversStates = ('closed', 'created', )
bourgmestreMeeting.powerAdvisersGroups = ()
bourgmestreMeeting.itemBudgetInfosStates = ()
bourgmestreMeeting.enableLabels = True
bourgmestreMeeting.hideItemHistoryCommentsToUsersOutsideProposingGroup = True
bourgmestreMeeting.selectableCopyGroups = []
bourgmestreMeeting.podTemplates = bourgmestreTemplates
bourgmestreMeeting.meetingConfigsToCloneTo = []
bourgmestreMeeting.recurringItems = []
bourgmestreMeeting.itemTemplates = []

data = PloneMeetingConfiguration(meetingFolderTitle='Mes séances',
                                 meetingConfigs=(bourgmestreMeeting, ),
                                 orgs=orgs)
data.forceAddUsersAndGroups = True
# ------------------------------------------------------------------------------
