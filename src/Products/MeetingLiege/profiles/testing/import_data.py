# -*- coding: utf-8 -*-
from Products.PloneMeeting.config import DEFAULT_LIST_TYPES
from Products.PloneMeeting.profiles import AnnexTypeDescriptor
from Products.PloneMeeting.profiles import CategoryDescriptor
from Products.PloneMeeting.profiles import GroupDescriptor
from Products.PloneMeeting.profiles import ItemAnnexTypeDescriptor
from Products.PloneMeeting.profiles import ItemAnnexSubTypeDescriptor
from Products.PloneMeeting.profiles import ItemTemplateDescriptor
from Products.PloneMeeting.profiles import MeetingConfigDescriptor
from Products.PloneMeeting.profiles import MeetingUserDescriptor
from Products.PloneMeeting.profiles import PloneGroupDescriptor
from Products.PloneMeeting.profiles import PloneMeetingConfiguration
from Products.PloneMeeting.profiles import PodTemplateDescriptor
from Products.PloneMeeting.profiles import RecurringItemDescriptor
from Products.PloneMeeting.profiles import UserDescriptor

# Annex types
overheadAnalysisSubtype = ItemAnnexSubTypeDescriptor(
    'overhead-analysis-sub-annex',
    'Overhead analysis sub annex',
    other_mc_correspondences=(
        'meeting-config-council_-_annexes_types_-_item_annexes_-_budget-analysis', ))

overheadAnalysis = ItemAnnexTypeDescriptor(
    'overhead-analysis', 'Administrative overhead analysis',
    u'overheadAnalysis.png',
    subTypes=[overheadAnalysisSubtype],
    other_mc_correspondences=(
        'meeting-config-council_-_annexes_types_-_item_annexes_-_budget-analysis_-_budget-analysis-sub-annex', ))

financialAnalysisSubAnnex = ItemAnnexSubTypeDescriptor(
    'financial-analysis-sub-annex',
    'Financial analysis sub annex')

financialAnalysis = ItemAnnexTypeDescriptor(
    'financial-analysis', 'Financial analysis', u'financialAnalysis.png',
    u'Predefined title for financial analysis', subTypes=[financialAnalysisSubAnnex])

legalAnalysis = ItemAnnexTypeDescriptor(
    'legal-analysis', 'Legal analysis', u'legalAnalysis.png')

budgetAnalysisCfg2Subtype = ItemAnnexSubTypeDescriptor(
    'budget-analysis-sub-annex',
    'Budget analysis sub annex')

budgetAnalysisCfg2 = ItemAnnexTypeDescriptor(
    'budget-analysis', 'Budget analysis', u'budgetAnalysis.png',
    subTypes=[budgetAnalysisCfg2Subtype])

budgetAnalysisCfg1Subtype = ItemAnnexSubTypeDescriptor(
    'budget-analysis-sub-annex',
    'Budget analysis sub annex',
    other_mc_correspondences=(
        'meeting-config-council_-_annexes_types_-_item_annexes_-_budget-analysis_-_budget-analysis-sub-annex', ))

budgetAnalysisCfg1 = ItemAnnexTypeDescriptor(
    'budget-analysis', 'Budget analysis', u'budgetAnalysis.png',
    subTypes=[budgetAnalysisCfg1Subtype],
    other_mc_correspondences=('meeting-config-council_-_annexes_types_-_item_annexes_-_budget-analysis', ))

itemAnnex = ItemAnnexTypeDescriptor(
    'item-annex', 'Other annex(es)', u'itemAnnex.png')

decisionAnnex = ItemAnnexTypeDescriptor(
    'decision-annex', 'Decision annex(es)', u'decisionAnnex.png', relatedTo='item_decision')
# A vintage annex type
marketingAnalysis = ItemAnnexTypeDescriptor(
    'marketing-annex', 'Marketing annex(es)', u'legalAnalysis.png', relatedTo='item_decision',
    enabled=False)
# Advice annex types
adviceAnnex = AnnexTypeDescriptor(
    'advice-annex', 'Advice annex(es)', u'itemAnnex.png', relatedTo='advice')
