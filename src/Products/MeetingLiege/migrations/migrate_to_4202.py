# -*- coding: utf-8 -*-

from plone import api
from Products.PloneMeeting.migrations import Migrator
from Products.ZCatalog.ProgressHandler import ZLogHandler

import logging


logger = logging.getLogger('MeetingLiege')


class Migrate_To_4202(Migrator):

    def _moveArchivingRefsToClassifiers(self):
        """Remove custom field MeetingItem.archivingRef and use
           default field MeetingItem.classifier."""
        logger.info('Moving archivingRef to classifier for every items...')
        # update MeetingConfig.archivingRefs
        for cfg in self.tool.objectValues('MeetingConfig'):
            archivingRefs = getattr(cfg, 'archivingRefs', ())
            if archivingRefs:
                # enable classifier
                self.update_used_attrs(
                    to_add=['classifier'],
                    to_remove=['archivingRef'],
                    cfg_ids=[cfg.getId()])
                # enable classifier faceted filter everywhere
                self.update_faceted_filters(to_add=['c24'], cfg_ids=[cfg.getId()])
                # create classifiers in MeetingConfig
                for archivingRef in archivingRefs:
                    api.content.create(container=cfg.classifiers,
                                       type="meetingcategory",
                                       id=archivingRef['row_id'],
                                       title=archivingRef['label'],
                                       category_id=archivingRef['code'],
                                       using_groups=archivingRef['restrict_to_groups'],
                                       enabled=True if archivingRef['active'] == '1' else False)
                self.cleanMeetingConfigs(field_names=['archivingRefs'])
                # update items
                brains = self.catalog(portal_type=cfg.getItemTypeName())
                pghandler = ZLogHandler(steps=1000)
                pghandler.init('Move archivingRef to classifier', len(brains))
                i = 0
                for brain in brains:
                    i += 1
                    pghandler.report(i)
                    item = brain.getObject()
                    item.setClassifier(item.archivingRef)
                    delattr(item, 'archivingRef')
                    item.reindexObject(idxs=['getRawClassifier'])
        logger.info('Done.')

    def run(self,
            profile_name=u'profile-Products.MeetingLiege:default',
            extra_omitted=[]):

        # this will upgrade Products.PloneMeeting and dependencies
        self.upgradeAll(omit=[profile_name.replace('profile-', '')])

        self._moveArchivingRefsToClassifiers()


# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function:

       1) Move MeetingItem.archivingRef to MeetingItem.classifier.
    '''
    migrator = Migrate_To_4202(context)
    migrator.run()
    migrator.finish()
