# -*- coding: utf-8 -*-

from collective.contact.plonegroup.utils import get_own_organization
from copy import deepcopy
from eea.facetednavigation.interfaces import ICriteria
from plone import api
from Products.MeetingLiege.profiles.liege.import_data import collegeMeeting
from Products.MeetingLiege.profiles.zbourgmestre.import_data import bourgmestreMeeting
from Products.PloneMeeting.migrations.migrate_to_4_1 import Migrate_To_4_1 as PMMigrate_To_4_1
from Products.PloneMeeting.migrations.migrate_to_4100 import Migrate_To_4100
from Products.PloneMeeting.migrations.migrate_to_4101 import Migrate_To_4101
from Products.PloneMeeting.migrations.migrate_to_4102 import Migrate_To_4102
from Products.PloneMeeting.migrations.migrate_to_4103 import Migrate_To_4103
from Products.PloneMeeting.migrations.migrate_to_4104 import Migrate_To_4104
from Products.PloneMeeting.utils import org_id_to_uid

import logging


logger = logging.getLogger('MeetingLiege')


# The migration class ----------------------------------------------------------
class Migrate_To_4_1(PMMigrate_To_4_1):

    def _hook_after_mgroups_to_orgs(self):
        """Migrate attributes that were using MeetingGroups :
           - MeetingConfig.archivingRefs.restrict_to_groups;
           - MeetingCategory.groupsInCharge;
           - MeetingItem.financeAdvice.
           Remove every users from _observers Plone groups.
           Then manage copyGroups and powerObservers at the end."""

        logger.info("Adapting organizations...")
        own_org = get_own_organization()
        own_org_ids = own_org.objectIds()
        for cfg in self.tool.objectValues('MeetingConfig'):
            # MeetingConfig.archivingRefs
            archivingRefs = deepcopy(cfg.getArchivingRefs())
            migratedArchivingRefs = []
            for archivingRef in archivingRefs:
                migratedArchivingRef = archivingRef.copy()
                migratedArchivingRef['restrict_to_groups'] = [
                    org_id_to_uid(mGroupId)
                    for mGroupId in migratedArchivingRef['restrict_to_groups']
                    if mGroupId in own_org_ids]
                migratedArchivingRefs.append(migratedArchivingRef)
            cfg.setArchivingRefs(migratedArchivingRefs)
            # MeetingCategory.groupsInCharge
            for category in cfg.getCategories(onlySelectable=False, caching=False):
                groupsInCharge = category.getGroupsInCharge()
                migratedGroupsInCharge = [org_id_to_uid(mGroupId) for mGroupId in groupsInCharge]
                category.setGroupsInCharge(migratedGroupsInCharge)
        own_org = get_own_organization()
        for brain in self.portal.portal_catalog(meta_type='MeetingItem'):
            item = brain.getObject()
            financeAdvice = item.getFinanceAdvice()
            if financeAdvice != '_none_':
                finance_org_uid = own_org.get(financeAdvice).UID()
                item.setFinanceAdvice(finance_org_uid)

        # remove users from Plone groups ending with _observers
        logger.info('Removing every users from observers groups...')
        pGroups = api.group.get_groups()
        for pGroup in pGroups:
            if pGroup.getId().endswith('_observers'):
                for member_id in pGroup.getMemberIds():
                    api.group.remove_user(group=pGroup, username=member_id)

        # migrate copyGroups :
        # - adapt configuration, use _copygroup instead _observers
        # - adapt copyGroups on every items (including item templates)
        logger.info("Adapting copyGroups...")
        for cfg in self.tool.objectValues('MeetingConfig'):
            selectableCopyGroups = cfg.getSelectableCopyGroups()
            patched_selectableCopyGroups = [
                copyGroup.replace('_observers', '_incopy')
                for copyGroup in selectableCopyGroups]
            cfg.setSelectableCopyGroups(patched_selectableCopyGroups)
        for brain in self.portal.portal_catalog(meta_type='MeetingItem'):
            item = brain.getObject()
            copyGroups = item.getCopyGroups()
            patched_copyGroups = [copyGroup.replace('_observers', '_incopy')
                                  for copyGroup in copyGroups]
            item.setCopyGroups(patched_copyGroups)

        # configure powerobsevers
        logger.info("Adapting powerObservers...")
        for cfg in self.tool.objectValues('MeetingConfig'):
            power_observers = deepcopy(cfg.getPowerObservers())
            if len(power_observers) == 2:
                if cfg.getId() in ['meeting-config-college', 'meeting-config-council']:
                    cfg.setPowerObservers(deepcopy(collegeMeeting.powerObservers))
                elif cfg.getId() in ['meeting-config-bourgmestre']:
                    cfg.setPowerObservers(deepcopy(bourgmestreMeeting.powerObservers))
                cfg._createOrUpdateAllPloneGroups(force_update_access=True)

    def _removeEmptyParagraphs(self):
        """Remove every <p>&nbsp;</p> from RichText fields of items."""
        logger.info('Removing empty paragraphs from every items RichText fields...')
        brains = self.portal.portal_catalog(meta_type='MeetingItem')
        i = 1
        total = len(brains)
        for brain in brains:
            logger.info('Removing empty paragraphs of element {0}/{1} ({2})...'.format(
                i,
                total,
                brain.getPath()))
            item = brain.getObject()
            # check every RichText fields
            for field in item.Schema().filterFields(default_content_type='text/html'):
                content = field.getRaw(item)
                # only remove if the previous element ends with </p>, so a paragraph
                # so we keep spaces added after a <table>, <ul>, ...
                if content.find('>&nbsp;</p>') != -1:
                    for prefix in ('</p>', ):
                        for pre_prefix in ('', '\n', '\n\n', '\r\n', '\r\n\r\n', '\n\r\n\r\n', '\r\n\r\n\r\n'):
                            for suffix in (
                                    '<p>',
                                    '<p style="margin-right:0cm">',
                                    '<p style="margin-right:0px">',
                                    '<p style="margin-left:0cm">',
                                    '<p style="margin-left:0px">',
                                    '<p style="text-align:justify">',
                                    '<p style="text-align:start">',
                                    '<p style="margin-left:0cm; margin-right:0cm">',
                                    '<p style="margin-left:0px; margin-right:0px">',
                                    '<p style="margin-left:0cm; margin-right:0cm; text-align:justify">',
                                    '<p style="margin-left:0cm; margin-right:0cm; text-align:start">',
                                    '<p style="margin-left:0px; margin-right:0px; text-align:justify">',
                                    '<p style="margin-left:0px; margin-right:0px; text-align:start">'):
                                to_replace = prefix + pre_prefix + suffix + "&nbsp;</p>"
                                content = content.replace(to_replace, prefix + '\n')
                    field.set(item, content)
            i = i + 1
        logger.info('Done.')

    def _removeGroupsOfMatter(self):
        """Remove MeetingCategory.groupsOfMatter field and related."""
        logger.info('Removing MeetingCategory.groupsOfMatter...')
        brains = self.portal.portal_catalog(meta_type='MeetingCategory')
        for brain in brains:
            cat = brain.getObject()
            if hasattr(cat, 'groupsOfMatter'):
                cat.setGroupsInCharge(cat.groupsOfMatter)
                delattr(cat, 'groupsOfMatter')
            else:
                self._already_migrated()
                return
        # remove portal_catalog index 'groupsOfMatter'
        self.removeUnusedIndexes(indexes=['groupsOfMatter'])

        # remove faceted filter
        for cfg in self.tool.objectValues('MeetingConfig'):
            # enable includeGroupsInChargeDefinedOnCategory so indexed groupsInCharge is correct
            cfg.setIncludeGroupsInChargeDefinedOnCategory(True)
            obj = cfg.searches.searches_items
            # update vocabulary for relevant filters
            criteria = ICriteria(obj)
            if criteria.get('c50'):
                criteria.delete('c50')
            # unselect 'c50' from dashboard filters and select 'c23'
            dashboardItemsListingsFilters = list(cfg.getDashboardItemsListingsFilters())
            if 'c50' in dashboardItemsListingsFilters:
                dashboardItemsListingsFilters.remove('c50')
                dashboardItemsListingsFilters.append('c23')
                cfg.setDashboardItemsListingsFilters(dashboardItemsListingsFilters)
            dashboardMeetingAvailableItemsFilters = list(cfg.getDashboardMeetingAvailableItemsFilters())
            if 'c50' in dashboardMeetingAvailableItemsFilters:
                dashboardMeetingAvailableItemsFilters.remove('c50')
                dashboardMeetingAvailableItemsFilters.append('c23')
                cfg.setDashboardMeetingAvailableItemsFilters(dashboardMeetingAvailableItemsFilters)
            dashboardMeetingLinkedItemsFilters = list(cfg.getDashboardMeetingLinkedItemsFilters())
            if 'c50' in dashboardMeetingLinkedItemsFilters:
                dashboardMeetingLinkedItemsFilters.remove('c50')
                dashboardMeetingLinkedItemsFilters.append('c23')
                cfg.setDashboardMeetingLinkedItemsFilters(dashboardMeetingLinkedItemsFilters)
        logger.info('Done.')

    def run(self):
        # change self.profile_name everything is right before launching steps
        self.profile_name = u'profile-Products.MeetingLiege:default'
        self._removeGroupsOfMatter()
        self.removeUnusedColumns(columns=['getAdoptsNextCouncilAgenda'])
        # enable 'publishable_activated' in Council so when the upgradestep
        # of collective.iconifiedcategory to 2101 update annexes, it is correct
        self.tool.get('meeting-config-council').annexes_types.item_annexes.publishable_activated = True

        # call steps from Products.PloneMeeting
        PMMigrate_To_4_1.run(self)

        # execute upgrade steps in PM that were added after main upgrade to 4.1
        Migrate_To_4100(self.portal).run()
        Migrate_To_4101(self.portal).run(from_migration_to_41=True)
        Migrate_To_4102(self.portal).run()
        Migrate_To_4103(self.portal).run()
        Migrate_To_4104(self.portal).run(from_migration_to_41=True)

        # now MeetingLiege specific steps
        logger.info('Migrating to MeetingLiege 4.1...')
        self._removeEmptyParagraphs()
        # enableScanDocs
        self.tool.setEnableScanDocs(True)
        self.finish()


# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function will:
       1) Remove useless indexes and MeetingCategory.groupsOfMatter functionnality;
       2) Runs the PloneMeeting migration to 4.1;
       3) Overrides the _hook_after_mgroups_to_orgs;
       4) Removes empty paragraphs from RichText fields of every items.
    '''
    Migrate_To_4_1(context).run()
# ------------------------------------------------------------------------------