adviceLegalAnalysis = AnnexTypeDescriptor(
    'advice-legal-analysis', 'Advice legal analysis', u'legalAnalysis.png', relatedTo='advice')
# Meeting annex types
meetingAnnex = AnnexTypeDescriptor(
    'meeting-annex', 'Meeting annex(es)', u'itemAnnex.png', relatedTo='meeting')

# Pod templates ----------------------------------------------------------------
agendaTemplate = PodTemplateDescriptor('agendaTemplate', 'Meeting agenda')
agendaTemplate.odt_file = 'Agenda.odt'
agendaTemplate.pod_portal_types = ['MeetingCollege']
agendaTemplate.tal_condition = ''

decisionsTemplate = PodTemplateDescriptor('decisionsTemplate',
                                          'Meeting decisions')
decisionsTemplate.odt_file = 'Decisions.odt'
decisionsTemplate.pod_portal_types = ['MeetingCollege']
decisionsTemplate.tal_condition = 'python:here.adapted().isDecided()'

itemTemplate = PodTemplateDescriptor('itemTemplate', 'Meeting item')
itemTemplate.odt_file = 'Item.odt'
itemTemplate.pod_portal_types = ['MeetingItemCollege']
itemTemplate.tal_condition = ''

# Item templates -------------------------------------------------------------------

template1 = ItemTemplateDescriptor(id='template1',
                                   title='Tutelle CPAS',
                                   description='Tutelle CPAS',
                                   category='',
                                   proposingGroup='',
                                   templateUsingGroups=['developers', 'vendors'],
                                   decision="""<p>...</p>""")
template2 = ItemTemplateDescriptor(id='template2',
                                   title='Contrôle médical systématique agent contractuel',
                                   description='Contrôle médical systématique agent contractuel',
                                   category='',
                                   proposingGroup='vendors',
                                   templateUsingGroups=['vendors', ],
                                   decision="""<p>...</p>""")

# Categories -------------------------------------------------------------------
deployment = CategoryDescriptor('deployment', 'Deployment topics', categoryId='deployment')
maintenance = CategoryDescriptor('maintenance', 'Maintenance topics', categoryId='maintenance')
development = CategoryDescriptor('development', 'Development topics', categoryId='development')
events = CategoryDescriptor('events', 'Events', categoryId='events')
research = CategoryDescriptor('research', 'Research topics', categoryId='research')
projects = CategoryDescriptor('projects', 'Projects', categoryId='projects')
# A vintage category
marketing = CategoryDescriptor('marketing', 'Marketing', categoryId='marketing', active=False)
# usingGroups category
subproducts = CategoryDescriptor('subproducts',
                                 'Subproducts wishes',
                                 categoryId='subproducts',
                                 usingGroups=('vendors',))

# Classifiers
classifier1 = CategoryDescriptor('classifier1', 'Classifier 1')
classifier2 = CategoryDescriptor('classifier2', 'Classifier 2')
classifier3 = CategoryDescriptor('classifier3', 'Classifier 3')

# Users and groups -------------------------------------------------------------
pmFinController = UserDescriptor('pmFinController', [])
pmFinControllerCompta = UserDescriptor('pmFinControllerCompta', [])
pmFinReviewer = UserDescriptor('pmFinReviewer', [])
pmFinManager = UserDescriptor('pmFinManager', [])
pmMeetingManagerBG = UserDescriptor('pmMeetingManagerBG', [], email="pm_mm_bg@plone.org", fullname='M. PMMMBG')
pmManager = UserDescriptor('pmManager', [], email="pmmanager@plonemeeting.org", fullname='M. PMManager')
pmCreator1 = UserDescriptor('pmCreator1', [], email="pmcreator1@plonemeeting.org", fullname='M. PMCreator One')
pmCreator1b = UserDescriptor('pmCreator1b', [], email="pmcreator1b@plonemeeting.org", fullname='M. PMCreator One bee')
pmObserver1 = UserDescriptor('pmObserver1', [], email="pmobserver1@plonemeeting.org", fullname='M. PMObserver One')
pmAdminReviewer1 = UserDescriptor('pmAdminReviewer1', [])
pmInternalReviewer1 = UserDescriptor('pmInternalReviewer1', [])
pmReviewer1 = UserDescriptor('pmReviewer1', [])
pmReviewerLevel1 = UserDescriptor('pmReviewerLevel1', [],
                                  email="pmreviewerlevel1@plonemeeting.org",
                                  fullname='M. PMReviewer Level One')
