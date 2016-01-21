# -*- coding: utf-8 -*-
from DateTime import DateTime
from Products.PloneMeeting.config import DEFAULT_LIST_TYPES
from Products.PloneMeeting.profiles import CategoryDescriptor
from Products.PloneMeeting.profiles import GroupDescriptor
from Products.PloneMeeting.profiles import ItemTemplateDescriptor
from Products.PloneMeeting.profiles import MeetingConfigDescriptor
from Products.PloneMeeting.profiles import MeetingFileTypeDescriptor
from Products.PloneMeeting.profiles import PodTemplateDescriptor
from Products.PloneMeeting.profiles import PloneMeetingConfiguration
from Products.PloneMeeting.profiles import RecurringItemDescriptor
from Products.PloneMeeting.profiles import UserDescriptor

today = DateTime().strftime('%Y/%m/%d')

# File types for College -------------------------------------------------------------------
annexe = MeetingFileTypeDescriptor('annexe', 'Annexe',
                                   'attach.png', '', isConfidentialDefault=True)
annexeBudget = MeetingFileTypeDescriptor('annexeBudget', 'Article Budgétaire',
                                         'budget.png', '', isConfidentialDefault=True)
annexeCahier = MeetingFileTypeDescriptor('annexeCahier',
                                         'Cahier des Charges',
                                         'cahier.gif',
                                         '')
courrierCollege = MeetingFileTypeDescriptor('courrier-a-valider-par-le-college',
                                            'Document soumis au Collège',
                                            'courrierCollege.png', '')
annexeDecision = MeetingFileTypeDescriptor('annexeDecision', 'Annexe à la décision',
                                           'attach.png', '', 'item_decision', isConfidentialDefault=True)
annexeAvis = MeetingFileTypeDescriptor('annexeAvis', 'Annexe à un avis',
                                       'attach.png', '', 'advice', isConfidentialDefault=True)
annexeAvisLegal = MeetingFileTypeDescriptor('annexeAvisLegal', 'Extrait article de loi',
                                            'legalAdvice.png', '', 'advice', isConfidentialDefault=True)

# Pod templates ----------------------------------------------------------------
agendaTemplate = PodTemplateDescriptor('oj', 'Ordre du jour')
agendaTemplate.odt_file = 'college-oj.odt'
agendaTemplate.pod_portal_types = ['MeetingCollege']
agendaTemplate.tal_condition = 'python: tool.isManager(here)'

agendaTemplatePDF = PodTemplateDescriptor('oj-pdf', 'Ordre du jour')
agendaTemplatePDF.odt_file = 'college-oj.odt'
agendaTemplatePDF.pod_formats = ['pdf', ]
agendaTemplatePDF.pod_portal_types = ['MeetingCollege']
agendaTemplatePDF.tal_condition = 'python: tool.isManager(here)'

decisionsTemplate = PodTemplateDescriptor('pv', 'Procès-verbal')
decisionsTemplate.odt_file = 'college-pv.odt'
decisionsTemplate.pod_portal_types = ['MeetingCollege']
decisionsTemplate.tal_condition = 'python: tool.isManager(here)'

decisionsTemplatePDF = PodTemplateDescriptor('pv-pdf', 'Procès-verbal')
decisionsTemplatePDF.odt_file = 'college-pv.odt'
decisionsTemplatePDF.pod_formats = ['pdf', ]
decisionsTemplatePDF.pod_portal_types = ['MeetingCollege']
decisionsTemplatePDF.tal_condition = 'python: tool.isManager(here)'

itemProjectTemplate = PodTemplateDescriptor('projet-deliberation', 'Projet délibération')
itemProjectTemplate.odt_file = 'projet-deliberation.odt'
itemProjectTemplate.pod_portal_types = ['MeetingItemCollege']
itemProjectTemplate.tal_condition = 'python: not here.hasMeeting()'

itemProjectTemplatePDF = PodTemplateDescriptor('projet-deliberation-pdf', 'Projet délibération')
itemProjectTemplatePDF.odt_file = 'projet-deliberation.odt'
itemProjectTemplatePDF.pod_formats = ['pdf', ]
itemProjectTemplatePDF.pod_portal_types = ['MeetingItemCollege']
itemProjectTemplatePDF.tal_condition = 'python: not here.hasMeeting()'

