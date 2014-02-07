# -*- coding: utf-8 -*-
from Products.PloneMeeting.profiles import *

# File types -------------------------------------------------------------------

annexe = MeetingFileTypeDescriptor('annexe', 'Annexe', 'attach.png', '')
annexeBudget = MeetingFileTypeDescriptor('annexeBudget', 'Article Budgetaire', 'budget.png', '')
annexeCahier = MeetingFileTypeDescriptor('annexeCahier', 'Cahier des Charges', 'cahier.gif', '')
itemAnnex = MeetingFileTypeDescriptor('item-annex', 'Other annex(es)', 'attach.png', '')
annexeDecision = MeetingFileTypeDescriptor('annexeDecision', 'Annexe a la decision', 'attach.png', '', True)
# Some type of annexes taken from the default PloneMeeting test profile
marketingAnalysis = MeetingFileTypeDescriptor(
    'marketing-annex', 'Marketing annex(es)', 'attach.png', '', True,
    active=False)
overheadAnalysis = MeetingFileTypeDescriptor(
    'overhead-analysis', 'Administrative overhead analysis',
    'attach.png', '')

# Pod templates ----------------------------------------------------------------
agendaTemplate = PodTemplateDescriptor('agendaTemplate', 'Meeting agenda')
agendaTemplate.podTemplate = 'Agenda.odt'
agendaTemplate.podCondition = 'python:here.meta_type=="Meeting"'

decisionsTemplate = PodTemplateDescriptor('decisionsTemplate',
                                          'Meeting decisions')
decisionsTemplate.podTemplate = 'Decisions.odt'
decisionsTemplate.podCondition = 'python:here.meta_type=="Meeting" and ' \
                                 'here.adapted().isDecided()'

itemTemplate = PodTemplateDescriptor('itemTemplate', 'Meeting item')
itemTemplate.podTemplate = 'Item.odt'
itemTemplate.podCondition = 'python:here.meta_type=="MeetingItem"'

# Categories -------------------------------------------------------------------
categories = [
    CategoryDescriptor('deployment', 'Deployment topics'),
    CategoryDescriptor('maintenance', 'Maintenance topics'),
    CategoryDescriptor('development', 'Development topics'),
    CategoryDescriptor('events', 'Events'),
    CategoryDescriptor('research', 'Research topics'),
    CategoryDescriptor('projects', 'Projects'),
    # A vintage category
    CategoryDescriptor('marketing', 'Marketing', active=False),
    # usingGroups category
    CategoryDescriptor('subproducts', 'Subproducts wishes', usingGroups=('vendors',)),
]

# Users and groups -------------------------------------------------------------
admin = UserDescriptor('admin', ['Manager', 'MeetingManager'])
pmManager = UserDescriptor('pmManager', ['MeetingManager'])
pmCreator1 = UserDescriptor('pmCreator1', [])
pmCreator1b = UserDescriptor('pmCreator1b', [])
pmReviewer1 = UserDescriptor('pmReviewer1', [])
pmServiceHead1 = UserDescriptor('pmServiceHead1', [])
pmOfficeManager1 = UserDescriptor('pmOfficeManager1', [])
pmDivisionHead1 = UserDescriptor('pmDivisionHead1', [])
pmDirector1 = UserDescriptor('pmDirector1', [])
pmCreator2 = UserDescriptor('pmCreator2', [])
pmReviewer2 = UserDescriptor('pmReviewer2', [])
pmDirector2 = UserDescriptor('pmDirector2', [])
pmAdviser1 = UserDescriptor('pmAdviser1', [])
voter1 = UserDescriptor('voter1', [], fullname='M. Voter One')
voter2 = UserDescriptor('voter2', [], fullname='M. Voter Two')
powerobserver1 = UserDescriptor('powerobserver1', [], fullname='M. Power Observer1')
# powerobserver1 is MeetingPowerObserverLocal because in the meetingPma '_powerobservers' group
plonemeeting_assembly_powerobservers = PloneGroupDescriptor('meeting-config-council_powerobservers',
                                                            'meeting-config-council_powerobservers',
                                                            [])
powerobserver1.ploneGroups = [plonemeeting_assembly_powerobservers, ]
powerobserver2 = UserDescriptor('powerobserver2', [], fullname='M. Power Observer2')

# Add a vintage group
endUsers = GroupDescriptor('endUsers', 'End users', 'EndUsers', active=False)