pmCreator2 = UserDescriptor('pmCreator2', [])
pmReviewer2 = UserDescriptor('pmReviewer2', [])
pmReviewerLevel2 = UserDescriptor('pmReviewerLevel2', [],
                                  email="pmreviewerlevel2@plonemeeting.org",
                                  fullname='M. PMReviewer Level Two')
pmAdviser1 = UserDescriptor('pmAdviser1', [])
voter1 = UserDescriptor('voter1', [], fullname='M. Voter One')
voter2 = UserDescriptor('voter2', [], fullname='M. Voter Two')
powerobserver1 = UserDescriptor('powerobserver1',
                                [],
                                email="powerobserver1@plonemeeting.org",
                                fullname='M. Power Observer1')

# powerobserver1 is 'power observer' because in the meeting-config-college '_powerobservers' group
college_powerobservers = PloneGroupDescriptor('meeting-config-college_powerobservers',
                                              'meeting-config-college_powerobservers',
                                              [])
powerobserver1.ploneGroups = [college_powerobservers, ]
powerobserver2 = UserDescriptor('powerobserver2',
                                [],
                                email="powerobserver2@plonemeeting.org",
                                fullname='M. Power Observer2')
restrictedpowerobserver1 = UserDescriptor('restrictedpowerobserver1',
                                          [],
                                          email="restrictedpowerobserver1@plonemeeting.org",
                                          fullname='M. Restricted Power Observer 1')
college_restrictedpowerobservers = PloneGroupDescriptor('meeting-config-college_restrictedpowerobservers',
                                                        'meeting-config-college_restrictedpowerobservers',
                                                        [])
restrictedpowerobserver1.ploneGroups = [college_restrictedpowerobservers, ]
restrictedpowerobserver2 = UserDescriptor('restrictedpowerobserver2',
                                          [],
                                          email="restrictedpowerobserver2@plonemeeting.org",
                                          fullname='M. Restricted Power Observer 2')
council_restrictedpowerobservers = PloneGroupDescriptor('meeting-config-council_restrictedpowerobservers',
                                                        'meeting-config-council_restrictedpowerobservers',
                                                        [])

restrictedpowerobserver2.ploneGroups = [council_restrictedpowerobservers, ]
developers = GroupDescriptor('developers', 'Developers', 'Devel')
developers.creators.append(pmCreator1)
developers.creators.append(pmCreator1b)
developers.administrativereviewers.append(pmAdminReviewer1)
developers.administrativereviewers.append(pmManager)
developers.administrativereviewers.append(pmReviewerLevel1)
developers.internalreviewers.append(pmInternalReviewer1)
developers.internalreviewers.append(pmManager)
developers.creators.append(pmManager)
developers.reviewers.append(pmReviewer1)
developers.reviewers.append(pmManager)
developers.reviewers.append(pmReviewerLevel2)
developers.observers.append(pmObserver1)
developers.observers.append(pmReviewer1)
developers.observers.append(pmManager)
developers.advisers.append(pmAdviser1)
developers.advisers.append(pmManager)
setattr(developers, 'signatures', 'developers signatures')
setattr(developers, 'echevinServices', 'developers')

# give an advice on recurring items
vendors = GroupDescriptor('vendors', 'Vendors', 'Devil')
vendors.creators.append(pmCreator2)
vendors.reviewers.append(pmReviewer2)
vendors.observers.append(pmReviewer2)
vendors.advisers.append(pmReviewer2)
vendors.advisers.append(pmManager)
setattr(vendors, 'signatures', '')

