# -*- coding: utf-8 -*-

from copy import deepcopy
from DateTime import DateTime
from Products.MeetingLiege.config import NOT_COPY_GROUP_IDS
from Products.MeetingLiege.config import TREASURY_GROUP_ID
from Products.PloneMeeting.config import DEFAULT_LIST_TYPES
from Products.PloneMeeting.profiles import AnnexTypeDescriptor
from Products.PloneMeeting.profiles import CategoryDescriptor
from Products.PloneMeeting.profiles import ItemAnnexTypeDescriptor
from Products.PloneMeeting.profiles import ItemTemplateDescriptor
from Products.PloneMeeting.profiles import MeetingConfigDescriptor
from Products.PloneMeeting.profiles import OrgDescriptor
from Products.PloneMeeting.profiles import PloneMeetingConfiguration
from Products.PloneMeeting.profiles import PodTemplateDescriptor
from Products.PloneMeeting.profiles import RecurringItemDescriptor
from Products.PloneMeeting.profiles import UserDescriptor


today = DateTime().strftime('%Y/%m/%d')

# File types for College -------------------------------------------------------------------
annexe = ItemAnnexTypeDescriptor('annexe', 'Annexe',
                                 u'attach.png', confidential=True)
annexeBudget = ItemAnnexTypeDescriptor('annexeBudget', 'Article Budgétaire',
                                       u'budget.png', confidential=True)
annexeCahier = ItemAnnexTypeDescriptor('annexeCahier', 'Cahier des Charges', u'cahier.gif')
courrierCollege = ItemAnnexTypeDescriptor('courrier-a-valider-par-le-college',
                                          'Document soumis au Collège',
                                          u'courrierCollege.png')
annexeDecision = ItemAnnexTypeDescriptor('annexeDecision', 'Annexe à la décision',
                                         u'attach.png', relatedTo='item_decision', confidential=True)
deliberation_to_sign = ItemAnnexTypeDescriptor(
    'deliberation_to_sign', 'Délibération à signer',
    u'deliberation_to_sign.png', relatedTo='item_decision',
    to_sign=True, only_for_meeting_managers=True)
deliberation = ItemAnnexTypeDescriptor(
    'deliberation', 'Délibération', u'deliberation.png',
    relatedTo='item_decision', to_sign=True, signed=True,
    only_for_meeting_managers=True)
annexeAvis = AnnexTypeDescriptor('annexeAvis', 'Annexe à un avis',
                                 u'attach.png', relatedTo='advice', confidential=True)
annexeAvisLegal = AnnexTypeDescriptor('annexeAvisLegal', 'Extrait article de loi',
                                      u'legalAdvice.png', relatedTo='advice', confidential=True)
annexeSeance = AnnexTypeDescriptor('annexe', 'Annexe', u'attach.png', relatedTo='meeting')

# Pod templates ----------------------------------------------------------------
agendaTemplate = PodTemplateDescriptor('oj', 'Ordre du jour')
agendaTemplate.odt_file = 'college-oj.odt'
agendaTemplate.pod_formats = ['odt', 'pdf', ]
agendaTemplate.pod_portal_types = ['Meeting']
agendaTemplate.tal_condition = u'python: tool.isManager(cfg)'

decisionsTemplate = PodTemplateDescriptor('pv', 'Procès-verbal')
decisionsTemplate.odt_file = 'college-pv.odt'
decisionsTemplate.pod_formats = ['odt', 'pdf', ]
decisionsTemplate.pod_portal_types = ['Meeting']
decisionsTemplate.tal_condition = u'python: tool.isManager(cfg)'

itemTemplate = PodTemplateDescriptor('deliberation', 'Délibération')
itemTemplate.odt_file = 'deliberation.odt'
itemTemplate.pod_formats = ['odt', 'pdf', ]
itemTemplate.pod_portal_types = ['MeetingItem']
itemTemplate.tal_condition = u'python: here.hasMeeting()'

dfAdviceTemplate = PodTemplateDescriptor('synthese-finance-advice', 'Synthèse Avis DF', dashboard=True)
dfAdviceTemplate.odt_file = 'synthese_avis_df.odt'
dfAdviceTemplate.dashboard_collections_ids = ['searchitemswithfinanceadvice']
dfAdviceTemplate.tal_condition = u''

statsDFAdvice = PodTemplateDescriptor('stats-finance-advice', 'Statistiques Avis DF', dashboard=True)
statsDFAdvice.odt_file = 'stats_DF_advice.ods'
statsDFAdvice.dashboard_collections_ids = ['searchitemswithfinanceadvice']
statsDFAdvice.tal_condition = u''

collegeTemplates = [agendaTemplate, decisionsTemplate,
                    itemTemplate,
                    dfAdviceTemplate, statsDFAdvice]

councilTemplates = []

