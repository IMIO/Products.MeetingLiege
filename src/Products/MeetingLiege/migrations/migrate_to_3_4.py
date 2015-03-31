# ------------------------------------------------------------------------------
import logging
logger = logging.getLogger('MeetingLiege')

from zope.i18n import translate
from Products.PloneMeeting.migrations import Migrator


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
                            event['comments'] = event['comments'].replace(toFind, '{0}</p>'.format(adviceTypes[adviceType].encode('utf-8')))
                            advice.workflow_history = advice.workflow_history
            advice.workflow_history = wfh
        logger.info('Done.')

    def run(self):
        logger.info('Migrating to MeetingLiege 3.4...')
        self._updateHistorizedFinanceAdviceInWFHistory()
        self.finish()


# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function will:

       1) Update historized finance advice advice_type in the advice workflow_history;
    '''
    Migrate_To_3_4(context).run()
# ------------------------------------------------------------------------------