itemTemplate = PodTemplateDescriptor('deliberation', 'Délibération')
itemTemplate.odt_file = 'deliberation.odt'
itemTemplate.pod_portal_types = ['MeetingItemCollege']
itemTemplate.tal_condition = 'python: here.hasMeeting()'

itemTemplatePDF = PodTemplateDescriptor('deliberation-pdf', 'Délibération')
itemTemplatePDF.odt_file = 'deliberation.odt'
itemTemplatePDF.pod_formats = ['pdf', ]
itemTemplatePDF.pod_portal_types = ['MeetingItemCollege']
itemTemplatePDF.tal_condition = 'python: here.hasMeeting()'

dfAdviceTemplate = PodTemplateDescriptor('synthese-finance-advice', 'Synthèse Avis DF', dashboard=True)
dfAdviceTemplate.odt_file = 'synthese_avis_df.odt'
dfAdviceTemplate.pod_portal_types = ['Folder']
dfAdviceTemplate.dashboard_collections_ids = ['searchitemswithfinanceadvice']
dfAdviceTemplate.tal_condition = ''

collegeTemplates = [agendaTemplate, agendaTemplatePDF,
                    decisionsTemplate, decisionsTemplatePDF,
                    itemProjectTemplate, itemProjectTemplatePDF,
                    itemTemplate, itemTemplatePDF, dfAdviceTemplate]

councilTemplates = [agendaTemplate, agendaTemplatePDF,
                    decisionsTemplate, decisionsTemplatePDF,
                    itemProjectTemplate, itemProjectTemplatePDF,
                    itemTemplate, itemTemplatePDF]

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
dfcontrol = GroupDescriptor('df-contrale',
                            u'DF - Contrôle',
                            'DF')
dfcontrol.itemAdviceStates = ('meeting-config-college__state__itemfrozen',
                              'meeting-config-college__state__proposed_to_finance',
                              'meeting-config-college__state__presented',
                              'meeting-config-college__state__validated')
dfcontrol.itemAdviceEditStates = ('meeting-config-college__state__itemfrozen',
                                  'meeting-config-college__state__proposed_to_finance',
                                  'meeting-config-college__state__presented',
                                  'meeting-config-college__state__validated')
dfcontrol.itemAdviceViewStates = ('meeting-config-college__state__accepted',
                                  'meeting-config-college__state__accepted_but_modified',
                                  'meeting-config-college__state__pre_accepted',
                                  'meeting-config-college__state__delayed',
                                  'meeting-config-college__state__itemfrozen',
                                  'meeting-config-college__state__proposed_to_finance',
                                  'meeting-config-college__state__presented',
                                  'meeting-config-college__state__refused',
                                  'meeting-config-college__state__validated')
dfcompta = GroupDescriptor('df-comptabilita-c-et-audit-financier',
                           u'DF - Comptabilité et Audit financier',
                           'DF')
dfcompta.itemAdviceStates = ('meeting-config-college__state__itemfrozen',
                             'meeting-config-college__state__proposed_to_finance',
                             'meeting-config-college__state__presented',
                             'meeting-config-college__state__validated')
dfcompta.itemAdviceEditStates = ('meeting-config-college__state__itemfrozen',
                                 'meeting-config-college__state__proposed_to_finance',
                                 'meeting-config-college__state__presented',
                                 'meeting-config-college__state__validated')
dfcompta.itemAdviceViewStates = ('meeting-config-college__state__accepted',
                                 'meeting-config-college__state__accepted_but_modified',
                                 'meeting-config-college__state__pre_accepted',
                                 'meeting-config-college__state__delayed',
                                 'meeting-config-college__state__itemfrozen',
                                 'meeting-config-college__state__proposed_to_finance',
                                 'meeting-config-college__state__presented',
                                 'meeting-config-college__state__refused',
                                 'meeting-config-college__state__validated')

groups = [GroupDescriptor('dirgen', 'Directeur Général', 'DG'),
          GroupDescriptor('secretariat', 'Secrétariat communal', 'Secr'),
          GroupDescriptor('informatique', 'Service informatique', 'Info'),
          GroupDescriptor('personnel', 'Service du personnel', 'Pers'),
          GroupDescriptor('dirfin', 'Directeur Financier', 'DF'),
          GroupDescriptor('comptabilite', 'Service comptabilité', 'Compt'),
          GroupDescriptor('travaux', 'Service travaux', 'Trav'),
          dfcontrol,
          dfcompta]