# Users and groups -------------------------------------------------------------
dgen = UserDescriptor('dgen', [], email="test@test.be", fullname="Henry Directeur")
bourgmestre = UserDescriptor('bourgmestre', [], email="test@test.be", fullname="Pierre Bourgmestre")
dfin = UserDescriptor('dfin', [], email="test@test.be", fullname="Directeur Financier")
agentInfo = UserDescriptor('agentInfo', [], email="test@test.be", fullname="Agent Service Informatique")
agentCompta = UserDescriptor('agentCompta', [], email="test@test.be", fullname="Agent Service Comptabilité")
agentPers = UserDescriptor('agentPers', [], email="test@test.be", fullname="Agent Service du Personnel")
agentTrav = UserDescriptor('agentTrav', [], email="test@test.be", fullname="Agent Travaux")
chefPers = UserDescriptor('chefPers', [], email="test@test.be", fullname="Chef Personnel")
chefCompta = UserDescriptor('chefCompta', [], email="test@test.be", fullname="Chef Comptabilité")
echevinPers = UserDescriptor('echevinPers', [], email="test@test.be", fullname="Echevin du Personnel")
echevinTrav = UserDescriptor('echevinTrav', [], email="test@test.be", fullname="Echevin des Travaux")
conseiller = UserDescriptor('conseiller', [], email="test@test.be", fullname="Conseiller")
emetteuravisPers = UserDescriptor('emetteuravisPers', [], email="test@test.be", fullname="Emetteur avis Personnel")

# add finance groups
dfcontrol = OrgDescriptor('df-contrale', u'DF - Contrôle', u'DF')
dfcontrol.item_advice_states = ['meeting-config-college__state__proposed_to_finance_waiting_advices']
dfcontrol.item_advice_edit_states = ['meeting-config-college__state__proposed_to_finance_waiting_advices']
dfcontrol.item_advice_view_states = ['meeting-config-college__state__accepted',
                                     'meeting-config-college__state__accepted_but_modified',
                                     'meeting-config-college__state__pre_accepted',
                                     'meeting-config-college__state__delayed',
                                     'meeting-config-college__state__itemfrozen',
                                     'meeting-config-college__state__proposed_to_finance_waiting_advices',
                                     'meeting-config-college__state__presented',
                                     'meeting-config-college__state__refused',
                                     'meeting-config-college__state__validated']
dfcompta = OrgDescriptor('df-comptabilita-c-et-audit-financier',
                         u'DF - Comptabilité et Audit financier',
                         u'DF')
dfcompta.item_advice_states = ['meeting-config-college__state__proposed_to_finance_waiting_advices']
dfcompta.item_advice_edit_states = ['meeting-config-college__state__proposed_to_finance_waiting_advices']
dfcompta.item_advice_view_states = ['meeting-config-college__state__accepted',
                                    'meeting-config-college__state__accepted_but_modified',
                                    'meeting-config-college__state__pre_accepted',
                                    'meeting-config-college__state__delayed',
                                    'meeting-config-college__state__itemfrozen',
                                    'meeting-config-college__state__proposed_to_finance_waiting_advices',
                                    'meeting-config-college__state__presented',
                                    'meeting-config-college__state__refused',
                                    'meeting-config-college__state__validated']
dftresor = OrgDescriptor(TREASURY_GROUP_ID,
                         u'DF - Contrôle (Trésorerie)',
                         u'DFCT',
                         as_copy_group_on=u'python: item.adapted().treasuryCopyGroup()')
dftresor.item_advice_states = ['meeting-config-college__state__accepted',
                               'meeting-config-college__state__accepted_but_modified']
dftresor.item_advice_edit_states = ['meeting-config-college__state__accepted',
                                    'meeting-config-college__state__accepted_but_modified']
rhrecr = OrgDescriptor(NOT_COPY_GROUP_IDS[0], u'RH - Recrutement', u'RHR')
rhgestadmin = OrgDescriptor(NOT_COPY_GROUP_IDS[1], u'RH - Gestion administrative', u'RHGA')

orgs = [OrgDescriptor('dirgen', 'Directeur Général', u'DG'),
        OrgDescriptor('secretariat', 'Secrétariat communal', u'Secr'),
        OrgDescriptor('informatique', 'Service informatique', u'Info'),
        OrgDescriptor('personnel', 'Service du personnel', u'Pers'),
        OrgDescriptor('dirfin', 'Directeur Financier', u'DF'),
        OrgDescriptor('comptabilite', 'Service comptabilité', u'Compt'),
        OrgDescriptor('travaux', 'Service travaux', u'Trav'),
        OrgDescriptor('scc', 'SCC', u'SCC'),
        OrgDescriptor('sc', 'SC', u'SC'),
        OrgDescriptor('secra-c-tariat-collage-conseil', 'Secrétariat Collège-Conseil', u'SC SCC'),
        dfcontrol,
        dfcompta,
        dftresor,
        rhrecr,
        rhgestadmin]

# MeetingManager
orgs[0].creators.append(dgen)
orgs[0].administrativereviewers.append(dgen)
orgs[0].internalreviewers.append(dgen)
orgs[0].reviewers.append(dgen)
orgs[0].observers.append(dgen)
orgs[0].advisers.append(dgen)

orgs[1].creators.append(dgen)
orgs[1].reviewers.append(dgen)
orgs[1].observers.append(dgen)
orgs[1].advisers.append(dgen)

orgs[2].creators.append(agentInfo)
orgs[2].creators.append(dgen)
orgs[2].reviewers.append(agentInfo)
orgs[2].reviewers.append(dgen)
orgs[2].observers.append(agentInfo)
orgs[2].advisers.append(agentInfo)