developers = GroupDescriptor('developers', 'Developers', 'Devel', givesMandatoryAdviceOn="python:False")
developers.creators.append(pmCreator1)
developers.creators.append(pmCreator1b)
developers.creators.append(pmManager)
developers.creators.append(admin)
developers.serviceheads.append(pmReviewer1)
developers.serviceheads.append(pmServiceHead1)
developers.officemanagers.append(pmOfficeManager1)
developers.divisionheads.append(pmDivisionHead1)
developers.directors.append(pmDirector1)
developers.directors.append(pmReviewer1)
developers.directors.append(pmManager)
developers.directors.append(admin)
developers.reviewers.append(pmReviewer1)
developers.reviewers.append(pmManager)
developers.reviewers.append(admin)
developers.observers.append(pmReviewer1)
developers.observers.append(pmManager)
developers.observers.append(admin)
developers.advisers.append(pmAdviser1)
developers.advisers.append(pmManager)
setattr(developers, 'signatures', 'developers signatures')
setattr(developers, 'echevinServices', 'developers')

#give an advice on recurring items
vendors = GroupDescriptor('vendors', 'Vendors', 'Devil', givesMandatoryAdviceOn="python: item.id == 'recurringagenda1'")
vendors.creators.append(pmCreator2)
vendors.directors.append(pmReviewer2)
vendors.directors.append(pmDirector2)
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

pmManager_observer = MeetingUserDescriptor('pmManager',
                                           duty='Secretaire de la Chancellerie',
                                           usages=['assemblyMember'])
cadranel_signer = MeetingUserDescriptor('cadranel', duty='Secretaire',
                                        usages=['assemblyMember', 'signer'],
                                        signatureImage='SignatureCadranel.jpg',
                                        signatureIsDefault=True)
# Add meeting users (voting purposes)
muser_voter1 = MeetingUserDescriptor('voter1', duty='Voter1',
                                     usages=['assemblyMember', 'voter', ])
muser_voter2 = MeetingUserDescriptor('voter2', duty='Voter2',
                                     usages=['assemblyMember', 'voter', ])


# Meeting configurations -------------------------------------------------------
# college
collegeMeeting = MeetingConfigDescriptor(
    'meeting-config-college', 'Collège Communal',
    'Collège communal', isDefault=True)
collegeMeeting.assembly = 'Pierre Dupont - Bourgmestre,\n' \
                          'Charles Exemple - 1er Echevin,\n' \
                          'Echevin Un, Echevin Deux, Echevin Trois - Echevins,\n' \
                          'Jacqueline Exemple, Responsable du CPAS'
collegeMeeting.signatures = 'Pierre Dupont, Bourgmestre - Charles Exemple, 1er Echevin'
collegeMeeting.categories = categories
collegeMeeting.shortName = 'College'
collegeMeeting.meetingFileTypes = [annexe, annexeBudget, annexeCahier, itemAnnex,
                                   annexeDecision, overheadAnalysis, marketingAnalysis]
collegeMeeting.usedItemAttributes = ('toDiscuss', 'associatedGroups', 'itemIsSigned', 'motivation', )
collegeMeeting.xhtmlTransformFields = ('description', 'detailedDescription', 'decision',
                                       'observations', 'interventions', 'commissionTranscript')
collegeMeeting.xhtmlTransformTypes = ('removeBlanks',)
collegeMeeting.itemWorkflow = 'meetingitemcollegelalouviere_workflow'
collegeMeeting.meetingWorkflow = 'meetingcollegelalouviere_workflow'
collegeMeeting.itemConditionsInterface = 'Products.MeetingLalouviere.interfaces.IMeetingItemCollegeLalouviereWorkflowConditions'
collegeMeeting.itemActionsInterface = 'Products.MeetingLalouviere.interfaces.IMeetingItemCollegeLalouviereWorkflowActions'
collegeMeeting.meetingConditionsInterface = 'Products.MeetingLalouviere.interfaces.IMeetingCollegeLalouviereWorkflowConditions'
collegeMeeting.meetingActionsInterface = 'Products.MeetingLalouviere.interfaces.IMeetingCollegeLalouviereWorkflowActions'
collegeMeeting.itemTopicStates = ('itemcreated', 'proposed_to_servicehead', 'proposed_to_officemanager',
                                  'proposed_to_divisionhead', 'proposed_to_director', 'validated',
                                  'presented', 'itemfrozen', 'accepted', 'refused',
                                  'delayed', 'pre_accepted', 'removed',)
