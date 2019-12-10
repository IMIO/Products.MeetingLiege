# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------

from collective.contact.plonegroup.utils import get_own_organization
from copy import deepcopy
from plone import api
from Products.MeetingLiege.profiles.liege.import_data import collegeMeeting
from Products.MeetingLiege.profiles.zbourgmestre.import_data import bourgmestreMeeting
from Products.PloneMeeting.migrations.migrate_to_4_1 import Migrate_To_4_1 as PMMigrate_To_4_1
from Products.PloneMeeting.utils import org_id_to_uid
import logging


logger = logging.getLogger('MeetingLiege')


# The migration class ----------------------------------------------------------
class Migrate_To_4_1(PMMigrate_To_4_1):

    def _hook_after_mgroups_to_orgs(self):
        """Migrate attributes that were using MeetingGroups :
           - MeetingConfig.archivingRefs.restrict_to_groups;
           - MeetingCategory.groupsOfMatter;
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
            # MeetingCategory.groupsOfMatter
            for category in cfg.getCategories(onlySelectable=False, caching=False):
                groupsOfMatter = category.getGroupsOfMatter()
                migratedGroupsOfMatter = [org_id_to_uid(mGroupId) for mGroupId in groupsOfMatter]
                category.setGroupsOfMatter(migratedGroupsOfMatter)
        own_org = get_own_organization()
        for brain in self.portal.portal_catalog(meta_type='MeetingItem'):
            item = brain.getObject()
            financeAdvice = item.getFinanceAdvice()
            if financeAdvice != '_none_':
                finance_org_uid = own_org.get(financeAdvice).UID()
                item.setFinanceAdvice(finance_org_uid)

        # remove users from Plone groups ending with _observers
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
                if content.find('<p>&nbsp;</p>') != -1:
                    content = content.replace('</p>\n\n<p>&nbsp;</p>', '</p>\n\n')
                    content = content.replace('</p>\n<p>&nbsp;</p>', '</p>\n')
                    field.set(item, content)
            i = i + 1
        logger.info('Done.')

    def run(self):
        # change self.profile_name everything is right before launching steps
        self.profile_name = u'profile-Products.MeetingLiege:default'
        self.removeUnusedColumns(columns=['getAdoptsNextCouncilAgenda'])
        # call steps from Products.PloneMeeting
        PMMigrate_To_4_1.run(self)
        # now MeetingLiege specific steps
        logger.info('Migrating to MeetingLiege 4.1...')
        self._removeEmptyParagraphs()
        self.finish()


# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function will:
       1) Runs the PloneMeeting migration to 4.1;
       2) Overrides the _hook_after_mgroups_to_orgs;
       3) Removes empty paragraphs from RichText fields of every items.
    '''
    Migrate_To_4_1(context).run()
# ------------------------------------------------------------------------------
