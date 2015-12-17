# ------------------------------------------------------------------------------
import lxml.html
import logging
logger = logging.getLogger('MeetingLiege')

from zope.i18n import translate
from plone.app.textfield.value import RichTextValue
from Products.CMFPlone.utils import safe_unicode
from collective.documentgenerator.content.pod_template import IPODTemplate
from Products.PloneMeeting.migrations import Migrator
from Products.MeetingLiege.config import FINANCE_GROUP_IDS


# The migration class ----------------------------------------------------------
class Migrate_To_3_4(Migrator):

    def _updateHistorizedFinanceAdviceInWFHistory(self):
        '''When finance advice was historized in the workflow_history,
           the type of the advice was not translated, do it now...'''
        logger.info('Updating historized finance advice on each meetingadvice...')
        brains = self.portal.portal_catalog(portal_type='meetingadvice')
        adviceTypes = {'positive_finance': translate('positive_finance',
                                                     domain='PloneMeeting',
                                                     context=self.portal.REQUEST),
                       'negative_finance': translate('negative_finance',
                                                     domain='PloneMeeting',
                                                     context=self.portal.REQUEST),
                       'not_required_finance': translate('not_required_finance',
                                                         domain='PloneMeeting',
                                                         context=self.portal.REQUEST)
                       }
        for brain in brains:
            advice = brain.getObject()
            wfh = advice.workflow_history.copy()
            for event in wfh['meetingadviceliege_workflow']:
                if event['action'] == 'historize_signed_advice_content':
                    for adviceType in adviceTypes.keys():
                        toFind = '{0}</p>'.format(adviceType)
                        if event['comments'].find(toFind):
                            event['comments'] = \
                                event['comments'].replace(
                                    toFind,
                                    '{0}</p>'.format(
                                        adviceTypes[adviceType].encode('utf-8')))
                            advice.workflow_history = advice.workflow_history
            advice.workflow_history = wfh
        logger.info('Done.')

    def _moveHistorizedFinanceAdviceToVersions(self):
        '''Previously, finance advice were historized in workflow_history as a comment to the
           signAdvice transition, now we need real versions (versioning).'''
        logger.info('Moving historized finance advice to real versions...')
        brains = self.portal.portal_catalog(portal_type='meetingadvice')
        adviceTypes = {'advice_standard_positive_finance.png': 'positive_finance',
                       'advice_standard_negative_finance.png': 'negative_finance',
                       'advice_standard_not_required_finance.png': 'not_required_finance'
                       }
        pr = self.portal.portal_repository
        for brain in brains:
            advice = brain.getObject()
            if not advice.advice_group in FINANCE_GROUP_IDS:
                continue
            newEvents = []
            for event in advice.workflow_history['meetingadviceliege_workflow']:
                if event['action'] == 'historize_signed_advice_content':
                    # turn saved infos into a lxml html tree so it is easy to handle
                    infos = lxml.html.fromstring(safe_unicode(event['comments']))
                    advice_type = adviceTypes[infos.getchildren()[0].find('img').attrib['src']]
                    advice_comment = infos.getchildren()[2].text_content().strip()
                    advice_observations = infos.getchildren()[4].text_content().strip()
                    # now create a version with these infos
                    # save current advice infos, set these infos for current advice,
                    # make a version and set back original infos for advice
                    old_advice_type = advice.advice_type
                    old_advice_comment = advice.advice_comment and advice.advice_comment.output
                    old_advice_observations = advice.advice_observations and advice.advice_observations.output
                    advice.advice_type = advice_type
                    advice.advice_comment = RichTextValue(advice_comment)
                    advice.advice_observations = RichTextValue(advice_observations)
                    pr.save(obj=advice, comment='financial_advice_signed_historized_comments')
                    # get freshly versioned element and adapt some metadata
                    lastVersion = pr.getHistoryMetadata(advice).nextVersionId - 1
                    retrieved = pr.getHistoryMetadata(advice).retrieve(lastVersion)
                    retrieved['metadata']['sys_metadata']['timestamp'] = float(event['time'])
                    retrieved['metadata']['sys_metadata']['review_state'] = 'advice_given'
                    # set back old_data
                    advice.advice_type = old_advice_type
                    advice.advice_comment = RichTextValue(old_advice_comment)
                    advice.advice_observations = RichTextValue(old_advice_observations)
                else:
                    newEvents.append(event)
            advice.workflow_history['meetingadviceliege_workflow'] = newEvents
        logger.info('Done.')

    def _cleanMeetingConfigs(self):
        """Clean attribute 'cdldProposingGroup' that was removed from schema."""
        logger.info('Cleaning MeetingConfigs...')
        for cfg in self.tool.objectValues('MeetingConfig'):
            if hasattr(cfg, 'cdldProposingGroup'):
                delattr(cfg, 'cdldProposingGroup')
        logger.info('Done.')

    def _migrateItemPositiveDecidedStates(self):
        """Before, the states in which an item was auto sent to
           selected other meetingConfig was defined in a method
           'itemPositiveDecidedStates' now it is stored in MeetingConfig.itemAutoSentToOtherMCStates."""
        logger.info('Defining values for MeetingConfig.itemAutoSentToOtherMCStates...')
        for cfg in self.tool.objectValues('MeetingConfig'):
            cfg.setItemAutoSentToOtherMCStates(('accepted', 'accepted_but_modified', 'accepted_and_returned'))
        logger.info('Done.')

    def _updateCouncilItemFinanceAdviceAttribute(self):
        """When a College item was sent to Council,
           the 'financeAdvice' attribute was not copied, now it is
           the case so update existing Council items regarding value
           defined on the 'predecessor', aka the College item."""
        logger.info('Updating every Council items \'financeAdvice\' attribute...')
        brains = self.portal.portal_catalog(portal_type='MeetingItemCouncil')
        for brain in brains:
            councilItem = brain.getObject()
            if councilItem.getFinanceAdvice() == '_none_':
                collegeItem = councilItem.getPredecessor()
                if collegeItem and \
                   collegeItem.portal_type == 'MeetingItemCollege' and \
                   collegeItem.getFinanceAdvice() != '_none_':
                    councilItem.setFinanceAdvice(collegeItem.getFinanceAdvice())
        logger.info('Done.')

    def _initPodTemplatesMailingListsField(self):
        """PodTemplates have now a mailing_lists field, initialize it."""
        logger.info('Updating every PodTemplates \'mailing_lists\' attribute...')
        brains = self.portal.portal_catalog(object_provides={'query': IPODTemplate.__identifier__},)
        for brain in brains:
            template = brain.getObject()
            if hasattr(template, 'mailing_lists'):
                # already migrated
                logger.info('Done.')
                return
            template.mailing_lists = ''
        logger.info('Done.')

    def run(self):
        logger.info('Migrating to MeetingLiege 3.4...')
        #self._updateHistorizedFinanceAdviceInWFHistory()
        #self._moveHistorizedFinanceAdviceToVersions()
        self._cleanMeetingConfigs()
        #self._migrateItemPositiveDecidedStates()
        self._updateCouncilItemFinanceAdviceAttribute()
        self._initPodTemplatesMailingListsField()
        self.finish()


# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function will:
       1) Update historized finance advice advice_type in the advice workflow_history;
       2) Move historized finance advices to versions;
       3) clean meetingConfigs regarding CDLD;
       4) Migrate 'itemPositiveDecidedStates' to MeetingConfig.itemAutoSentToOtherMCStates;
       5) Initialize new field 'mailing_lists' for Pod Templates.
    '''
    Migrate_To_3_4(context).run()
# ------------------------------------------------------------------------------
