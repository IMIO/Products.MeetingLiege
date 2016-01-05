# -*- coding: utf-8 -*-
#
# File: setuphandlers.py
#
# Copyright (c) 2015 by Imio.be
# Generator: ArchGenXML Version 2.7
#            http://plone.org/products/archgenxml
#
# GNU General Public License (GPL)
#

__author__ = """Gauthier Bastien <g.bastien@imio.be>"""
__docformat__ = 'plaintext'


import logging
logger = logging.getLogger('MeetingLiege: setuphandlers')
from Products.MeetingLiege.config import PROJECTNAME
from Products.MeetingLiege.config import DEPENDENCIES
import os
from Products.CMFCore.utils import getToolByName
import transaction
##code-section HEAD
from DateTime import DateTime
from imio.helpers.catalog import addOrUpdateColumns
from imio.helpers.catalog import addOrUpdateIndexes
from Products.PloneMeeting.exportimport.content import ToolInitializer
##/code-section HEAD

def isNotMeetingLiegeProfile(context):
    return context.readDataFile("MeetingLiege_marker.txt") is None



def updateRoleMappings(context):
    """after workflow changed update the roles mapping. this is like pressing
    the button 'Update Security Setting' and portal_workflow"""
    if isNotMeetingLiegeProfile(context): return
    wft = getToolByName(context.getSite(), 'portal_workflow')
    wft.updateRoleMappings()

def postInstall(context):
    """Called as at the end of the setup process. """
    # the right place for your custom code
    if isNotMeetingLiegeProfile(context):
        return
    site = context.getSite()
    # Reinstall PloneMeeting
    reinstallPloneMeeting(context, site)
    # reorder skins so we are sure that the meetingliege_xxx skins are just under custom
    reorderSkinsLayers(context, site)
    # set correct wf for meetingadvice
    setCorrectWorkflowForAdvices(context, site)
    # add getAdoptsNextCouncilAgenda metadata
    addOrUpdateColumns(site, ('getAdoptsNextCouncilAgenda', ))
    # add the groupsOfMatter index
    addOrUpdateIndexes(site, {'groupsOfMatter': ('KeywordIndex', {})})
    # add our own faceted advanced criteria
    #addFacetedCriteria(context, site)

##code-section FOOT
def logStep(method, context):
    logger.info("Applying '%s' in profile '%s'" % (method, '/'.join(context._profile_path.split(os.sep)[-3:])))


def isMeetingLiegeConfigureProfile(context):
    return context.readDataFile("MeetingLiege_liege_marker.txt") or \
        context.readDataFile("MeetingLiege_testing_marker.txt")


def installMeetingLiege(context):
    """ Run the default profile before being able to run the liege profile"""
    if not isMeetingLiegeConfigureProfile(context):
        return

    logStep("installMeetingLiege", context)
    portal = context.getSite()
    portal.portal_setup.runAllImportStepsFromProfile('profile-Products.MeetingLiege:default')


def reinstallPloneMeeting(context, site):
    '''Reinstall PloneMeeting so after install methods are called and applied,
       like performWorkflowAdaptations for example.'''

    if isNotMeetingLiegeProfile(context):
        return

    logStep("reinstallPloneMeeting", context)
    _installPloneMeeting(context)
    # launch skins step for MeetingLiege so MeetingLiege skin layers are before PM ones
    site.portal_setup.runImportStepFromProfile('profile-Products.MeetingLiege:default', 'skins')


def _installPloneMeeting(context):
    site = context.getSite()
    profileId = u'profile-Products.PloneMeeting:default'
    site.portal_setup.runAllImportStepsFromProfile(profileId)


def initializeTool(context):
    '''Initialises the PloneMeeting tool based on information from the current
       profile.'''
    if not isMeetingLiegeConfigureProfile(context):
        return

    logStep("initializeTool", context)
    _installPloneMeeting(context)
    return ToolInitializer(context, PROJECTNAME).run()


def reorderSkinsLayers(context, site):
    """
       Reinstall Products.plonemeetingskin and re-apply MeetingLiege skins.xml step
       as the reinstallation of MeetingLiege and PloneMeeting changes the portal_skins layers order
    """
    if isNotMeetingLiegeProfile(context) and not isMeetingLiegeConfigureProfile(context):
        return

    logStep("reorderSkinsLayers", context)
    try:
        site.portal_setup.runImportStepFromProfile(u'profile-Products.MeetingLiege:default', 'skins')
    except KeyError:
        # if the Products.plonemeetingskin profile is not available
        # (not using plonemeetingskin or in testing?) we pass...
        pass


