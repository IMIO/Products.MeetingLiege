# -*- coding: utf-8 -*-

from copy import deepcopy
from plone import api
from Products.MeetingLiege.profiles.liege import import_data as ml_import_data
from Products.MeetingLiege.utils import finance_group_uids
from Products.PloneMeeting.migrations import Migrator

import logging


logger = logging.getLogger('MeetingLiege')


class Migrate_To_4201(Migrator):

    def _upgradeToAdvisersConfig(self):
        """Custom advisers are now configured in UI, we need to:
           - adapt MeetingConfig.usedAdviceTypes;
           - configure ToolPloneMeeting.customAdivsers;
           - update every finances advice wokflow_history as used WF id changed."""
        logger.info('Upgrading to customAdvisers UI...')
        catalog = api.portal.get_tool('portal_catalog')
        # update every MeetingConfig.usedAdviceTypes to remove _finance values
        for cfg in self.tool.objectValues('MeetingConfig'):
            usedAdviceTypes = cfg.getUsedAdviceTypes()
            cfg.setUsedAdviceTypes([at for at in usedAdviceTypes
                                    if not at.endswith('_finance')])
        # configure ToolPloneMeeting.advisersConfig
        if not self.tool.getAdvisersConfig():
            data = deepcopy(ml_import_data.data.advisersConfig)
            data[0]['org_uids'] = finance_group_uids()
            self.tool.setAdvisersConfig(data)
            self.tool.configureAdvices()

        # update finance advice workflow_history
        old_wf_id = 'meetingadviceliege_workflow'
        new_wf_id = 'meetingadvicefinances__meetingadviceliege_workflow'
        for brain in catalog(portal_type='meetingadvicefinances'):
            advice = brain.getObject()
            if new_wf_id not in advice.workflow_history:
                advice.workflow_history[new_wf_id] = \
                    tuple(advice.workflow_history[old_wf_id])
                del advice.workflow_history[old_wf_id]
                # persist change
                advice.workflow_history._p_changed = True
            else:
                # already migrated
                break
        logger.info('Done.')

    def run(self,
            profile_name=u'profile-Products.MeetingLiege:default',
            extra_omitted=[]):

        # this will upgrade Products.PloneMeeting and dependencies
        self.upgradeAll(omit=[profile_name.replace('profile-', '')])

        self._upgradeToAdvisersConfig()


# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function:

       1) Upgrade to ToolPloneMeeting.advisersConfig.
    '''
    migrator = Migrate_To_4201(context)
    migrator.run()
    migrator.finish()