# MeetingManager
groups[0].creators.append(dgen)
groups[0].reviewers.append(dgen)
groups[0].observers.append(dgen)
groups[0].advisers.append(dgen)

groups[1].creators.append(dgen)
groups[1].reviewers.append(dgen)
groups[1].observers.append(dgen)
groups[1].advisers.append(dgen)

groups[2].creators.append(agentInfo)
groups[2].creators.append(dgen)
groups[2].reviewers.append(agentInfo)
groups[2].reviewers.append(dgen)
groups[2].observers.append(agentInfo)
groups[2].advisers.append(agentInfo)

groups[3].creators.append(agentPers)
groups[3].observers.append(agentPers)
groups[3].creators.append(dgen)
groups[3].reviewers.append(dgen)
groups[3].creators.append(chefPers)
groups[3].reviewers.append(chefPers)
groups[3].observers.append(chefPers)
groups[3].observers.append(echevinPers)
groups[3].advisers.append(emetteuravisPers)

groups[4].creators.append(dfin)
groups[4].reviewers.append(dfin)
groups[4].observers.append(dfin)
groups[4].advisers.append(dfin)

groups[5].creators.append(agentCompta)
groups[5].creators.append(chefCompta)
groups[5].creators.append(dfin)
groups[5].creators.append(dgen)
groups[5].reviewers.append(chefCompta)
groups[5].reviewers.append(dfin)
groups[5].reviewers.append(dgen)
groups[5].observers.append(agentCompta)
groups[5].advisers.append(chefCompta)
groups[5].advisers.append(dfin)

groups[6].creators.append(agentTrav)
groups[6].creators.append(dgen)
groups[6].reviewers.append(agentTrav)
groups[6].reviewers.append(dgen)
groups[6].observers.append(agentTrav)
groups[6].observers.append(echevinTrav)
groups[6].advisers.append(agentTrav)

groups[7].creators.append(dfin)
groups[7].reviewers.append(dfin)
groups[7].observers.append(dfin)
groups[7].advisers.append(dfin)
groups[7].administrativereviewers.append(dfin)
groups[7].internalreviewers.append(dfin)

groups[8].creators.append(dfin)
groups[8].reviewers.append(dfin)
groups[8].observers.append(dfin)
groups[8].advisers.append(dfin)
groups[8].administrativereviewers.append(dfin)
groups[8].internalreviewers.append(dfin)

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
collegeMeeting.meetingFileTypes = [annexe, annexeBudget, annexeCahier, courrierCollege, annexeDecision]
collegeMeeting.enableAnnexConfidentiality = True
collegeMeeting.annexConfidentialFor = ('restricted_power_observers',)
collegeMeeting.usedItemAttributes = ['budgetInfos',
                                     'observations',
                                     'detailedDescription',
                                     'toDiscuss',
                                     'itemAssembly',
                                     'financeAdvice',
                                     'completeness',
                                     'labelForCouncil',
                                     'privacyForCouncil',
                                     'archivingRef',
                                     'motivation',
                                     'decisionSuite',
                                     'decisionEnd',
                                     'textCheckList', ]
collegeMeeting.usedMeetingAttributes = ['signatures',
                                        'assembly',
                                        'assemblyExcused',
                                        'observations', ]
collegeMeeting.xhtmlTransformFields = ('MeetingItem.description', 'MeetingItem.detailedDescription',
                                       'MeetingItem.decision', 'MeetingItem.observations', )
collegeMeeting.xhtmlTransformTypes = ('removeBlanks',)
collegeMeeting.meetingConfigsToCloneTo = ({'meeting_config': 'meeting-config-council',
                                           'trigger_workflow_transitions_until': '__nothing__'},)
collegeMeeting.itemAutoSentToOtherMCStates = ('sent_to_council_emergency', 'accepted',
                                              'accepted_but_modified', 'accepted_and_returned')
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
                                                              'item_transition': 'accept'},)
collegeMeeting.itemDecidedStates = ('accepted', 'accepted_but_modified', 'pre_accepted', 'refused', 'delayed',
                                    'accepted_and_returned', 'returned', 'marked_not_applicable',
                                    'sent_to_council_emergency')