def setCorrectWorkflowForAdvices(context, site):
    """
       We use a different workflow for advice, make 'meetingadvice' portal_type use it.
    """
    if isNotMeetingLiegeProfile(context) and not isMeetingLiegeConfigureProfile(context):
        return

    logStep("setCorrectWorkflowForAdvices", context)
    wfTool = getToolByName(site, 'portal_workflow')
    wfTool.setChainForPortalTypes(['meetingadvice'], ['meetingadviceliege_workflow'])
    # update role mappings of existing meetingadvice
    updateRoleMappings(context)
    # updateLocalRoles on every items again so advices are updated
    tool = getToolByName(site, 'portal_plonemeeting')
    tool.updateAllLocalRoles(meta_type=('MeetingItem', ))


def addFacetedCriteria(context, site):
    """ """
    logStep("addFacetedCriteria", context)
    tool = getToolByName(site, 'portal_plonemeeting')
    for cfg in tool.objectValues('MeetingConfig'):
        tool._enableFacetedDashboardFor(cfg.searches.searches_items,
                                        os.path.dirname(__file__) +
                                        '/faceted_conf/meetingliege_dashboard_items_widgets.xml')


def createArchivingReferences(context, site):
    """
       Create some MeetingConfig.archivingRefs if empty.
    """
    logStep("createArchivingReferences", context)
    cfg = getattr(site.portal_plonemeeting, 'meeting-config-college')
    if not cfg.getArchivingRefs():
        cfg.setArchivingRefs(
            (
                {'code': '1.1',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '001',
                 'finance_advice': 'no_finance_advice',
                 'label': "Permis d'urbanisme"},
                {'code': '1.2',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '002',
                 'finance_advice': 'no_finance_advice',
                 'label': 'Permis unique'},
                {'code': '1.3',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '003',
                 'finance_advice': 'no_finance_advice',
                 'label': 'Permis environnement'},
                {'code': '1.4',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '004',
                 'finance_advice': 'no_finance_advice',
                 'label': 'Enseignes et stores'},
                {'code': '1.5',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '005',
                 'finance_advice': 'no_finance_advice',
                 'label': 'Panneaux publicitaires'},
                {'code': '1.6',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '006',
                 'finance_advice': 'no_finance_advice',
                 'label': 'Certificat patrimoine'},
                {'code': '10.1',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '007',
                 'finance_advice': 'no_finance_advice',
                 'label': 'Taxes et redevances'},
                {'code': '10.10',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '008',
                 'finance_advice': 'df-comptabilita-c-et-audit-financier',
                 'label': 'Comptes'},
                {'code': '10.11',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '009',
                 'finance_advice': 'df-comptabilita-c-et-audit-financier',
                 'label': 'Emprunts'},
                {'code': '10.12',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '010',
                 'finance_advice': 'no_finance_advice',
                 'label': 'Contentieux'},
                {'code': '10.13',
                 'active': '0',
                 'restrict_to_groups': [],
                 'row_id': '011',
                 'finance_advice': 'no_finance_advice',
                 'label': 'Factures'},
                {'code': '10.2.1',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '012',
                 'finance_advice': 'df-contrale',
                 'label': 'Mise-en-non valeurs - prestations'},
                {'code': '10.2.2',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '013',
                 'finance_advice': 'df-contrale',
                 'label': 'Mise-en-non valeurs - locations'},
                {'code': '10.2.3',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '014',
                 'finance_advice': 'df-comptabilita-c-et-audit-financier',
                 'label': 'Mise-en-non valeurs - subventions'},
                {'code': '10.3.1',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '015',
                 'finance_advice': 'df-comptabilita-c-et-audit-financier',
                 'label': 'Donations et legs - biens immobiliers'},
                {'code': '10.3.2',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '016',
                 'finance_advice': 'df-comptabilita-c-et-audit-financier',
                 'label': 'Donations et legs - ouvrages et \xc5\x93uvres'},
                {'code': '10.3.3',
                 'active': '1',
                 'restrict_to_groups': [],
                 'row_id': '017',
                 'finance_advice': 'df-comptabilita-c-et-audit-financier',
                 'label': 'Donations et legs - capital'}))


def finalizeInstance(context):
    """
      Called at the very end of the installation process (after PloneMeeting).
    """
    if not isMeetingLiegeConfigureProfile(context):
        return

    site = context.getSite()
    createArchivingReferences(context, site)
    reorderSkinsLayers(context, site)
    reorderCss(context)
    # make sure we use the correct workflow for meetingadvice
    setCorrectWorkflowForAdvices(context, site)
    # create finance groups but not for the testing profile
    # or it mess tests computing available groups and so on
    # this method is called manually by relevant tests
    if not context.readDataFile("MeetingLiege_testing_marker.txt"):
        logStep("_createFinanceGroups", context)
        _createFinanceGroups(site)
        # populate the customAdvisers of 'meeting-config-college'
        logStep("_configureCollegeCustomAdvisers", context)
        _configureCollegeCustomAdvisers(site)