# Do voters able to see items to vote for
developers.observers.append(voter1)
developers.observers.append(voter2)
vendors.observers.append(voter1)
vendors.observers.append(voter2)

# Add a vintage group
endUsers = GroupDescriptor('endUsers', 'End users', 'EndUsers', active=False)

pmManager_observer = MeetingUserDescriptor('pmManager',
                                           duty='Secrétaire de la Chancellerie',
                                           usages=['assemblyMember'])
cadranel_signer = MeetingUserDescriptor('cadranel', duty='Secrétaire',
                                        usages=['assemblyMember', 'signer'],
                                        signatureImage='SignatureCadranel.jpg',
                                        signatureIsDefault=True)
# Add meeting users (voting purposes)
muser_voter1 = MeetingUserDescriptor('voter1', duty='Voter1',
                                     usages=['assemblyMember', 'voter', ])
muser_voter2 = MeetingUserDescriptor('voter2', duty='Voter2',
                                     usages=['assemblyMember', 'voter', ])

# budget impact editors
budgetimpacteditor = UserDescriptor('budgetimpacteditor',
                                    [],
                                    email="budgetimpacteditor@plonemeeting.org",
                                    fullname='M. Budget Impact Editor')
college_budgetimpacteditors = PloneGroupDescriptor('meeting-config-college_budgetimpacteditors',
                                                   'meeting-config-college_budgetimpacteditors',
                                                   [])
budgetimpacteditor.ploneGroups = [college_budgetimpacteditors,
                                  college_powerobservers]

# Meeting configurations -------------------------------------------------------
# college
collegeMeeting = MeetingConfigDescriptor(
    'meeting-config-college', u'College Communal',
    u'College communal', isDefault=True)

collegeMeeting.meetingManagers = ('pmManager', )
collegeMeeting.assembly = 'Pierre Dupont - Bourgmestre,\n' \
                          'Charles Exemple - 1er Echevin,\n' \
                          'Echevin Un, Echevin Deux, Echevin Trois - Echevins,\n' \
                          'Jacqueline Exemple, Responsable du CPAS'
collegeMeeting.signatures = 'Pierre Dupont, Bourgmestre - Charles Exemple, Secrétaire communal'
collegeMeeting.certifiedSignatures = [{'signatureNumber': '1',
                                       'name': u'Vraiment Présent',
                                       'name': u'Mr Vraiment Présent',
                                       'function': u'Le Secrétaire communal',
                                       'date_from': '',
                                       'date_to': ''},
                                      {'signatureNumber': '2',
                                       'name': u'Charles Exemple',
                                       'name': u'Mr Charles Exemple',
                                       'function': u'Le Bourgmestre',
                                       'date_from': '',
                                       'date_to': '',
                                       }]
collegeMeeting.categories = [development, research]
collegeMeeting.classifiers = [classifier1, classifier2, classifier3]
collegeMeeting.shortName = 'College'
collegeMeeting.annexTypes = [financialAnalysis, budgetAnalysisCfg1, overheadAnalysis,
                             itemAnnex, decisionAnnex, marketingAnalysis,
                             adviceAnnex, adviceLegalAnalysis, meetingAnnex]
collegeMeeting.usedItemAttributes = ['budgetInfos',
                                     'detailedDescription',
                                     'observations',
                                     'toDiscuss',
                                     'itemAssembly',
                                     'completeness',
                                     'labelForCouncil',
                                     'otherMeetingConfigsClonableToPrivacy',
                                     'archivingRef',
                                     'motivation',
                                     'textCheckList',
                                     'itemIsSigned']
collegeMeeting.maxShownListings = '100'
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
collegeMeeting.transitionsToConfirm = []
collegeMeeting.meetingTopicStates = ('created', 'frozen')
collegeMeeting.decisionTopicStates = ('decided', 'closed')
collegeMeeting.recordItemHistoryStates = []
collegeMeeting.maxShownMeetings = 5
collegeMeeting.maxDaysDecisions = 60
collegeMeeting.useAdvices = True
collegeMeeting.selectableAdvisers = ('developers', 'vendors')
collegeMeeting.usedAdviceTypes = ('positive_finance', 'positive_with_remarks_finance',
                                  'negative_finance', 'not_required_finance',
                                  'positive', 'positive_with_remarks', 'negative', 'nil')
