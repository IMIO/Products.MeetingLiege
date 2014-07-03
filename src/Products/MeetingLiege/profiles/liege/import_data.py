# -*- coding: utf-8 -*-
from DateTime import DateTime
from Products.PloneMeeting.profiles import *

today = DateTime().strftime('%Y/%m/%d')

# File types -------------------------------------------------------------------
annexe = MeetingFileTypeDescriptor('annexe', 'Annexe',
                                   'attach.png', '')
annexeBudget = MeetingFileTypeDescriptor('annexeBudget', 'Article Budgétaire',
                                         'budget.png', '')
annexeCahier = MeetingFileTypeDescriptor('annexeCahier', 'Cahier des Charges',
                                         'cahier.gif', '')
annexeDecision = MeetingFileTypeDescriptor('annexeDecision', 'Annexe à la décision',
                                           'attach.png', '', 'item_decision')
annexeAvis = MeetingFileTypeDescriptor('annexeAvis', 'Annexe à un avis',
                                       'attach.png', '', 'advice')
annexeAvisLegal = MeetingFileTypeDescriptor('annexeAvisLegal', 'Extrait article de loi',
                                            'legalAdvice.png', '', 'advice')

# Pod templates ----------------------------------------------------------------
agendaTemplate = PodTemplateDescriptor('oj', 'Ordre du jour')
agendaTemplate.podTemplate = 'college-oj.odt'
agendaTemplate.podCondition = 'python:(here.meta_type=="Meeting") and here.portal_plonemeeting.isManager()'

agendaTemplatePDF = PodTemplateDescriptor('oj-pdf', 'Ordre du jour')
agendaTemplatePDF.podTemplate = 'college-oj.odt'
agendaTemplatePDF.podFormat = 'pdf'
agendaTemplatePDF.podCondition = 'python:(here.meta_type=="Meeting") and here.portal_plonemeeting.isManager()'

decisionsTemplate = PodTemplateDescriptor('pv', 'Procès-verbal')
decisionsTemplate.podTemplate = 'college-pv.odt'
decisionsTemplate.podCondition = 'python:(here.meta_type=="Meeting") and here.portal_plonemeeting.isManager()'

decisionsTemplatePDF = PodTemplateDescriptor('pv-pdf', 'Procès-verbal')
decisionsTemplatePDF.podTemplate = 'college-pv.odt'
decisionsTemplatePDF.podFormat = 'pdf'
decisionsTemplatePDF.podCondition = 'python:(here.meta_type=="Meeting") and here.portal_plonemeeting.isManager()'

itemProjectTemplate = PodTemplateDescriptor('projet-deliberation', 'Projet délibération')
itemProjectTemplate.podTemplate = 'projet-deliberation.odt'
itemProjectTemplate.podCondition = 'python:here.meta_type=="MeetingItem" and not here.hasMeeting()'

itemProjectTemplatePDF = PodTemplateDescriptor('projet-deliberation-pdf', 'Projet délibération')
itemProjectTemplatePDF.podTemplate = 'projet-deliberation.odt'
itemProjectTemplatePDF.podFormat = 'pdf'
itemProjectTemplatePDF.podCondition = 'python:here.meta_type=="MeetingItem" and not here.hasMeeting()'

itemTemplate = PodTemplateDescriptor('deliberation', 'Délibération')
itemTemplate.podTemplate = 'deliberation.odt'
itemTemplate.podCondition = 'python:here.meta_type=="MeetingItem" and here.hasMeeting()'

itemTemplatePDF = PodTemplateDescriptor('deliberation-pdf', 'Délibération')
itemTemplatePDF.podTemplate = 'deliberation.odt'
itemTemplatePDF.podFormat = 'pdf'
itemTemplatePDF.podCondition = 'python:here.meta_type=="MeetingItem" and here.hasMeeting()'

collegeTemplates = [agendaTemplate, agendaTemplatePDF,
                    decisionsTemplate, decisionsTemplatePDF,
                    itemProjectTemplate, itemProjectTemplatePDF,
                    itemTemplate, itemTemplatePDF]

# Users and groups -------------------------------------------------------------
dgen = UserDescriptor('dgen', ['MeetingManager'], email="test@test.be", fullname="Henry Directeur")
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
                                  'meeting-config-college__state__removed',
                                  'meeting-config-college__state__validated')
dfcompta = GroupDescriptor('df-comptabilita-c-et-audit-financier',
                           u'DF - Comptabilité et Audit financier',
                           'DF')