collegeMeeting.meetingTopicStates = ('created', 'frozen')
collegeMeeting.decisionTopicStates = ('decided', 'closed')
# done in setuphandlers._configureCollegeCustomAdvisers
collegeMeeting.customAdvisers = []
collegeMeeting.powerAdvisersGroups = ('dirgen', 'dirfin')
collegeMeeting.itemPowerObserversStates = ('accepted', 'accepted_but_modified', 'accepted_and_returned',
                                           'pre_accepted', 'delayed', 'itemfrozen', 'marked_not_applicable',
                                           'validated', 'presented', 'refused', 'returned')
collegeMeeting.meetingPowerObserversStates = ('closed', 'created', 'decided', 'frozen')
collegeMeeting.meetingAppDefaultView = 'searchmyitems'
collegeMeeting.itemDocFormats = ('odt', 'pdf')
collegeMeeting.meetingDocFormats = ('odt', 'pdf')
collegeMeeting.useAdvices = True
collegeMeeting.usedAdviceTypes = ('positive_finance', 'positive_with_remarks_finance',
                                  'negative_finance', 'not_required_finance',
                                  'positive', 'positive_with_remarks', 'negative', 'nil')
collegeMeeting.itemAdviceStates = ('itemcreated_waiting_advices',
                                   'proposed_to_internal_reviewer_waiting_advices')
collegeMeeting.itemAdviceEditStates = ('itemcreated_waiting_advices',
                                       'proposed_to_internal_reviewer_waiting_advices')
collegeMeeting.itemAdviceViewStates = ('itemcreated_waiting_advices', 'proposed_to_administrative_reviewer',
                                       'proposed_to_internal_reviewer', 'proposed_to_internal_reviewer_waiting_advices',
                                       'proposed_to_director', 'validated', 'presented',
                                       'itemfrozen', 'refused', 'delayed',
                                       'pre_accepted', 'accepted', 'accepted_but_modified', )
collegeMeeting.transitionReinitializingDelays = 'backToProposedToDirector'
collegeMeeting.enforceAdviceMandatoriness = False
collegeMeeting.enableAdviceInvalidation = False
collegeMeeting.useCopies = True
collegeMeeting.selectableCopyGroups = [groups[0].getIdSuffixed('reviewers'),
                                       groups[1].getIdSuffixed('reviewers'),
                                       groups[2].getIdSuffixed('reviewers'),
                                       groups[3].getIdSuffixed('reviewers'),
                                       groups[4].getIdSuffixed('reviewers'),
                                       groups[5].getIdSuffixed('reviewers'),
                                       groups[6].getIdSuffixed('reviewers'), ]
collegeMeeting.itemCopyGroupsStates = ('accepted', 'accepted_but_modified', 'pre_accepted',
                                       'itemfrozen', 'refused', 'delayed')
collegeMeeting.podTemplates = collegeTemplates
collegeMeeting.insertingMethodsOnAddItem = ({'insertingMethod': 'on_categories',
                                             'reverse': '0'},
                                            {'insertingMethod': 'on_other_mc_to_clone_to',
                                             'reverse': '0'}, )
collegeMeeting.useGroupsAsCategories = False
collegeMeeting.recurringItems = [
    RecurringItemDescriptor(
        id='recurringagenda1',
        title='Approuve le procès-verbal de la séance antérieure',
        description='Approuve le procès-verbal de la séance antérieure',
        category='recurrents',
        proposingGroup='secretariat',
        decision='Procès-verbal approuvé'),
    RecurringItemDescriptor(
        id='recurringofficialreport1',
        title='Autorise et signe les bons de commande de la semaine',
        description='Autorise et signe les bons de commande de la semaine',
        category='recurrents',
        proposingGroup='secretariat',
        decision='Bons de commande signés'),
    RecurringItemDescriptor(
        id='recurringofficialreport2',
        title='Ordonnance et signe les mandats de paiement de la semaine',
        description='Ordonnance et signe les mandats de paiement de la semaine',
        category='recurrents',
        proposingGroup='secretariat',
        decision='Mandats de paiement de la semaine approuvés'), ]