orgs[3].creators.append(agentPers)
orgs[3].observers.append(agentPers)
orgs[3].creators.append(dgen)
orgs[3].reviewers.append(dgen)
orgs[3].creators.append(chefPers)
orgs[3].reviewers.append(chefPers)
orgs[3].observers.append(chefPers)
orgs[3].observers.append(echevinPers)
orgs[3].advisers.append(emetteuravisPers)

orgs[4].creators.append(dfin)
orgs[4].reviewers.append(dfin)
orgs[4].observers.append(dfin)
orgs[4].advisers.append(dfin)

orgs[5].creators.append(agentCompta)
orgs[5].creators.append(chefCompta)
orgs[5].creators.append(dfin)
orgs[5].creators.append(dgen)
orgs[5].reviewers.append(chefCompta)
orgs[5].reviewers.append(dfin)
orgs[5].reviewers.append(dgen)
orgs[5].observers.append(agentCompta)
orgs[5].advisers.append(chefCompta)
orgs[5].advisers.append(dfin)

orgs[6].creators.append(agentTrav)
orgs[6].creators.append(dgen)
orgs[6].reviewers.append(agentTrav)
orgs[6].reviewers.append(dgen)
orgs[6].observers.append(agentTrav)
orgs[6].observers.append(echevinTrav)
orgs[6].advisers.append(agentTrav)

orgs[7].creators.append(dfin)
orgs[7].reviewers.append(dfin)
orgs[7].observers.append(dfin)
orgs[7].advisers.append(dfin)
orgs[7].administrativereviewers.append(dfin)
orgs[7].internalreviewers.append(dfin)

orgs[8].creators.append(dfin)
orgs[8].reviewers.append(dfin)
orgs[8].observers.append(dfin)
orgs[8].advisers.append(dfin)
orgs[8].administrativereviewers.append(dfin)
orgs[8].internalreviewers.append(dfin)

orgs[9].creators.append(agentPers)
orgs[9].reviewers.append(chefPers)
orgs[9].administrativereviewers.append(chefPers)
orgs[9].internalreviewers.append(chefPers)

orgs[10].creators.append(agentPers)
orgs[10].reviewers.append(chefPers)
orgs[10].administrativereviewers.append(chefPers)
orgs[10].internalreviewers.append(chefPers)

# Meeting configurations -------------------------------------------------------
# college
collegeMeeting = MeetingConfigDescriptor(
    'meeting-config-college', 'Collège Communal',
    'Collège Communal', isDefault=True)
collegeMeeting.meetingManagers = ('dgen', )
collegeMeeting.assembly = 'Pierre Dupont - Bourgmestre,\n' \
                          'Charles Exemple - 1er Echevin,\n' \
                          'Echevin Un, Echevin Deux, Echevin Trois - Echevins,\n' \
                          'Jacqueline Exemple, Responsable du CPAS'
collegeMeeting.signatures = 'Pierre Dupont, Bourgmestre - Charles Exemple, 1er Echevin'
recurring = CategoryDescriptor('recurrents', 'Récurrents')
categoriesCollege = [recurring,
                     CategoryDescriptor('cat-coll-1', u'Catégorie collège 1'),
                     CategoryDescriptor('cat-coll-2', u'Catégorie collège 2'),
                     CategoryDescriptor('cat-coll-3', u'Catégorie collège 3'),
                     CategoryDescriptor('cat-coll-4', u'Catégorie collège 4'),
                     CategoryDescriptor('cat-coll-5', u'Catégorie collège 5'),
                     CategoryDescriptor('cat-coll-6', u'Catégorie collège 6'), ]
collegeMeeting.categories = categoriesCollege
collegeMeeting.shortName = 'College'
collegeMeeting.itemReferenceFormat = 'python: here.adapted().getItemRefForActe()'
collegeMeeting.annexTypes = [annexe, annexeBudget, annexeCahier, courrierCollege,
                             annexeDecision, deliberation_to_sign, deliberation,
                             annexeAvis, annexeAvisLegal, annexeSeance]
collegeMeeting.itemGroupsInChargeStates = (
    u'accepted', u'accepted_but_modified', u'accepted_and_returned',
    u'pre_accepted', u'delayed', u'returned', u'itemfrozen', u'validated',
    u'presented', u'refused', u'returned_to_proposing_group',
    u'marked_not_applicable')
collegeMeeting.itemAnnexConfidentialVisibleFor = ('configgroup_budgetimpacteditors',
                                                  'reader_advices',
                                                  'reader_copy_groups',
                                                  'reader_groupsincharge',
                                                  'suffix_proposing_group_internalreviewers',
                                                  'suffix_proposing_group_observers',
                                                  'suffix_proposing_group_reviewers',
                                                  'suffix_proposing_group_creators',
                                                  'suffix_proposing_group_administrativereviewers')