collegeMeeting.itemAdviceStates = ('proposed_to_director')
collegeMeeting.itemAdviceEditStates = ('proposed_to_director', 'validated')
collegeMeeting.itemAdviceViewStates = ('presented', 'itemfrozen', 'refused', 'delayed',
                                       'pre_accepted', 'accepted', 'accepted_but_modified', )
collegeMeeting.transitionsReinitializingDelays = ('backToItemCreated',)
collegeMeeting.enforceAdviceMandatoriness = False
collegeMeeting.itemPowerObserversStates = ('itemcreated', 'presented', 'accepted', 'delayed', 'refused')
collegeMeeting.itemDecidedStates = ['accepted', 'refused', 'delayed', 'accepted_but_modified', 'pre_accepted']
collegeMeeting.insertingMethodsOnAddItem = ({'insertingMethod': 'on_proposing_groups',
                                             'reverse': '0'}, )
collegeMeeting.useGroupsAsCategories = True
collegeMeeting.meetingPowerObserversStates = ('frozen', 'decided', 'closed')
collegeMeeting.useCopies = True
collegeMeeting.selectableCopyGroups = [developers.getIdSuffixed('reviewers'), vendors.getIdSuffixed('reviewers'), ]
collegeMeeting.podTemplates = [agendaTemplate, decisionsTemplate, itemTemplate]
collegeMeeting.meetingConfigsToCloneTo = ({'meeting_config': 'meeting-config-council',
                                           'trigger_workflow_transitions_until': '__nothing__'},)
collegeMeeting.itemAutoSentToOtherMCStates = ('sent_to_council_emergency',
                                              'accepted', 'accepted_but_modified', 'accepted_and_returned',)
collegeMeeting.recurringItems = [
    RecurringItemDescriptor(
        id='recItem1',
        description='<p>This is the first recurring item.</p>',
        title='Recurring item #1',
        proposingGroup='developers',
        decision='First recurring item approved'),

    RecurringItemDescriptor(
        id='recItem2',
        title='Recurring item #2',
        description='<p>This is the second recurring item.</p>',
        proposingGroup='developers',
        decision='Second recurring item approved'),
]
collegeMeeting.itemTemplates = (template1, template2)

# Conseil communal
councilMeeting = MeetingConfigDescriptor(
    'meeting-config-council', 'Conseil Communal',
    'Conseil Communal')
councilMeeting.meetingManagers = ('pmManager', )
councilMeeting.assembly = 'Default assembly'
councilMeeting.signatures = 'Default signatures'
councilMeeting.certifiedSignatures = [{'signatureNumber': '1',
                                       'name': u'Vraiment Présent',
                                       'name': u'Mr Vraiment Présent',
                                       'function': u'Le Secrétaire communal',
                                       'date_from': '',
                                       'date_to': ''},
                                      {'signatureNumber': '2',
                                       'name': u'Charles Exemple',
                                       'name': u'Mr Charles Exemple',
                                       'function': u'Le Bourgmestre',
                                       'date_from': '',
                                       'date_to': '',
                                       }]
councilMeeting.categories = [deployment, maintenance, development, events,
                             research, projects, marketing, subproducts]
councilMeeting.classifiers = [classifier1, classifier2, classifier3]
councilMeeting.shortName = 'Council'
councilMeeting.annexTypes = [financialAnalysis, legalAnalysis,
                             budgetAnalysisCfg2, itemAnnex, decisionAnnex,
                             adviceAnnex, adviceLegalAnalysis, meetingAnnex]
