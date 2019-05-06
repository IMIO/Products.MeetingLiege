# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------

from collective.contact.plonegroup.utils import get_own_organization
from copy import deepcopy
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
           - MeetingItem.financeAdvice."""
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
            for category in cfg.getCategories(onlySelectable=True, caching=False):
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

    def run(self):
        # change self.profile_name everything is right before launching steps
        self.profile_name = u'profile-Products.MeetingLiege:default'
        # call steps from Products.PloneMeeting
        PMMigrate_To_4_1.run(self)
        # now MeetingLiege specific steps
        logger.info('Migrating to MeetingLiege 4.1...')
        self.finish()


# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function will:
       1) Runs the PloneMeeting migration to 4.1.
    '''
    Migrate_To_4_1(context).run()
# ------------------------------------------------------------------------------