collegeMeeting.usedItemAttributes = ['budgetInfos',
                                     'category',
                                     'observations',
                                     'description',
                                     'detailedDescription',
                                     'toDiscuss',
                                     'financeAdvice',
                                     'completeness',
                                     'emergency',
                                     'otherMeetingConfigsClonableToFieldDetailedDescription',
                                     'otherMeetingConfigsClonableToEmergency',
                                     'otherMeetingConfigsClonableToPrivacy',
                                     'takenOverBy',
                                     'motivation',
                                     'decisionSuite',
                                     'decisionEnd',
                                     'textCheckList',
                                     'copyGroups']
collegeMeeting.usedMeetingAttributes = ['signatures',
                                        'assembly',
                                        'assembly_excused',
                                        'observations', ]
collegeMeeting.xhtmlTransformFields = ('MeetingItem.description', 'MeetingItem.detailedDescription',
                                       'MeetingItem.decision', 'MeetingItem.observations', )
collegeMeeting.xhtmlTransformTypes = ('removeBlanks',)
collegeMeeting.meetingConfigsToCloneTo = ({'meeting_config': 'cfg2',
                                           'trigger_workflow_transitions_until': '__nothing__'},)
collegeMeeting.itemAutoSentToOtherMCStates = ('sent_to_council_emergency', 'accepted',
                                              'accepted_but_modified', 'accepted_and_returned')
collegeMeeting.hideCssClassesTo = ('powerobservers', 'restrictedpowerobservers')
collegeMeeting.itemWorkflow = 'meetingitem_workflow'
collegeMeeting.meetingWorkflow = 'meeting_workflow'
collegeMeeting.itemConditionsInterface = 'Products.MeetingLiege.interfaces.IMeetingItemCollegeLiegeWorkflowConditions'
collegeMeeting.itemActionsInterface = 'Products.MeetingLiege.interfaces.IMeetingItemCollegeLiegeWorkflowActions'
collegeMeeting.meetingConditionsInterface = 'Products.MeetingLiege.interfaces.IMeetingCollegeLiegeWorkflowConditions'
collegeMeeting.meetingActionsInterface = 'Products.MeetingLiege.interfaces.IMeetingCollegeLiegeWorkflowActions'
collegeMeeting.workflowAdaptations = [
    'item_validation_shortcuts',
    'item_validation_no_validate_shortcuts',
    'accepted_and_returned',
    'accepted_but_modified',
    'delayed',
    'mark_not_applicable',
    'no_publication',
    'only_creator_may_delete',
    'pre_accepted',
    'refused',
    'returned',
    'return_to_proposing_group',
    'sent_to_council_emergency',
    'waiting_advices',
    'waiting_advices_proposing_group_send_back',
    'waiting_advices_adviser_send_back']
collegeMeeting.itemWFValidationLevels = (
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
)
collegeMeeting.transitionsForPresentingAnItem = ('proposeToAdministrativeReviewer',
                                                 'proposeToInternalReviewer',
                                                 'proposeToDirector',
                                                 'validate',
                                                 'present', )
collegeMeeting.onMeetingTransitionItemActionToExecute = (
    {'meeting_transition': 'freeze',
     'item_action': 'itemfreeze',
     'tal_expression': ''},

    {'meeting_transition': 'decide',
     'item_action': 'itemfreeze',
     'tal_expression': ''},

    {'meeting_transition': 'close',
     'item_action': 'itemfreeze',
     'tal_expression': ''},
    {'meeting_transition': 'close',
     'item_action': 'accept',
     'tal_expression': ''}, )
collegeMeeting.itemDecidedStates = ('accepted', 'accepted_but_modified', 'pre_accepted', 'refused', 'delayed',
                                    'accepted_and_returned', 'returned', 'marked_not_applicable',
                                    'sent_to_council_emergency')
collegeMeeting.itemPositiveDecidedStates = ('accepted', 'accepted_but_modified', 'accepted_and_returned',
                                            'pre_accepted', 'sent_to_council_emergency')
