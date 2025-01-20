# -*- coding: utf-8 -*-

from dexterity.localroles.utils import add_fti_configuration
from imio.helpers.catalog import addOrUpdateColumns
from Products.CMFCore.utils import getToolByName
from Products.MeetingLiege.config import PROJECTNAME
from Products.PloneMeeting.exportimport.content import ToolInitializer
from Products.PloneMeeting.utils import org_id_to_uid

import logging
import os


__author__ = """Gauthier Bastien <g.bastien@imio.be>"""
__docformat__ = 'plaintext'
logger = logging.getLogger('MeetingLiege: setuphandlers')


def isNotMeetingLiegeProfile(context):
    return context.readDataFile("MeetingLiege_marker.txt") is None


def updateRoleMappings(context):
    """after workflow changed update the roles mapping. this is like pressing
    the button 'Update Security Setting' and portal_workflow"""
    if isNotMeetingLiegeProfile(context):
        return
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
    # configure localroles field for meetingadvicefinances
    _configureDexterityLocalRolesField()
    # add category_id metadata
    addOrUpdateColumns(site, ('category_id', ))


def logStep(method, context):
    logger.info("Applying '%s' in profile '%s'" % (method, '/'.join(context._profile_path.split(os.sep)[-3:])))


def isMeetingLiegeConfigureProfile(context):
    return context.readDataFile("MeetingLiege_liege_marker.txt") or \
        context.readDataFile("MeetingLiege_testing_marker.txt") or \
        context.readDataFile("MeetingLiege_bourgmestre_marker.txt")


def installMeetingLiege(context):
    """ Run the default profile before being able to run the liege profile"""
    if not isMeetingLiegeConfigureProfile(context):
        return

    logStep("installMeetingLiege", context)
    portal = context.getSite()
    if not portal.portal_quickinstaller.isProductInstalled('MeetingLiege'):
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


def _installPloneMeeting(context, force=False):
    site = context.getSite()
    if not site.portal_quickinstaller.isProductInstalled('PloneMeeting') or not force:
        profileId = u'profile-Products.PloneMeeting:default'
        site.portal_setup.runAllImportStepsFromProfile(profileId)


def initializeTool(context):
    '''Initialises the PloneMeeting tool based on information from the current
       profile.'''
    if not isMeetingLiegeConfigureProfile(context):
        return

    logStep("initializeTool", context)
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


def addFacetedCriteria(context, site):
    """ """
    logStep("addFacetedCriteria", context)
    tool = getToolByName(site, 'portal_plonemeeting')
    for cfg in tool.objectValues('MeetingConfig'):
        tool._enableFacetedDashboardFor(cfg.searches.searches_items,
                                        os.path.dirname(__file__) +
                                        '/faceted_conf/meetingliege_dashboard_items_widgets.xml')


def _configureDexterityLocalRolesField():
    """Configure field meetingadvice.advice_group for meetingadvicefinances."""
    # meetingadvicefinances
    roles_config = {
        'advice_group': {
            'advice_given': {
                'advisers': {'roles': [], 'rel': ''}},
            'proposed_to_financial_controller': {
                u'financialcontrollers': {'roles': [u'Editor', u'Reviewer'], 'rel': ''}},
            'proposed_to_financial_reviewer': {
                u'financialreviewers': {'roles': [u'Editor', u'Reviewer'], 'rel': ''}},
            'proposed_to_financial_manager': {
                u'financialmanagers': {'roles': [u'Editor', u'Reviewer'], 'rel': ''}},
            'financial_advice_signed': {
                u'financialmanagers': {'roles': [], 'rel': ''}},
        }
    }
    msg = add_fti_configuration(portal_type='meetingadvicefinances',
                                configuration=roles_config['advice_group'],
                                keyname='advice_group',
                                force=True)
    if msg:
        logger.warn(msg)