collegeMeeting.meetingTopicStates = ('created', 'frozen')
collegeMeeting.decisionTopicStates = ('decided', 'closed')
collegeMeeting.itemAdviceStates = ('validated',)
collegeMeeting.recordItemHistoryStates = ['', ]
collegeMeeting.useGroupsAsCategories = True
collegeMeeting.maxShownMeetings = 5
collegeMeeting.maxDaysDecisions = 60
collegeMeeting.meetingAppDefaultView = 'topic_searchmyitems'
collegeMeeting.itemDocFormats = ('odt', 'pdf')
collegeMeeting.meetingDocFormats = ('odt', 'pdf')
collegeMeeting.useAdvices = True
collegeMeeting.enforceAdviceMandatoriness = False
collegeMeeting.enableAdviceInvalidation = False
collegeMeeting.useCopies = True
collegeMeeting.selectableCopyGroups = [developers.getIdSuffixed('reviewers'), vendors.getIdSuffixed('reviewers'), ]
collegeMeeting.itemPowerObserversStates = ('itemcreated', 'presented', 'accepted', 'delayed', 'refused')
collegeMeeting.itemDecidedStates = ['accepted', 'refused', 'delayed', 'accepted_but_modified', 'pre_accepted']
collegeMeeting.sortingMethodOnAddItem = 'on_proposing_groups'
collegeMeeting.useGroupsAsCategories = True
collegeMeeting.defaultMeetingItemMotivation = """<p>Vu l'arrêté du Gouvernement Wallon du 22 avril 2004 portant codification de la législation relative aux pouvoirs locaux; dit le code de la démocratie locale et de la décentralisation;</p>
<p>Vu le décret du 27 mai 2004 portant confirmation dudit arrêté du gouvernement Wallon du 22 avril 2004;</p>
<p>Vu la nouvelle Loi communale;</p> <p>Vu l'article 123 de la nouvelle Loi communale;</p>
<p>Vu l'article L1123-23 du code de la Démocratie locale et de la Décentralisation;</p>"""
collegeMeeting.meetingUsers = []
collegeMeeting.podTemplates = [agendaTemplate, decisionsTemplate, itemTemplate]
collegeMeeting.meetingConfigsToCloneTo = ['meeting-config-council']
collegeMeeting.recurringItems = [
    RecurringItemDescriptor(
        id='recItem1',
        description='<p>This is the first recurring item.</p>',
        title='Recurring item #1',
        proposingGroup='',
        category='developers',
        decision='First recurring item approved'),

    RecurringItemDescriptor(
        id='recItem2',
        title='Recurring item #2',
        description='<p>This is the second recurring item.</p>',
        proposingGroup='',
        category='developers',
        decision='Second recurring item approved'),

    RecurringItemDescriptor(
        id='template1',
        title='Template 1',
        description='Template 1',
        category='',
        proposingGroup='developers',
        templateUsingGroups=['developers', 'vendors'],
        usages=['as_template_item', ],
        decision="""<p>Template 1.</p>"""),
    RecurringItemDescriptor(
        id='template2',
        title='Template 2',
        description='Template 2',
        category='',
        proposingGroup='vendors',
        templateUsingGroups=['vendors', ],
        usages=['as_template_item', ],
        decision="""
            <p>Template 2.</p>"""),
]

# Conseil communal
councilMeeting = MeetingConfigDescriptor(
    'meeting-config-council', 'Conseil Communal',
    'Conseil Communal')
councilMeeting.assembly = """M.J.GOBERT, Bourgmestre-Président
Mme A.SABBATINI, MM.J.GODIN, O.DESTREBECQ, G.HAINE,
Mmes A.DUPONT, F.GHIOT, M.J.C.WARGNIE, Echevins
Mme D.STAQUET, Présidente du CPAS
M.B.LIEBIN, Mme C.BURGEON, MM.M.DUBOIS, Y.DRUGMAND,
G.MAGGIORDOMO, O.ZRIHEN, M.DI MATTIA, Mme T.ROTOLO, M.F.ROMEO,
Mmes M.HANOT, I.VAN STEEN, MM.J.KEIJZER, A.FAGBEMI,
A.GAVA, A.POURBAIX, L.DUVAL, J.CHRISTIAENS, M.VAN HOOLAND,
Mme F.RMILI, MM.P.WATERLOT, A.BUSCEMI, L.WIMLOT,
Mme C.BOULANGIER, M.V.LIBOIS, Mme A.M.MARIN, MM.A.GOREZ,
J.P.MICHIELS, C.DELPLANCQ, Mmes F.VERMEER, L.BACCARELLA D'URSO,
M.C.LICATA et Mme M.ROLAND, Conseillers communaux
M.R.ANKAERT, Secrétaire
En présence de M.L.DEMOL, Chef de Corps, en ce qui concerne les points « Police »"""
councilMeeting.signatures = """Le Secrétaire,
R.ANKAERT
Le Président,
J.GOBERT"""
councilMeeting.defaultMeetingItemMotivation = """<p>Le Conseil,</p>
<p>&nbsp;</p>
<p>Vu, d'une part, l'arrêté du Gouvernement  Wallon du 22 avril 2004 portant codification de la législation relative aux pouvoirs locaux et d'autre part, le décret du 27 mai 2004 portant  confirmation dudit arrêté;</p>
<p>&nbsp;</p>
<p>Vu l'article 117 de la nouvelle Loi Communale;</p>
<p>&nbsp;</p>
<p>Vu l'article L 1122-30 du Code de Démocratie Locale et de la Décentralisation;</p>"""
councilMeeting.categories = categories
councilMeeting.shortName = 'Council'
councilMeeting.meetingFileTypes = [annexe, annexeBudget, annexeCahier, itemAnnex, annexeDecision]
councilMeeting.xhtmlTransformFields = ('description', 'detailedDescription', 'decision', 'observations',
                                       'interventions', 'commissionTranscript')