collegeMeeting.meetingTopicStates = ('created', 'frozen')
collegeMeeting.decisionTopicStates = ('decided', 'closed')
# done in setuphandlers._configureCollegeCustomAdvisers
collegeMeeting.customAdvisers = []
collegeMeeting.powerAdvisersGroups = ('dirgen', 'dirfin')
collegeMeeting.powerObservers = (
    {'item_access_on': '',
     'item_states': ['accepted',
                     'accepted_but_modified',
                     'accepted_and_returned',
                     'pre_accepted',
                     'delayed',
                     'returned',
                     'itemfrozen',
                     'refused',
                     'returned_to_proposing_group',
                     'marked_not_applicable',
                     'validated'],
     'label': 'Super observateurs',
     'meeting_access_on': '',
     'meeting_states': ('closed', 'created', 'decided', 'frozen'),
     'row_id': 'powerobservers'},
    {'item_access_on': '',
     'item_states': ['accepted',
                     'accepted_but_modified',
                     'accepted_and_returned',
                     'pre_accepted',
                     'delayed',
                     'returned',
                     'itemfrozen',
                     'refused',
                     'returned_to_proposing_group',
                     'marked_not_applicable',
                     'validated'],
     'label': 'Super observateurs restreints',
     'meeting_access_on': '',
     'meeting_states': ('closed', 'decided', 'frozen'),
     'row_id': 'restrictedpowerobservers'},
    # police administrative
    {'item_access_on': 'python:item.getProposingGroup() in [pm_utils.org_id_to_uid("bpa-arraata-c-s")]',
     'item_states': ['accepted',
                     'accepted_but_modified',
                     'accepted_and_returned'],
     'label': 'Super observateurs Police administrative',
     'meeting_access_on': '',
     'meeting_states': (),
     'row_id': 'adminpolicepowerobservers'},
    # gestionnaires infrastructure
    {'item_access_on': 'python:item.getProposingGroup() in ' \
        '[pm_utils.org_id_to_uid("urba-gestion-administrative"), ' \
        'pm_utils.org_id_to_uid("urba-service-de-lurbanisme")]',
     'item_states': ['accepted',
                     'accepted_but_modified',
                     'pre_accepted'],
     'label': 'Super observateurs Gestionnaires infrastructure',
     'meeting_access_on': '',
     'meeting_states': (),
     'row_id': 'gestinfrapowerobservers'},
    # Juristes MP
    {'item_access_on': 'python:item.getProposingGroup() in [pm_utils.org_id_to_uid("bat-marcha-c-s-publics")]',
     'item_states': ['accepted',
                     'accepted_but_modified',
                     'pre_accepted'],
     'label': 'Super observateurs Juristes Marchés publics',
     'meeting_access_on': '',
     'meeting_states': (),
     'row_id': 'jurmppowerobservers'},
    # Juristes Urbanisme
    {'item_access_on': 'python:item.getProposingGroup() in ' \
        '[pm_utils.org_id_to_uid("urba-gestion-administrative"), ' \
        'pm_utils.org_id_to_uid("urba-service-de-lurbanisme"), ' \
        'pm_utils.org_id_to_uid("bpa-permis-environnement")]',
     'item_states': ['accepted',
                     'accepted_but_modified',
                     'pre_accepted'],
     'label': 'Super observateurs Juristes Urbanisme',
     'meeting_access_on': '',
     'meeting_states': (),
     'row_id': 'jururbapowerobservers'},
    # Juristes Sécurité publique
    {'item_access_on': 'python:item.getProposingGroup() in [pm_utils.org_id_to_uid("bpa-sa-c-curita-c-publique")]',
     'item_states': ['accepted',
                     'accepted_but_modified',
                     'pre_accepted'],
     'label': 'Super observateurs Juristes Sécurité publique',
     'meeting_access_on': '',
     'meeting_states': (),
     'row_id': 'jursecpubpowerobservers'},
    # Cabinet
    {'item_access_on': 'python:item.getProposingGroup() not in ' \
        '[pm_utils.org_id_to_uid("rh-direction"), ' \
        'pm_utils.org_id_to_uid("rh-gestion-administrative"), ' \
        'pm_utils.org_id_to_uid("rh-juridique"), ' \
        'pm_utils.org_id_to_uid("rh-recrutement"), ' \
        'pm_utils.org_id_to_uid("rh-pension"), ' \
        'pm_utils.org_id_to_uid("ip-personnel")]',
     'item_states': ['accepted',
                     'accepted_but_modified',
                     'accepted_and_returned',
                     'pre_accepted',
                     'delayed',
                     'returned',
                     'itemfrozen',
                     'refused',
                     'returned_to_proposing_group',
                     'marked_not_applicable'],
     'label': 'Super observateurs Cabinet',
     'meeting_access_on': '',
     'meeting_states': (),
     'row_id': 'cabinetpowerobservers'},
)

collegeMeeting.meetingAppDefaultView = 'searchmyitems'
collegeMeeting.useAdvices = True
collegeMeeting.usedAdviceTypes = ('positive', 'positive_with_remarks', 'negative', 'nil')
collegeMeeting.itemAdviceStates = ('itemcreated_waiting_advices',
                                   'proposed_to_internal_reviewer_waiting_advices')
collegeMeeting.itemAdviceEditStates = ('itemcreated_waiting_advices',
                                       'proposed_to_internal_reviewer_waiting_advices')
collegeMeeting.itemAdviceViewStates = ('itemcreated_waiting_advices', 'proposed_to_administrative_reviewer',
                                       'proposed_to_internal_reviewer', 'proposed_to_internal_reviewer_waiting_advices',
                                       'proposed_to_director', 'validated', 'presented',
                                       'itemfrozen', 'refused', 'delayed',
                                       'pre_accepted', 'accepted', 'accepted_but_modified', )
collegeMeeting.keepAccessToItemWhenAdvice = 'is_given'
collegeMeeting.hideItemHistoryCommentsToUsersOutsideProposingGroup = True
collegeMeeting.transitionReinitializingDelays = 'backToProposedToDirector'
collegeMeeting.defaultAdviceHiddenDuringRedaction = ['meetingadvice', 'meetingadvicefinances']
collegeMeeting.enforceAdviceMandatoriness = False
collegeMeeting.enableAdviceInvalidation = False
collegeMeeting.selectableCopyGroups = [orgs[0].getIdSuffixed('reviewers'),
                                       orgs[1].getIdSuffixed('reviewers'),
                                       orgs[2].getIdSuffixed('reviewers'),
                                       orgs[3].getIdSuffixed('reviewers'),
                                       orgs[4].getIdSuffixed('reviewers'),
                                       orgs[5].getIdSuffixed('reviewers'),
                                       orgs[6].getIdSuffixed('reviewers'), ]