councilMeeting.itemWorkflow = 'meetingitemcouncilliege_workflow'
councilMeeting.meetingWorkflow = 'meetingcouncilliege_workflow'
councilMeeting.itemConditionsInterface = 'Products.MeetingLiege.interfaces.IMeetingItemCouncilLiegeWorkflowConditions'
councilMeeting.itemActionsInterface = 'Products.MeetingLiege.interfaces.IMeetingItemCouncilLiegeWorkflowActions'
councilMeeting.meetingConditionsInterface = 'Products.MeetingLiege.interfaces.IMeetingCouncilLiegeWorkflowConditions'
councilMeeting.meetingActionsInterface = 'Products.MeetingLiege.interfaces.IMeetingCouncilLiegeWorkflowActions'
councilMeeting.transitionsForPresentingAnItem = ('present', )
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
councilMeeting.transitionsToConfirm = []
councilMeeting.meetingTopicStates = ('created', 'frozen', 'published')
councilMeeting.decisionTopicStates = ('decided', 'closed')
councilMeeting.itemAdviceStates = ('validated',)
councilMeeting.recordItemHistoryStates = []
councilMeeting.maxShownMeetings = 5
councilMeeting.maxDaysDecisions = 60
councilMeeting.usedItemAttributes = ['budgetInfos',
                                     'labelForCouncil',
                                     'observations',
                                     'privacy',
                                     'itemAssembly',
                                     'motivation',
                                     'itemIsSigned']
councilMeeting.insertingMethodsOnAddItem = ({'insertingMethod': 'on_categories',
                                             'reverse': '0'}, )
councilMeeting.useGroupsAsCategories = False
councilMeeting.listTypes = DEFAULT_LIST_TYPES + [{'identifier': 'addendum',
                                                  'label': 'Addendum',
                                                  'used_in_inserting_method': ''}, ]
councilMeeting.useAdvices = False
councilMeeting.selectableAdvisers = []
councilMeeting.itemAdviceStates = []
councilMeeting.itemAdviceEditStates = []
councilMeeting.itemAdviceViewStates = []
councilMeeting.enforceAdviceMandatoriness = False
councilMeeting.itemDecidedStates = ['accepted', 'refused', 'delayed', 'accepted_but_modified', 'pre_accepted']
councilMeeting.itemPowerObserversStates = ('presented', 'itemfrozen', 'accepted', 'delayed', 'refused')
councilMeeting.itemRestrictedPowerObserversStates = ('presented', 'itemfrozen', 'accepted', 'delayed', 'refused')
councilMeeting.meetingPowerObserversStates = collegeMeeting.meetingPowerObserversStates
councilMeeting.useCopies = True
councilMeeting.selectableCopyGroups = [developers.getIdSuffixed('reviewers'), vendors.getIdSuffixed('reviewers'), ]
councilMeeting.useVotes = True
councilMeeting.meetingUsers = [muser_voter1, muser_voter2, ]
councilMeeting.recurringItems = []
councilMeeting.itemTemplates = (template1, template2)

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
bourgmestreMeeting.categories = [
    deployment, maintenance, development, events,
    research, projects, marketing, subproducts]
bourgmestreMeeting.shortName = 'Bourgmestre'
bourgmestreMeeting.annexTypes = [
    financialAnalysis, legalAnalysis,
    budgetAnalysisCfg2, itemAnnex, decisionAnnex,
    adviceAnnex, adviceLegalAnalysis, meetingAnnex]

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
    'itemAssembly',
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

# no recurring items for this meetingConfig, only for tests !!!
# so we can test a meetingConfig with recurring items (college) and without (council)
data = PloneMeetingConfiguration(
    meetingFolderTitle='Mes seances',
    meetingConfigs=(collegeMeeting, councilMeeting, bourgmestreMeeting),
    groups=(developers, vendors, endUsers))
# necessary for testSetup.test_pm_ToolAttributesAreOnlySetOnFirstImportData
data.restrictUsers = False
data.usersOutsideGroups = [voter1, voter2, powerobserver1, powerobserver2,
                           restrictedpowerobserver1, restrictedpowerobserver2,
                           pmFinController, pmFinReviewer, pmFinManager,
                           budgetimpacteditor, pmMeetingManagerBG]
# ------------------------------------------------------------------------------