councilMeeting.xhtmlTransformTypes = ('removeBlanks',)
councilMeeting.usedItemAttributes = ['oralQuestion', 'itemInitiator', 'observations',
                                     'privacy', 'itemAssembly', 'itemIsSigned',
                                     'motivation', ]
councilMeeting.usedMeetingAttributes = (
    'place', 'observations', 'signatures', 'assembly', 'preMeetingDate', 'preMeetingPlace', 'preMeetingAssembly',
    'preMeetingDate_2', 'preMeetingPlace_2', 'preMeetingAssembly_2', 'preMeetingDate_3', 'preMeetingPlace_3',
    'preMeetingAssembly_3', 'preMeetingDate_4', 'preMeetingPlace_4', 'preMeetingAssembly_4', 'preMeetingDate_5',
    'preMeetingPlace_5', 'preMeetingAssembly_5', 'preMeetingDate_6', 'preMeetingPlace_6', 'preMeetingAssembly_6',
    'preMeetingDate_7', 'preMeetingPlace_7', 'preMeetingAssembly_7', 'startDate', 'endDate', )
councilMeeting.recordMeetingHistoryStates = []
councilMeeting.workflowAdaptations = ['return_to_proposing_group', ]
councilMeeting.itemWorkflow = 'meetingitemcouncillalouviere_workflow'
councilMeeting.meetingWorkflow = 'meetingcouncillalouviere_workflow'
councilMeeting.itemConditionsInterface = 'Products.MeetingLalouviere.interfaces.IMeetingItemCouncilLalouviereWorkflowConditions'
councilMeeting.itemActionsInterface = 'Products.MeetingLalouviere.interfaces.IMeetingItemCouncilLalouviereWorkflowActions'
councilMeeting.meetingConditionsInterface = 'Products.MeetingLalouviere.interfaces.IMeetingCouncilLalouviereWorkflowConditions'
councilMeeting.meetingActionsInterface = 'Products.MeetingLalouviere.interfaces.IMeetingCouncilLalouviereWorkflowActions'
#show every items states
councilMeeting.itemTopicStates = ('itemcreated', 'proposed_to_director', 'validated', 'presented', 'itemfrozen',
                                  'item_in_committee', 'item_in_council', 'returned_to_service', 'accepted',
                                  'accepted_but_modified', 'refused', 'delayed')
councilMeeting.meetingTopicStates = ('created', 'frozen', 'in_committee')
councilMeeting.decisionTopicStates = ('in_council', 'closed')
councilMeeting.itemAdviceStates = ('proposed_to_director', 'validated',)
councilMeeting.recordItemHistoryStates = ['', ]
councilMeeting.maxShownMeetings = 5
councilMeeting.maxDaysDecisions = 60
councilMeeting.meetingAppDefaultView = 'topic_searchmyitems'
councilMeeting.itemDocFormats = ('odt', 'pdf')
councilMeeting.meetingDocFormats = ('odt', 'pdf')
councilMeeting.useAdvices = True
councilMeeting.enforceAdviceMandatoriness = False
councilMeeting.enableAdviceInvalidation = False
councilMeeting.useCopies = True
councilMeeting.selectableCopyGroups = [developers.getIdSuffixed('reviewers'), vendors.getIdSuffixed('reviewers'), ]
councilMeeting.itemPowerObserversStates = collegeMeeting.itemPowerObserversStates
councilMeeting.itemDecidedStates = ['accepted', 'refused', 'delayed', 'accepted_but_modified']
councilMeeting.podTemplates = []
councilMeeting.transitionsToConfirm = ['MeetingItem.return_to_service', ]
councilMeeting.sortingMethodOnAddItem = 'on_categories'
councilMeeting.useGroupsAsCategories = False
councilMeeting.meetingUsers = [muser_voter1, muser_voter2, ]
councilMeeting.recurringItems = []

data = PloneMeetingConfiguration(
    meetingFolderTitle='Mes seances',
    meetingConfigs=(collegeMeeting, councilMeeting),
    groups=(developers, vendors, endUsers))
data.unoEnabledPython = '/usr/bin/python'
data.usersOutsideGroups = [voter1, voter2, powerobserver1, powerobserver2]
# ------------------------------------------------------------------------------
