# -*- coding: utf-8 -*-

from collective.contact.plonegroup.utils import get_organizations
from DateTime import DateTime
from imio.helpers.content import uuidToObject
from imio.pyutils.utils import replace_in_list
from plone import api
from Products.MeetingLiege.profiles.liege import import_data as ml_import_data
from Products.MeetingLiege.profiles.zbourgmestre import import_data as bg_import_data
from Products.PloneMeeting.migrations.migrate_to_4200 import Migrate_To_4200 as PMMigrate_To_4200
from Products.PloneMeeting.migrations.migrate_to_4201 import Migrate_To_4201
from Products.ZCatalog.ProgressHandler import ZLogHandler

import logging


logger = logging.getLogger('MeetingLiege')


class Migrate_To_4200(PMMigrate_To_4200):

    def _fixUsedMeetingWFs(self):
        """meetingliege_workflow/meetingitemliege_workflows do not exist anymore,
           we use meeting_workflow/meetingitem_workflow."""
        logger.info("Adapting 'meetingWorkflow/meetingItemWorkflow' for every MeetingConfigs...")
        for cfg in self.tool.objectValues('MeetingConfig'):
            if cfg.getMeetingWorkflow() in ('meetingcollegeliege_workflow',
                                            'meetingcouncilliege_workflow',
                                            'meetingbourgmestre_workflow', ):
                cfg.setMeetingWorkflow('meeting_workflow')
            if cfg.getItemWorkflow() in ('meetingitemcollegeliege_workflow',
                                         'meetingitemcouncilliege_workflow',
                                         'meetingitembourgmestre_workflow', ):
                cfg.setItemWorkflow('meetingitem_workflow')
        # delete old unused workflows
        wfs_to_delete = [wfId for wfId in self.wfTool.listWorkflows()
                         if any(x in wfId for x in (
                            'meetingcollegeliege_workflow',
                            'meetingcouncilliege_workflow',
                            'meetingbourgmestre_workflow',
                            'meetingitemcollegeliege_workflow',
                            'meetingitemcouncilliege_workflow',
                            'meetingitembourgmestre_workflow',))]
        if wfs_to_delete:
            self.wfTool.manage_delObjects(wfs_to_delete)
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
        catalog = api.portal.get_tool('portal_catalog')
        for cfg in self.tool.objectValues('MeetingConfig'):
            # this will call especially part where we duplicate WF and apply WFAdaptations
            cfg.registerPortalTypes()
            for brain in catalog(portal_type=(cfg.getItemTypeName(), cfg.getMeetingTypeName())):
                itemOrMeeting = brain.getObject()
                itemOrMeetingWFId = self.wfTool.getWorkflowsFor(itemOrMeeting)[0].getId()
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

    def _doConfigureItemWFValidationLevels(self, cfg):
        """Apply correct itemWFValidationLevels from profiles import_data."""
        stored_itemWFValidationLevels = getattr(cfg, 'itemWFValidationLevels', [])
        if not stored_itemWFValidationLevels:
            if cfg.getId() == 'meeting-config-college':
                cfg.setItemWFValidationLevels(ml_import_data.collegeMeeting.itemWFValidationLevels)
                cfg.setWorkflowAdaptations(ml_import_data.collegeMeeting.workflowAdaptations)
            elif cfg.getId() == 'meeting-config-council':
                cfg.setItemWFValidationLevels(ml_import_data.councilMeeting.itemWFValidationLevels)
                cfg.setWorkflowAdaptations(ml_import_data.councilMeeting.workflowAdaptations)
            else:
                # meeting-config-bourgmestre
                cfg.setItemWFValidationLevels(bg_import_data.bourgmestreMeeting.itemWFValidationLevels)
                cfg.setWorkflowAdaptations(bg_import_data.bourgmestreMeeting.workflowAdaptations)

    def _migrateLabelForCouncil(self):
        """Field labelForCouncil is replaced by
           otherMeetingConfigsClonableToFieldDetailedDescription in College and
           detailedDescription in Council."""
        logger.info('Migrating field "labelForCouncil" in "meeting-config-college"...')
        # enable relevant fields in MeetingConfigs
        # College we use the "otherMeetingConfigsClonableToFieldLabelForCouncil" field
        # Council is correct
        college_cfg = self.tool.get('meeting-config-college')
        used_attrs = college_cfg.getUsedItemAttributes()
        used_attrs = replace_in_list(used_attrs,
                                     "labelForCouncil",
                                     "otherMeetingConfigsClonableToFieldLabelForCouncil")
        college_cfg.setUsedItemAttributes(used_attrs)
        logger.info('Done.')

        logger.info('Migrating field "labelForCouncil" for College items...')
        pghandler = ZLogHandler(steps=1000)
        brains = self.catalog(portal_type='MeetingItemCollege')
        pghandler.init('Migrating field "labelForCouncil" for College items', len(brains))
        i = 0
        for brain in brains:
            i += 1
            pghandler.report(i)
            item = brain.getObject()
            if not item.fieldIsEmpty('labelForCouncil'):
                item.setOtherMeetingConfigsClonableToFieldLabelForCouncil(
                    item.getRawLabelForCouncil())
                item.setLabelForCouncil('')
        pghandler.finish()
        logger.info('Done.')

    def _hook_before_meeting_to_dx(self):
        """Adapt Meeting.workflow_history before migrating to DX."""
        # enable adopts_next_agenda_of in usedMeetingAttributes of College
        college_cfg = self.tool.get('meeting-config-college')
        used_attrs = college_cfg.getUsedMeetingAttributes()
        used_attrs = replace_in_list(used_attrs,
                                     "adoptsNextCouncilAgenda",
                                     "adopts_next_agenda_of")
        college_cfg.setUsedMeetingAttributes(used_attrs)
        self._adaptWFHistoryForItemsAndMeetings()

    def _mc_fixPODTemplatesInstructions(self):
        '''Make some replace in POD templates to fit changes in code...'''
        return
        # for every POD templates
        # replacements = {}
        # specific for Meeting POD Templates
        # meeting_replacements = {}
        # specific for MeetingItem POD Templates
        # item_replacements = {}

        # comment for now, nothing to do
        # self.updatePODTemplatesCode(replacements, meeting_replacements, item_replacements)

    def _migrateItemsWorkflowHistory(self):
        """Migrate items workflow_history and remap states."""
        # as state "proposed_to_finance" changed to "proposed_to_finance_waiting_advices",
        # we must update various places
        # organizations
        old_finance_value = 'meeting-config-college__state__proposed_to_finance'
        new_finance_value = 'meeting-config-college__state__proposed_to_finance_waiting_advices'
        for org in get_organizations():
            for field_name in ('item_advice_states', 'item_advice_edit_states', 'item_advice_view_states'):
                value = getattr(org, field_name) or []
                if old_finance_value in value:
                    setattr(org,
                            field_name,
                            tuple(replace_in_list(
                                value, old_finance_value, new_finance_value)))
        # MeetingConfigs
        old_finance_value = 'proposed_to_finance'
        new_finance_value = 'proposed_to_finance_waiting_advices'
        for cfg in self.tool.objectValues('MeetingConfig'):
            for field_name in ('itemAdviceStates', 'itemAdviceEditStates', 'itemAdviceViewStates'):
                value = getattr(cfg, field_name) or []
                if old_finance_value in value:
                    setattr(cfg,
                            field_name,
                            tuple(replace_in_list(
                                value, old_finance_value, new_finance_value)))

        # update item workflow_history and MeetingConfig fields using states/transitions
        self.updateWFStatesAndTransitions(
            query={'portal_type': ('MeetingItemCollege', 'MeetingItemBourgmestre')},
            review_state_mappings={
                # meeting-config-college
                'proposed_to_finance': 'proposed_to_finance_waiting_advices'},
            transition_mappings={
                # meeting-config-college
                'proposeToFinance': 'wait_advices_from_proposed_to_director',
                'askAdvicesByInternalReviewer': 'wait_advices_from_proposed_to_internal_reviewer',
                'askAdvicesByItemCreator': 'wait_advices_from_itemcreated',
                # meeting-config-bourgmestre
                'askAdvicesByDirector': 'wait_advices_from_proposed_to_director', },
            # will be done by next step in migration
            update_local_roles=False)

    def _migrateDeliberationToSignAnnexType(self):
        """Make the annex_type confidential by default."""
        logger.info('Migrating deliberation-to-sign annex_type...')
        for cfg in self.tool.objectValues('MeetingConfig'):
            pod_template_path = cfg.getMeetingItemTemplatesToStoreAsAnnex()
            if pod_template_path:
                pod_template = cfg.podtemplates.get(pod_template_path[0].split('__')[0])
                annex_type_uid = pod_template.store_as_annex
                annex_type = uuidToObject(annex_type_uid, unrestricted=True)
                annex_type.confidential = True
        logger.info('Done.')

    def _hook_custom_meeting_to_dx(self, old, new):
        """Called when meetings migrated to DX."""
        if old.adoptsNextCouncilAgenda:
            new.adopts_next_agenda_of = ['meeting-config-council']

    def run(self,
            profile_name=u'profile-Products.MeetingLiege:default',
            extra_omitted=[]):

        if self.is_in_part('a'):  # main step

            # change self.profile_name that is reinstalled at the beginning of the PM migration
            self.profile_name = profile_name

            # fix used WFs before reinstalling
            self._fixUsedMeetingWFs()

            # fix some instructions in POD templates
            self._mc_fixPODTemplatesInstructions()

            # migrate labelForCouncil
            self._migrateLabelForCouncil()

            # make the deliberation to sign annex_type, confidential by default
            self._migrateDeliberationToSignAnnexType()

        if self.is_in_part('b'):  # update_local_roles step
            # migrate items workflow_history
            self._migrateItemsWorkflowHistory()

        # call steps from Products.PloneMeeting
        # this will manage parts 'a', 'b' and 'c'
        super(Migrate_To_4200, self).run(extra_omitted=extra_omitted)

        if self.is_in_part('c'):  # update wf_mappings/recatalog step

            # execute upgrade steps in PM that were added after main upgrade to 4200
            Migrate_To_4201(self.portal).run(from_migration_to_4200=True)

            # now MeetingLiege specific steps
            logger.info('Migrating to MeetingLiege 4200...')
            # add new searches (searchitemswithnofinanceadvice)
            self.addNewSearches()
            # enable 'async_actions' column in dashboards
            self.updateItemColumns(to_remove=['actions'], to_add=['async_actions'])


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