collegeMeeting.itemCopyGroupsStates = ('accepted', 'accepted_but_modified', 'pre_accepted',
                                       'itemfrozen', 'refused', 'delayed')
collegeMeeting.podTemplates = collegeTemplates
collegeMeeting.insertingMethodsOnAddItem = ({'insertingMethod': 'on_categories',
                                             'reverse': '0'},
                                            {'insertingMethod': 'on_other_mc_to_clone_to',
                                             'reverse': '0'}, )
collegeMeeting.recurringItems = [
    RecurringItemDescriptor(
        id='recurringagenda1',
        title='Approuve le procès-verbal de la séance antérieure',
        description='<p>Approuve le procès-verbal de la séance antérieure</p>',
        category='recurrents',
        proposingGroup='secretariat',
        decision='Procès-verbal approuvé'),
    RecurringItemDescriptor(
        id='recurringofficialreport1',
        title='Autorise et signe les bons de commande de la semaine',
        description='<p>Autorise et signe les bons de commande de la semaine</p>',
        category='recurrents',
        proposingGroup='secretariat',
        decision='Bons de commande signés'),
    RecurringItemDescriptor(
        id='recurringofficialreport2',
        title='Ordonnance et signe les mandats de paiement de la semaine',
        description='<p>Ordonnance et signe les mandats de paiement de la semaine</p>',
        category='recurrents',
        proposingGroup='secretariat',
        decision='Mandats de paiement de la semaine approuvés'), ]
collegeMeeting.meetingUsers = []
collegeMeeting.itemTemplates = [
    ItemTemplateDescriptor(
        id='template1',
        title='Tutelle CPAS',
        description='<p>Tutelle CPAS</p>',
        proposingGroup='',
        templateUsingGroups=[],
        decision="""<p>Vu la loi du 8 juillet 1976 organique des centres publics d'action sociale...;</p>
        <p>Vu l'Arrêté du Gouvernement Wallon du 22 avril 2004 portant codification de la...;</p>
        <p>Attendu que les décisions suivantes du Bureau permanent/du Conseil de l'Action sociale du ...:</p>
        <p>- ...;</p>
        <p>- ...;</p>
        <p>- ...</p>
        <p>Attendu que ces décisions sont conformes à la loi et à l'intérêt général;</p>
        <p>Déclare à l'unanimité que :</p>
        <p><strong>Article 1er :</strong></p>
        <p>Les décisions du Bureau permanent/Conseil de l'Action sociale visées ci-dessus sont conformes...</p>
        <p><strong>Article 2 :</strong></p>
        <p>Copie de la présente délibération sera transmise au Bureau permanent/Conseil de l'Action sociale.</p>"""),
    ItemTemplateDescriptor(
        id='template2',
        title='Contrôle médical systématique agent contractuel',
        description='<p>Contrôle médical systématique agent contractuel</p>',
        proposingGroup='',
        templateUsingGroups=[],
        decision="""
        <p>Vu la loi du 26 mai 2002 instituant le droit à l’intégration sociale;</p>
        <p>Vu la délibération du Conseil communal du 29 juin 2009 concernant le cahier spécial des charges...;</p>
        <p>Vu sa délibération du 17 décembre 2009 désignant le docteur XXX en qualité d’adjudicataire pour...;</p>
        <p>Vu également sa décision du 17 décembre 2009 d’opérer les contrôles médicaux de manière...;</p>
        <p>Attendu qu’un certificat médical a été  reçu le XXX concernant XXX la couvrant du XXX au XXX, ...;</p>
        <p>Attendu que le Docteur XXX a transmis au service du Personnel, par fax, le même jour à XXX le...;</p>
        <p>Considérant que XXX avait été informée par le Service du Personnel de la mise en route du système...;</p>
        <p>Considérant qu’ayant été absent(e) pour maladie la semaine précédente elle avait reçu la visite...;</p>
        <p>DECIDE :</p>
        <p><strong>Article 1</strong> : De convoquer XXX devant  Monsieur le Secrétaire communal f.f. afin de...</p>
        <p><strong>Article 2</strong> :  De prévenir XXX, qu’en cas de récidive, il sera proposé par...</p>
        <p><strong>Article 3</strong> : De charger le service du personnel du suivi de ce dossier.</p>"""),
    ItemTemplateDescriptor(
        id='template4',
        title='Prestation réduite',
        description='<p>Prestation réduite</p>',
        proposingGroup='',
        templateUsingGroups=[],
        decision="""<p>Vu la loi de redressement du 22 janvier 1985 (article 99 et suivants) et de l’Arrêté...;</p>
        <p>Vu la lettre du XXX par laquelle Madame XXX, institutrice maternelle, sollicite le renouvellement...;</p>
        <p>Attendu que le remplacement de l’intéressée&nbsp;est assuré pour la prochaine rentrée scolaire;</p>
        <p>Vu le décret de la Communauté Française du 13 juillet 1988 portant restructuration de l’enseignement...;</p>
        <p>Vu la loi du 29 mai 1959 (Pacte Scolaire) et les articles L1122-19 et L1213-1 du code de la...;</p>
        <p>Vu l’avis favorable de l’Echevin de l’Enseignement;</p>
        <p><b>DECIDE&nbsp;:</b><br><b><br> Article 1<sup>er</sup></b>&nbsp;:</p>
        <p>Au scrutin secret et à l’unanimité, d’accorder à Madame XXX le congé pour prestations réduites...</p>
        <p><b>Article 2</b> :</p>
        <p>Une activité lucrative est autorisée durant ce congé qui est assimilé à une période d’activité...</p>
        <p><b>Article 3&nbsp;:</b></p>
        <p>La présente délibération sera soumise pour accord au prochain Conseil, transmise au Bureau...,</p>"""),
    ItemTemplateDescriptor(
        id='template5',
        title='Exemple modèle disponible pour tous',
        description='<p>Exemple modèle disponible pour tous</p>',
        proposingGroup='',
        templateUsingGroups=[],
        decision="""<p>Vu la loi du XXX;</p>
        <p>Vu ...;</p>
        <p>Attendu que ...;</p>
        <p>Vu le décret de la Communauté Française du ...;</p>
        <p>Vu la loi du ...;</p>
        <p>Vu l’avis favorable de ...;</p>
        <p><b>DECIDE&nbsp;:</b><br><b><br> Article 1<sup>er</sup></b>&nbsp;:</p>
        <p>...</p>
        <p><b>Article 2</b> :</p>
        <p>...</p>
        <p><b>Article 3&nbsp;:</b></p>
        <p>...</p>"""),
]
collegeMeeting.category_group_activated_attrs = {
    'item_annexes': ['confidentiality_activated', 'signed_activated'],
    'item_decision_annexes': ['confidentiality_activated', 'signed_activated']}