def _configureCollegeCustomAdvisers(site):
    '''
    '''
    today = DateTime().strftime('%Y/%m/%d')
    college = getattr(site.portal_plonemeeting, 'meeting-config-college')
    college.setCustomAdvisers([
        {'row_id': 'unique_id_002',
         'group': 'df-contrale',
         'gives_auto_advice_on': "python: item.adapted().needFinanceAdviceOf('df-contrale')",
         'for_item_created_from': today,
         'delay': '10',
         'delay_left_alert': '4',
         'delay_label': 'Incidence financière',
         'is_linked_to_previous_row': '0',
         },
        {'row_id': 'unique_id_003',
         'group': 'df-contrale',
         'for_item_created_from': today,
         'delay': '5',
         'delay_left_alert': '4',
         'delay_label': 'Incidence financière (Urgence)',
         'is_linked_to_previous_row': '1',
         },
        {'row_id': 'unique_id_004',
         'group': 'df-contrale',
         'for_item_created_from': today,
         'delay': '20',
         'delay_left_alert': '4',
         'delay_label': 'Incidence financière (Prolongation)',
         'is_linked_to_previous_row': '1',
         },
        {'row_id': 'unique_id_005',
         'group': 'df-comptabilita-c-et-audit-financier',
         'gives_auto_advice_on': "python: item.adapted().needFinanceAdviceOf('df-comptabilita-c-et-audit-financier')",
         'for_item_created_from': today,
         'delay': '10',
         'delay_left_alert': '4',
         'delay_label': 'Incidence financière',
         'is_linked_to_previous_row': '0',
         },
        {'row_id': 'unique_id_006',
         'group': 'df-comptabilita-c-et-audit-financier',
         'for_item_created_from': today,
         'delay': '5',
         'delay_left_alert': '4',
         'delay_label': 'Incidence financière (Urgence)',
         'is_linked_to_previous_row': '1',
         },
        {'row_id': 'unique_id_007',
         'group': 'df-comptabilita-c-et-audit-financier',
         'for_item_created_from': today,
         'delay': '20',
         'delay_left_alert': '4',
         'delay_label': 'Incidence financière (Prolongation)',
         'is_linked_to_previous_row': '1',
         }, ])


def _createFinanceGroups(site):
    """
       Create the finance groups.
    """
    financeGroupsData = ({'id': 'df-contrale',
                          'title': 'DF - Contrôle',
                          'acronym': 'DF', },
                         {'id': 'df-comptabilita-c-et-audit-financier',
                          'title': 'DF - Comptabilité et Audit financier',
                          'acronym': 'DF', },
                         )

    tool = getToolByName(site, 'portal_plonemeeting')
    for financeGroup in financeGroupsData:
        if not hasattr(tool, financeGroup['id']):
            newGroupId = tool.invokeFactory('MeetingGroup',
                                            id=financeGroup['id'],
                                            title=financeGroup['title'],
                                            acronym=financeGroup['acronym'],
                                            itemAdviceStates=('meeting-config-college__state__proposed_to_finance',
                                                              'meeting-config-college__state__presented',
                                                              'meeting-config-college__state__validated'),
                                            itemAdviceEditStates=('meeting-config-college__state__proposed_to_finance',
                                                                  'meeting-config-college__state__presented',
                                                                  'meeting-config-college__state__validated'),
                                            itemAdviceViewStates=('meeting-config-college__state__accepted',
                                                                  'meeting-config-college__state__accepted_but_modified',
                                                                  'meeting-config-college__state__pre_accepted',
                                                                  'meeting-config-college__state__delayed',
                                                                  'meeting-config-college__state__itemfrozen',
                                                                  'meeting-config-college__state__proposed_to_finance',
                                                                  'meeting-config-college__state__presented',
                                                                  'meeting-config-college__state__refused',
                                                                  'meeting-config-college__state__removed',
                                                                  'meeting-config-college__state__validated'))
            newGroup = getattr(tool, newGroupId)
            newGroup.processForm(values={'dummy': None})


def reorderCss(context):
    """
       Make sure CSS are correctly reordered in portal_css so things
       work as expected...
    """
    site = context.getSite()
    logStep("reorderCss", context)
    portal_css = site.portal_css
    css = ['plonemeeting.css',
           'meeting.css',
           'meetingitem.css',
           'meetingliege.css',
           'imioapps.css',
           'plonemeetingskin.css',
           'imioapps_IEFixes.css',
           'ploneCustom.css']
    for resource in css:
        portal_css.moveResourceToBottom(resource)

##/code-section FOOT