collegeMeeting.meetingUsers = []
collegeMeeting.itemTemplates = [
    ItemTemplateDescriptor(
        id='template1',
        title='Tutelle CPAS',
        description='Tutelle CPAS',
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
        description='Contrôle médical systématique agent contractuel',
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
        description='Prestation réduite',
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
        description='Exemple modèle disponible pour tous',
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
    "python: 'Ref. ' + (here.hasMeeting() and here.restrictedTraverse('pm_unrestricted_methods').getLinkedMeetingDate().strftime('%Y%m%d') or '') + '/' + " \
    "str(here.getItemNumber(relativeTo='meeting'))"
councilMeeting.meetingFileTypes = [annexe, annexeBudget, annexeCahier, courrierCollege, annexeDecision]
councilMeeting.enableAnnexConfidentiality = True
councilMeeting.annexConfidentialFor = ('restricted_power_observers',)
councilMeeting.usedItemAttributes = ['budgetInfos',
                                     'labelForCouncil',
                                     'observations',
                                     'privacy',
                                     'itemAssembly',
                                     'motivation',
                                     'decisionSuite',
                                     'decisionEnd']
councilMeeting.usedMeetingAttributes = ['signatures',
                                        'assembly',
                                        'assemblyExcused',
                                        'observations', ]
councilMeeting.xhtmlTransformFields = ('MeetingItem.description', 'MeetingItem.detailedDescription',
                                       'MeetingItem.decision', 'MeetingItem.observations', )
councilMeeting.xhtmlTransformTypes = ('removeBlanks',)
councilMeeting.listTypes = DEFAULT_LIST_TYPES + [{'identifier': 'addendum',
                                                  'label': 'Addendum',
                                                  'used_in_inserting_method': ''}, ]
councilMeeting.itemAutoSentToOtherMCStates = ('delayed', 'returned')
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
                                                              'item_transition': 'accept'},)
councilMeeting.onTransitionFieldTransforms = (
    {'transition': 'present',
     'field_name': 'MeetingItem.decisionEnd',
     'tal_expression': 'python: here.adapted().adaptCouncilItemDecisionEnd()'},)
councilMeeting.itemDecidedStates = ('accepted', 'accepted_but_modified', 'pre_accepted',
                                    'delayed', 'returned', 'refused', 'marked_not_applicable')
councilMeeting.meetingTopicStates = ('created', 'frozen')
councilMeeting.decisionTopicStates = ('decided', 'closed')
councilMeeting.meetingAppDefaultView = 'searchmyitems'
councilMeeting.itemDocFormats = ('odt', 'pdf')
councilMeeting.meetingDocFormats = ('odt', 'pdf')
councilMeeting.useAdvices = False
councilMeeting.enforceAdviceMandatoriness = False
councilMeeting.enableAdviceInvalidation = False
councilMeeting.useCopies = True
councilMeeting.selectableCopyGroups = [groups[0].getIdSuffixed('reviewers'),
                                       groups[1].getIdSuffixed('reviewers'),
                                       groups[2].getIdSuffixed('reviewers'),
                                       groups[3].getIdSuffixed('reviewers'),
                                       groups[4].getIdSuffixed('reviewers'),
                                       groups[5].getIdSuffixed('reviewers'),
                                       groups[6].getIdSuffixed('reviewers'), ]
councilMeeting.itemCopyGroupsStates = ('accepted', 'accepted_but_modified',
                                       'pre_accepted', 'itemfrozen',
                                       'refused', 'delayed')
councilMeeting.podTemplates = councilTemplates
councilMeeting.insertingMethodsOnAddItem = ({'insertingMethod': 'on_categories',
                                             'reverse': '0'},)
councilMeeting.useGroupsAsCategories = False
councilMeeting.meetingUsers = []
councilMeeting.recurringItems = [
    RecurringItemDescriptor(
        id='recurringagenda1',
        title='Approuve le procès-verbal de la séance antérieure',
        description='Approuve le procès-verbal de la séance antérieure',
        category='recurrents',
        proposingGroup='secretariat',
        decision='Procès-verbal approuvé'),
    RecurringItemDescriptor(
        id='recurringofficialreport1',
        title='Autorise et signe les bons de commande de la semaine',
        description='Autorise et signe les bons de commande de la semaine',
        category='recurrents',
        proposingGroup='secretariat',
        decision='Bons de commande signés'),
    RecurringItemDescriptor(
        id='recurringofficialreport2',
        title='Ordonnance et signe les mandats de paiement de la semaine',
        description='Ordonnance et signe les mandats de paiement de la semaine',
        category='recurrents',
        proposingGroup='secretariat',
        decision='Mandats de paiement de la semaine approuvés'), ]

data = PloneMeetingConfiguration(meetingFolderTitle='Mes séances',
                                 meetingConfigs=(collegeMeeting, councilMeeting),
                                 groups=groups)
# ------------------------------------------------------------------------------