# council
councilMeeting = MeetingConfigDescriptor(
    'meeting-config-council', 'Conseil Communal',
    'Conseil Communal', isDefault=True)
councilMeeting.meetingManagers = ('dgen', )
councilMeeting.assembly = 'Pierre Dupont - Bourgmestre,\n' \
                          'Charles Exemple - 1er Echevin,\n' \
                          'Echevin Un, Echevin Deux, Echevin Trois - Echevins,\n' \
                          'Jacqueline Exemple, Responsable du CPAS'
councilMeeting.signatures = 'Pierre Dupont, Bourgmestre - Charles Exemple, 1er Echevin'
categoriesCouncil = [recurring,
                     CategoryDescriptor('cat-council-1', u'Catégorie conseil 1'),
                     CategoryDescriptor('cat-council-2', u'Catégorie conseil 2'),
                     CategoryDescriptor('cat-council-3', u'Catégorie conseil 3'),
                     CategoryDescriptor('cat-council-4', u'Catégorie conseil 4'),
                     CategoryDescriptor('cat-council-5', u'Catégorie conseil 5'),
                     CategoryDescriptor('cat-council-6', u'Catégorie conseil 6'), ]
councilMeeting.categories = categoriesCouncil
councilMeeting.shortName = 'Council'
councilMeeting.itemReferenceFormat = \
    "python: 'Ref. ' + (here.hasMeeting() " \
    "and here.restrictedTraverse('pm_unrestricted_methods').getLinkedMeetingDate().strftime('%Y%m%d') or '') + '/' + " \
    "str(here.getItemNumber(relativeTo='meeting'))"
councilMeeting.annexTypes = [annexe, annexeBudget, annexeCahier, courrierCollege,
                             annexeDecision, deliberation_to_sign, deliberation,
                             annexeAvis, annexeAvisLegal, annexeSeance]
councilMeeting.itemAnnexConfidentialVisibleFor = ('configgroup_budgetimpacteditors',
                                                  'reader_advices',
                                                  'reader_copy_groups',
                                                  'reader_groupsincharge',
                                                  'suffix_proposing_group_observers',
                                                  'suffix_proposing_group_creators', )
councilMeeting.usedItemAttributes = ['budgetInfos',
                                     'category',
                                     'description',
                                     'detailedDescription',
                                     'observations',
                                     'privacy',
                                     'motivation',
                                     'decisionSuite',
                                     'decisionEnd',
                                     'copyGroups']
councilMeeting.usedMeetingAttributes = ['signatures',
                                        'assembly',
                                        'assembly_excused',
                                        'observations', ]
councilMeeting.xhtmlTransformFields = ('MeetingItem.description', 'MeetingItem.detailedDescription',
                                       'MeetingItem.decision', 'MeetingItem.observations', )
councilMeeting.xhtmlTransformTypes = ('removeBlanks',)
councilMeeting.listTypes = DEFAULT_LIST_TYPES + [{'identifier': 'addendum',
                                                  'label': 'Addendum',
                                                  'used_in_inserting_method': ''}, ]
