# -*- coding: utf-8 -*-

from DateTime import DateTime
from plone import api
from Products.PloneMeeting.migrations.migrate_to_4200 import Migrate_To_4200 as PMMigrate_To_4200
from Products.PloneMeeting.migrations.migrate_to_4201 import Migrate_To_4201
from imio.pyutils.utils import replace_in_list

import logging


logger = logging.getLogger('MeetingLiege')


class Migrate_To_4200(PMMigrate_To_4200):

    def _fixUsedMeetingWFs(self):
        """meetingcommunes_workflow/meetingitemcommunes_workflows do not exist anymore,
           we use meeting_workflow/meetingitem_workflow."""
        logger.info("Adapting 'meetingWorkflow/meetingItemWorkflow' for every MeetingConfigs...")
        for cfg in self.tool.objectValues('MeetingConfig'):
            if cfg.getMeetingWorkflow() in ('meetingcollegeliege_workflow',
                                            'meetingcouncil_workflow',
                                            'meetingbourgmestre_workflow', ):
                cfg.setMeetingWorkflow('meeting_workflow')
            if cfg.getMeetingWorkflow() in ('meetingitemcollegeliege_workflow',
                                            'meetingitemcouncil_workflow',
                                            'meetingitembourgmestre_workflow', ):
                cfg.setItemWorkflow('meetingitem_workflow')
        # delete old unused workflows
        wfTool = api.portal.get_tool('portal_workflow')
        wfs_to_delete = [wfId for wfId in wfTool.listWorkflows()
                         if any(x in wfId for x in (
                            'meetingcollegeliege_workflow',
                            'meetingcouncil_workflow',
                            'meetingbourgmestre_workflow',
                            'meetingitemcollegeliege_workflow',
                            'meetingitemcouncil_workflow',
                            'meetingitembourgmestre_workflow',))]
        if wfs_to_delete:
            wfTool.manage_delObjects(wfs_to_delete)
        logger.info('Done.')

    def _get_wh_key(self, itemOrMeeting):
        """Get workflow_history key to use, in case there are several keys, we take the one
           having the last event."""
        keys = itemOrMeeting.workflow_history.keys()
        if len(keys) == 1:
            return keys[0]
        else:
            lastEventDate = DateTime('1950/01/01')
            keyToUse = None
            for key in keys:
                if itemOrMeeting.workflow_history[key][-1]['time'] > lastEventDate:
                    lastEventDate = itemOrMeeting.workflow_history[key][-1]['time']
                    keyToUse = key
            return keyToUse

    def _adaptWFHistoryForItemsAndMeetings(self):
        """We use PM default WFs, no more meeting(item)liege_workflow..."""
        logger.info('Updating WF history items and meetings to use new WF id...')
        wfTool = api.portal.get_tool('portal_workflow')
        catalog = api.portal.get_tool('portal_catalog')
        for cfg in self.tool.objectValues('MeetingConfig'):
            # this will call especially part where we duplicate WF and apply WFAdaptations
            cfg.registerPortalTypes()
            for brain in catalog(portal_type=(cfg.getItemTypeName(), cfg.getMeetingTypeName())):
                itemOrMeeting = brain.getObject()
                itemOrMeetingWFId = wfTool.getWorkflowsFor(itemOrMeeting)[0].getId()
                if itemOrMeetingWFId not in itemOrMeeting.workflow_history:
                    wf_history_key = self._get_wh_key(itemOrMeeting)
                    itemOrMeeting.workflow_history[itemOrMeetingWFId] = \
                        tuple(itemOrMeeting.workflow_history[wf_history_key])
                    del itemOrMeeting.workflow_history[wf_history_key]
                    # do this so change is persisted
                    itemOrMeeting.workflow_history = itemOrMeeting.workflow_history
                else:
                    # already migrated
                    break
        logger.info('Done.')

    def _migrateLabelForCouncil(self):
        """Field labelForCouncil is replaced by
           otherMeetingConfigsClonableToFieldDetailedDescription in College and
           detailedDescription in Council."""
        logger.info('Migrating field "labelForCouncil"...')
        # enable relevant fields in MeetingConfigs
        # College we use the "otherMeetingConfigsClonableToFieldLabelForCouncil" field
        # Council is correct
        college_cfg = self.tool.get('meeting-config-college')
        used_attrs = college_cfg.getUsedItemAttributes()
        used_attrs = replace_in_list(used_attrs,
                                     "labelForCouncil",
                                     "otherMeetingConfigsClonableToFieldLabelForCouncil")
        college_cfg.setUsedItemAttributes(used_attrs)
        for brain in self.catalog(portal_type='MeetingItemCollege'):
            item = brain.getObject()
            if not item.fieldIsEmpty('labelForCouncil'):
                item.otherMeetingConfigsClonableToFieldLabelForCouncil(item.getRawLabelForCouncil())
                item.setLabelForCouncil('')
        logger.info('Done.')

    def _hook_before_meeting_to_dx(self):
        """Adapt Meeting.workflow_history before migrating to DX."""
        self._adaptWFHistoryForItemsAndMeetings()

    def _mc_fixPODTemplatesInstructions(self):
        '''Make some replace in POD templates to fit changes in code...'''
        # for every POD templates
        replacements = {'.getLabelForCouncil(': '.getDetailedDescription(', }
        # specific for Meeting POD Templates
        meeting_replacements = {}
        # specific for MeetingItem POD Templates
        item_replacements = {}

        self.updatePODTemplatesCode(replacements, meeting_replacements, item_replacements)

    def run(self,
            profile_name=u'profile-Products.MeetingLiege:default',
            extra_omitted=[]):
        # change self.profile_name that is reinstalled at the beginning of the PM migration
        self.profile_name = profile_name

        # fix used WFs before reinstalling
        self._fixUsedMeetingWFs()

        # fix some instructions in POD templates
        self._mc_fixPODTemplatesInstructions()

        # migrate labelForCouncil
        self._migrateLabelForCouncil()

        # call steps from Products.PloneMeeting
        super(Migrate_To_4200, self).run(extra_omitted=extra_omitted)

        # execute upgrade steps in PM that were added after main upgrade to 4200
        Migrate_To_4201(self.portal).run(from_migration_to_4200=True)

        # add new searches (searchitemswithnofinanceadvice)
        self.addNewSearches()

        # now MeetingCommunes specific steps
        logger.info('Migrating to MeetingCommunes 4200...')


# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function:

       1) Change MeetingConfig workflows to use meeting_workflow/meetingitem_workflow;
       2) Call PloneMeeting migration to 4200 and 4201;
       3) In _after_reinstall hook, adapt items and meetings workflow_history
          to reflect new defined workflow done in 1);
       4) Add new searches.
    '''
    migrator = Migrate_To_4200(context)
    migrator.run()
    migrator.finish()