dfcompta.itemAdviceStates = ('meeting-config-college__state__itemfrozen',
                             'meeting-config-college__state__proposed_to_finance',
                             'meeting-config-college__state__presented',
                             'meeting-config-college__state__validated'),
dfcompta.itemAdviceEditStates = ('meeting-config-college__state__itemfrozen',
                                 'meeting-config-college__state__proposed_to_finance',
                                 'meeting-config-college__state__presented',
                                 'meeting-config-college__state__validated'),
dfcompta.itemAdviceViewStates = ('meeting-config-college__state__accepted',
                                 'meeting-config-college__state__accepted_but_modified',
                                 'meeting-config-college__state__pre_accepted',
                                 'meeting-config-college__state__delayed',
                                 'meeting-config-college__state__itemfrozen',
                                 'meeting-config-college__state__proposed_to_finance',
                                 'meeting-config-college__state__presented',
                                 'meeting-config-college__state__refused',
                                 'meeting-config-college__state__removed',
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

# Meeting configurations -------------------------------------------------------
# college
collegeMeeting = MeetingConfigDescriptor(
    'meeting-config-college', 'Collège Communal',
    'Collège Communal', isDefault=True)
collegeMeeting.assembly = 'Pierre Dupont - Bourgmestre,\n' \
                          'Charles Exemple - 1er Echevin,\n' \
                          'Echevin Un, Echevin Deux, Echevin Trois - Echevins,\n' \
                          'Jacqueline Exemple, Responsable du CPAS'
collegeMeeting.signatures = 'Pierre Dupont, Bourgmestre - Charles Exemple, 1er Echevin'
categoriesCollege = [CategoryDescriptor('cat-coll-1', u'Catégorie collège 1'),
                     CategoryDescriptor('cat-coll-2', u'Catégorie collège 2'),
                     CategoryDescriptor('cat-coll-3', u'Catégorie collège 3'),
                     CategoryDescriptor('cat-coll-4', u'Catégorie collège 4'),
                     CategoryDescriptor('cat-coll-5', u'Catégorie collège 5'),
                     CategoryDescriptor('cat-coll-6', u'Catégorie collège 6'), ]
collegeMeeting.categories = categoriesCollege
collegeMeeting.shortName = 'College'
collegeMeeting.meetingFileTypes = [annexe, annexeBudget, annexeCahier, annexeDecision]
collegeMeeting.usedItemAttributes = ['budgetInfos',
                                     'observations',
                                     'toDiscuss',
                                     'itemAssembly',
                                     'completeness',
                                     'titleForCouncil',
                                     'privacyForCouncil',
                                     'archivingRef',
                                     'motivation',
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
collegeMeeting.itemDecidedStates = ('accepted', 'accepted_but_modified', 'pre_accepted', 'refused', 'delayed', 'removed')
collegeMeeting.meetingTopicStates = ('created', 'frozen')
collegeMeeting.decisionTopicStates = ('decided', 'closed')
collegeMeeting.itemsListVisibleColumns = ['state', 'proposingGroupAcronym', 'advices',
                                          'annexes', 'annexesDecision', 'actions']
collegeMeeting.itemColumns = ['creationDate', 'creator', 'state', 'annexes', 'annexesDecision',
                              'proposingGroupAcronym', 'advices', 'actions', 'meeting']
collegeMeeting.customAdvisers = [
    {'row_id': 'unique_id_002',
     'group': 'df-contrale',
     'gives_auto_advice_on': "python: item.adapted().needFinanceAdviceOf('df-contrale')",
     'for_item_created_from': today,
     'delay': '10',
     'delay_left_alert': '4',
     'delay_label': u'Incidence financière',
     },
    {'row_id': 'unique_id_003',
     'group': 'df-contrale',
     'for_item_created_from': today,
     'delay': '5',
     'delay_left_alert': '4',
     'delay_label': u'Incidence financière (Urgence)',
     'is_linked_to_previous_row': '1',
     },
    {'row_id': 'unique_id_004',
     'group': 'df-contrale',
     'for_item_created_from': today,
     'delay': '20',
     'delay_left_alert': '4',
     'delay_label': u'Incidence financière (Prolongation)',
     'is_linked_to_previous_row': '1',
     },
    {'row_id': 'unique_id_005',
     'group': 'df-comptabilita-c-et-audit-financier',
     'gives_auto_advice_on': "python: item.adapted().needFinanceAdviceOf('df-comptabilita-c-et-audit-financier')",
     'for_item_created_from': today,
     'delay': '10',
     'delay_left_alert': '4',
     'delay_label': u'Incidence financière',
     },
    {'row_id': 'unique_id_006',
     'group': 'df-comptabilita-c-et-audit-financier',
     'for_item_created_from': today,
     'delay': '5',
     'delay_left_alert': '4',
     'delay_label': u'Incidence financière (Urgence)',
     'is_linked_to_previous_row': '1',
     },
    {'row_id': 'unique_id_007',
     'group': 'df-comptabilita-c-et-audit-financier',
     'for_item_created_from': today,
     'delay': '20',
     'delay_left_alert': '4',
     'delay_label': u'Incidence financière (Prolongation)',
     'is_linked_to_previous_row': '1',
     }, ]

collegeMeeting.powerAdvisersGroups = ('dirgen', 'dirfin')
collegeMeeting.meetingAppDefaultView = 'topic_searchmyitems'
collegeMeeting.itemDocFormats = ('odt', 'pdf')
collegeMeeting.meetingDocFormats = ('odt', 'pdf')
collegeMeeting.useAdvices = True
collegeMeeting.usedAdviceTypes = ('positive_finance', 'negative_finance', 'not_required_finance',
                                  'positive', 'positive_with_remarks', 'negative', 'nil')
collegeMeeting.itemAdviceStates = ('itemcreated_waiting_advices',
                                   'proposed_to_internal_reviewer_waiting_advices')
collegeMeeting.itemAdviceEditStates = ('itemcreated_waiting_advices',
                                       'proposed_to_internal_reviewer_waiting_advices')
collegeMeeting.itemAdviceViewStates = ('itemcreated_waiting_advices', 'proposed_to_administrative_reviewer',
                                       'proposed_to_internal_reviewer', 'proposed_to_internal_reviewer_waiting_advices',
                                       'proposed_to_director', 'validated', 'presented',
                                       'itemfrozen', 'refused', 'delayed', 'removed',
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
collegeMeeting.itemCopyGroupsStates = ('accepted', 'accepted_but_modified', 'pre_accepted', 'itemfrozen', 'refused', 'delayed', 'removed')
collegeMeeting.podTemplates = collegeTemplates
collegeMeeting.insertingMethodsOnAddItem = ({'insertingMethod': 'on_categories',
                                             'reverse': '0'},
                                            {'insertingMethod': 'on_other_mc_to_clone_to',
                                             'reverse': '0'}, )
collegeMeeting.useGroupsAsCategories = False
collegeMeeting.recurringItems = []
collegeMeeting.meetingUsers = []
collegeMeeting.recurringItems = [
    RecurringItemDescriptor(
        id='recurringagenda1',
        title='Approuve le procès-verbal de la séance antérieure',
        description='Approuve le procès-verbal de la séance antérieure',
        proposingGroup='',
        decision='Procès-verbal approuvé'),
    RecurringItemDescriptor(
        id='recurringofficialreport1',
        title='Autorise et signe les bons de commande de la semaine',
        description='Autorise et signe les bons de commande de la semaine',
        proposingGroup='',
        decision='Bons de commande signés'),
    RecurringItemDescriptor(
        id='recurringofficialreport2',
        title='Ordonnance et signe les mandats de paiement de la semaine',
        description='Ordonnance et signe les mandats de paiement de la semaine',
        proposingGroup='',
        decision='Mandats de paiement de la semaine approuvés'),
    RecurringItemDescriptor(
        id='template1',
        title='Tutelle CPAS',
        description='Tutelle CPAS',
        proposingGroup='',
        templateUsingGroups=[],
        usages=['as_template_item', ],
        decision="""<p>Vu la loi du 8 juillet 1976 organique des centres publics d'action sociale et plus particulièrement son article 111;</p>
        <p>Vu l'Arrêté du Gouvernement Wallon du 22 avril 2004 portant codification de la législation relative aux pouvoirs locaux tel que confirmé par le décret du 27 mai 2004 du Conseil régional wallon;</p>
        <p>Attendu que les décisions suivantes du Bureau permanent/du Conseil de l'Action sociale du XXX ont été reçues le XXX dans le cadre de la tutelle générale sur les centres publics d'action sociale :</p>
        <p>- ...;</p>
        <p>- ...;</p>
        <p>- ...</p>
        <p>Attendu que ces décisions sont conformes à la loi et à l'intérêt général;</p>
        <p>Déclare à l'unanimité que :</p>
        <p><strong>Article 1er :</strong></p>
        <p>Les décisions du Bureau permanent/Conseil de l'Action sociale visées ci-dessus sont conformes à la loi et à l'intérêt général et qu'il n'y a, dès lors, pas lieu de les annuler.</p>
        <p><strong>Article 2 :</strong></p>
        <p>Copie de la présente délibération sera transmise au Bureau permanent/Conseil de l'Action sociale.</p>"""),
    RecurringItemDescriptor(
        id='template2',
        title='Contrôle médical systématique agent contractuel',
        description='Contrôle médical systématique agent contractuel',
        proposingGroup='',
        templateUsingGroups=[],
        usages=['as_template_item', ],
        decision="""
        <p>Vu la loi du 26 mai 2002 instituant le droit à l’intégration sociale;</p>
        <p>Vu la délibération du Conseil communal du 29 juin 2009 concernant le cahier spécial des charges relatif au marché de services portant sur le contrôle des agents communaux absents pour raisons médicales;</p>
        <p>Vu sa délibération du 17 décembre 2009 désignant le docteur XXX en qualité d’adjudicataire pour la mission de contrôle médical des agents de l’Administration communale;</p>
        <p>Vu également sa décision du 17 décembre 2009 d’opérer les contrôles médicaux de manière systématique et pour une période d’essai d’un trimestre;</p>
        <p>Attendu qu’un certificat médical a été  reçu le XXX concernant XXX la couvrant du XXX au XXX, avec la mention « XXX »;</p>
        <p>Attendu que le Docteur XXX a transmis au service du Personnel, par fax, le même jour à XXX le rapport de contrôle mentionnant l’absence de XXX ce XXX à XXX;</p>
        <p>Considérant que XXX avait été informée par le Service du Personnel de la mise en route du système de contrôle systématique que le médecin-contrôleur;</p>
        <p>Considérant qu’ayant été absent(e) pour maladie la semaine précédente elle avait reçu la visite du médecin-contrôleur;</p>
        <p>DECIDE :</p>
        <p><strong>Article 1</strong> : De convoquer XXX devant  Monsieur le Secrétaire communal f.f. afin de lui rappeler ses obligations en la matière.</p>
        <p><strong>Article 2</strong> :  De prévenir XXX, qu’en cas de récidive, il sera proposé par le Secrétaire communal au Collège de transformer les jours de congés de maladie en absence injustifiée (retenue sur traitement avec application de la loi du 26 mai 2002 citée ci-dessus).</p>
        <p><strong>Article 3</strong> : De charger le service du personnel du suivi de ce dossier.</p>"""),
    RecurringItemDescriptor(
        id='template4',
        title='Prestation réduite',
        description='Prestation réduite',
        proposingGroup='',
        templateUsingGroups=[],
        usages=['as_template_item', ],
        decision="""<p>Vu la loi de redressement du 22 janvier 1985 (article 99 et suivants) et de l’Arrêté Royal du 12 août 1991 (tel que modifié) relatifs à l’interruption de carrière professionnelle dans l’enseignement;</p>
        <p>Vu la lettre du XXX par laquelle Madame XXX, institutrice maternelle, sollicite le renouvellement pendant l’année scolaire 2009/2010 de son congé pour prestations réduites mi-temps pour convenances personnelles dont elle bénéficie depuis le 01 septembre 2006;</p>
        <p>Attendu que le remplacement de l’intéressée&nbsp;est assuré pour la prochaine rentrée scolaire;</p>
        <p>Vu le décret de la Communauté Française du 13 juillet 1988 portant restructuration de l’enseignement maternel et primaire ordinaires avec effet au 1er octobre 1998;</p>
        <p>Vu la loi du 29 mai 1959 (Pacte Scolaire) et les articles L1122-19 et L1213-1 du code de la démocratie locale et de la décentralisation;</p>
        <p>Vu l’avis favorable de l’Echevin de l’Enseignement;</p>
        <p><b>DECIDE&nbsp;:</b><br><b><br> Article 1<sup>er</sup></b>&nbsp;:</p>
        <p>Au scrutin secret et à l’unanimité, d’accorder à Madame XXX le congé pour prestations réduites mi-temps sollicité pour convenances personnelles en qualité d’institutrice maternelle aux écoles communales fondamentales&nbsp;&nbsp;de Sambreville (section de XXX).</p>
        <p><b>Article 2</b> :</p>
        <p>Une activité lucrative est autorisée durant ce congé qui est assimilé à une période d’activité de service, dans le respect de la réglementation relative au cumul.</p>
        <p><b>Article 3&nbsp;:</b></p>
        <p>La présente délibération sera soumise pour accord au prochain Conseil, transmise au Bureau Régional de l’Enseignement primaire et maternel, à&nbsp;l’Inspectrice Cantonale, à la direction concernée et à l’intéressée.</p>"""),
    RecurringItemDescriptor(
        id='template5',
        title='Exemple modèle disponible pour tous',
        description='Exemple modèle disponible pour tous',
        proposingGroup='',
        templateUsingGroups=[],
        usages=['as_template_item', ],
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
councilMeeting.assembly = 'Pierre Dupont - Bourgmestre,\n' \
                          'Charles Exemple - 1er Echevin,\n' \
                          'Echevin Un, Echevin Deux, Echevin Trois - Echevins,\n' \
                          'Jacqueline Exemple, Responsable du CPAS'
councilMeeting.signatures = 'Pierre Dupont, Bourgmestre - Charles Exemple, 1er Echevin'
categoriesCouncil = [CategoryDescriptor('cat-council-1', u'Catégorie conseil 1'),
                     CategoryDescriptor('cat-council-2', u'Catégorie conseil 2'),
                     CategoryDescriptor('cat-council-3', u'Catégorie conseil 3'),
                     CategoryDescriptor('cat-council-4', u'Catégorie conseil 4'),
                     CategoryDescriptor('cat-council-5', u'Catégorie conseil 5'),
                     CategoryDescriptor('cat-council-6', u'Catégorie conseil 6'), ]
councilMeeting.categories = categoriesCouncil
councilMeeting.shortName = 'Council'
councilMeeting.meetingFileTypes = [annexe, annexeBudget, annexeCahier, annexeDecision]
councilMeeting.usedItemAttributes = ['budgetInfos',
                                     'observations',
                                     'itemAssembly',
                                     'motivation', ]
councilMeeting.usedMeetingAttributes = ['signatures',
                                        'assembly',
                                        'assemblyExcused',
                                        'observations', ]
councilMeeting.xhtmlTransformFields = ('MeetingItem.description', 'MeetingItem.detailedDescription',
                                       'MeetingItem.decision', 'MeetingItem.observations', )
councilMeeting.xhtmlTransformTypes = ('removeBlanks',)
councilMeeting.itemWorkflow = 'meetingitemcouncilliege_workflow'
councilMeeting.meetingWorkflow = 'meetingcouncilliege_workflow'
councilMeeting.itemConditionsInterface = 'Products.MeetingLiege.interfaces.IMeetingItemCouncilLiegeWorkflowConditions'
councilMeeting.itemActionsInterface = 'Products.MeetingLiege.interfaces.IMeetingItemCouncilLiegeWorkflowActions'
councilMeeting.meetingConditionsInterface = 'Products.MeetingLiege.interfaces.IMeetingCouncilLiegeWorkflowConditions'
councilMeeting.meetingActionsInterface = 'Products.MeetingLiege.interfaces.IMeetingCouncilLiegeWorkflowActions'
councilMeeting.transitionsForPresentingAnItem = ('present', )
councilMeeting.meetingTopicStates = ('created', 'frozen')
councilMeeting.decisionTopicStates = ('decided', 'closed')
councilMeeting.meetingAppDefaultView = 'topic_searchmyitems'
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
councilMeeting.itemCopyGroupsStates = ('accepted', 'accepted_but_modified', 'pre_accepted', 'itemfrozen', 'refused', 'delayed', 'removed')
councilMeeting.podTemplates = collegeTemplates
councilMeeting.insertingMethodsOnAddItem = ({'insertingMethod': 'on_categories',
                                             'reverse': '0'},)
councilMeeting.useGroupsAsCategories = False
councilMeeting.recurringItems = []
councilMeeting.meetingUsers = []


data = PloneMeetingConfiguration(meetingFolderTitle='Mes séances',
                                 meetingConfigs=(collegeMeeting, councilMeeting),
                                 groups=groups)
data.unoEnabledPython = '/usr/bin/python'
data.usedColorSystem = 'state_color'
# ------------------------------------------------------------------------------