def finalizeInstance(context):
    """
      Called at the very end of the installation process (after PloneMeeting).
    """
    if not isMeetingLiegeConfigureProfile(context):
        return

    site = context.getSite()
    reorderSkinsLayers(context, site)
    reorderCss(context)
    # create finance groups but not for the testing profile
    # or it mess tests computing available groups and so on
    # this method is called manually by relevant tests
    if not context.readDataFile("MeetingLiege_testing_marker.txt"):
        # populate the customAdvisers of 'meeting-config-college'
        logStep("_configureCollegeCustomAdvisers", context)
        _configureCollegeCustomAdvisers(site)


def _configureCollegeCustomAdvisers(site):
    '''
    '''
    college = getattr(site.portal_plonemeeting, 'meeting-config-college', None)
    if college and not college.getCustomAdvisers():
        college.setCustomAdvisers((
            {'delay_label': 'Incidence financi\xc3\xa8re',
             'for_item_created_until': '',
             'org': org_id_to_uid('df-comptabilita-c-et-audit-financier'),
             'available_on': '',
             'delay': '10',
             'gives_auto_advice_on_help_message': '',
             'gives_auto_advice_on':
                "python: item.adapted().needFinanceAdviceOf('df-comptabilita-c-et-audit-financier')",
             'delay_left_alert': '3',
             'is_linked_to_previous_row': '0',
             'for_item_created_from': '2014/06/05',
             'row_id': '2014-06-05.5584062584'},
            {'delay_label': 'Incidence financi\xc3\xa8re (urgence)',
             'for_item_created_until': '',
             'org': org_id_to_uid('df-comptabilita-c-et-audit-financier'),
             'available_on': '',
             'delay': '5',
             'gives_auto_advice_on_help_message': '',
             'gives_auto_advice_on': '',
             'delay_left_alert': '3',
             'is_linked_to_previous_row': '1',
             'for_item_created_from': '2014/06/05',
             'row_id': '2014-06-05.5584062390'},
            {'delay_label': 'Incidence financi\xc3\xa8re (prolongation)',
             'for_item_created_until': '',
             'org': org_id_to_uid('df-comptabilita-c-et-audit-financier'),
             'available_on': '',
             'delay': '20',
             'gives_auto_advice_on_help_message': '',
             'gives_auto_advice_on': '',
             'delay_left_alert': '3',
             'is_linked_to_previous_row': '1',
             'for_item_created_from': '2014/06/05',
             'row_id': '2014-06-05.5584074805'},
            {'delay_label': 'Incidence financi\xc3\xa8re',
             'for_item_created_until': '',
             'org': org_id_to_uid('df-contrale'),
             'available_on': '',
             'delay': '10',
             'gives_auto_advice_on_help_message': '',
             'gives_auto_advice_on': "python: item.adapted().needFinanceAdviceOf('df-contrale')",
             'delay_left_alert': '3',
             'is_linked_to_previous_row': '0',
             'for_item_created_from': '2014/06/05',
             'row_id': '2014-06-05.5584079907'},
            {'delay_label': 'Incidence financi\xc3\xa8re (urgence)',
             'for_item_created_until': '',
             'org': org_id_to_uid('df-contrale'),
             'available_on': '',
             'delay': '5',
             'gives_auto_advice_on_help_message': '',
             'gives_auto_advice_on': '',
             'delay_left_alert': '3',
             'is_linked_to_previous_row': '1',
             'for_item_created_from': '2014/06/05',
             'row_id': '2014-06-05.5584070070'},
            {'delay_label': 'Incidence financi\xc3\xa8re (prolongation)',
             'for_item_created_until': '',
             'org': org_id_to_uid('df-contrale'),
             'available_on': '',
             'delay': '20',
             'gives_auto_advice_on_help_message': '',
             'gives_auto_advice_on': '',
             'delay_left_alert': '3',
             'is_linked_to_previous_row': '1',
             'for_item_created_from': '2014/06/05',
             'row_id': '2014-06-05.5584080681'}))


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
           'imioapps.css',
           'plonemeetingskin.css',
           'imioapps_IEFixes.css',
           'meetingliege.css',
           'ploneCustom.css']
    for resource in css:
        portal_css.moveResourceToBottom(resource)