councilMeeting.itemAutoSentToOtherMCStates = ('delayed', 'returned')
councilMeeting.hideCssClassesTo = ('powerobservers', 'restrictedpowerobservers')
councilMeeting.enableItemDuplication = False
councilMeeting.itemWorkflow = 'meetingitem_workflow'
councilMeeting.meetingWorkflow = 'meeting_workflow'
councilMeeting.itemConditionsInterface = 'Products.MeetingLiege.interfaces.IMeetingItemCouncilLiegeWorkflowConditions'
councilMeeting.itemActionsInterface = 'Products.MeetingLiege.interfaces.IMeetingItemCouncilLiegeWorkflowActions'
councilMeeting.meetingConditionsInterface = 'Products.MeetingLiege.interfaces.IMeetingCouncilLiegeWorkflowConditions'
councilMeeting.meetingActionsInterface = 'Products.MeetingLiege.interfaces.IMeetingCouncilLiegeWorkflowActions'
councilMeeting.workflowAdaptations = [
    'return_to_proposing_group',
    'accepted_but_modified',
    'delayed',
    'mark_not_applicable',
    'no_publication',
    'pre_accepted',
    'refused',
    'returned']
councilMeeting.itemWFValidationLevels = (
    {'state': 'itemcreated',
     'state_title': 'itemcreated',
     'leading_transition': '-',
     'leading_transition_title': '-',
     'back_transition': 'backToItemCreated',
     'back_transition_title': 'backToItemCreated',
     'suffix': 'creators',
     'extra_suffixes': [u'administrativereviewers', u'internalreviewers', u'reviewers'],
     'enabled': '0',
     }, )
councilMeeting.transitionsForPresentingAnItem = ('present', )
councilMeeting.onMeetingTransitionItemActionToExecute = deepcopy(
    collegeMeeting.onMeetingTransitionItemActionToExecute)
councilMeeting.onTransitionFieldTransforms = (
    {'transition': 'present',
     'field_name': 'MeetingItem.decisionEnd',
     'tal_expression': 'python: here.adapted().adaptCouncilItemDecisionEnd()'},)
councilMeeting.itemDecidedStates = ('accepted', 'accepted_but_modified', 'pre_accepted',
                                    'delayed', 'returned', 'refused', 'marked_not_applicable')
councilMeeting.itemPositiveDecidedStates = ('accepted', 'accepted_but_modified', 'pre_accepted')
councilMeeting.meetingTopicStates = ('created', 'frozen')
councilMeeting.decisionTopicStates = ('decided', 'closed')
councilMeeting.meetingAppDefaultView = 'searchmyitems'
councilMeeting.useAdvices = False
councilMeeting.enforceAdviceMandatoriness = False
councilMeeting.enableAdviceInvalidation = False
councilMeeting.hideItemHistoryCommentsToUsersOutsideProposingGroup = True
councilMeeting.selectableCopyGroups = [orgs[0].getIdSuffixed('reviewers'),
                                       orgs[1].getIdSuffixed('reviewers'),
                                       orgs[2].getIdSuffixed('reviewers'),
                                       orgs[3].getIdSuffixed('reviewers'),
                                       orgs[4].getIdSuffixed('reviewers'),
                                       orgs[5].getIdSuffixed('reviewers'),
                                       orgs[6].getIdSuffixed('reviewers'), ]
councilMeeting.itemCopyGroupsStates = ('accepted', 'accepted_but_modified',
                                       'pre_accepted', 'itemfrozen',
                                       'refused', 'delayed')
councilMeeting.powerObservers = deepcopy(collegeMeeting.powerObservers)
councilMeeting.podTemplates = councilTemplates
councilMeeting.insertingMethodsOnAddItem = ({'insertingMethod': 'on_categories',
                                             'reverse': '0'},)
councilMeeting.meetingUsers = []
councilMeeting.recurringItems = [
    RecurringItemDescriptor(
        id='recurringagenda1',
        title='Approuve le procès-verbal de la séance antérieure',
        description='<p>Approuve le procès-verbal de la séance antérieure</p>',
        category='recurrents',
        proposingGroup='secretariat',
        decision='Procès-verbal approuvé'),
    RecurringItemDescriptor(
        id='recurringofficialreport1',
        title='Autorise et signe les bons de commande de la semaine',
        description='<p>Autorise et signe les bons de commande de la semaine</p>',
        category='recurrents',
        proposingGroup='secretariat',
        decision='Bons de commande signés'),
    RecurringItemDescriptor(
        id='recurringofficialreport2',
        title='Ordonnance et signe les mandats de paiement de la semaine',
        description='<p>Ordonnance et signe les mandats de paiement de la semaine</p>',
        category='recurrents',
        proposingGroup='secretariat',
        decision='Mandats de paiement de la semaine approuvés'), ]
councilMeeting.category_group_activated_attrs = {
    'item_annexes': ['confidentiality_activated', 'signed_activated'],
    'item_decision_annexes': ['confidentiality_activated', 'signed_activated']}

data = PloneMeetingConfiguration(meetingFolderTitle='Mes séances',
                                 meetingConfigs=(collegeMeeting, councilMeeting),
                                 orgs=orgs)
data.advisersConfig = (
    {'advice_types': ['positive_finance',
                      'positive_with_remarks_finance',
                      'negative_finance',
                      'not_required_finance'],
     'base_wf': 'meetingadviceliege_workflow',
     'default_advice_type': 'positive_finance',
     'org_uids': [dfcompta.id, dfcontrol.id],
     'portal_type': 'meetingadvicefinances',
     'show_advice_on_final_wf_transition': '1',
     'wf_adaptations': []},)
