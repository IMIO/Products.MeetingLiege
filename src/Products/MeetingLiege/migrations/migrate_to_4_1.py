# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
import logging
from Products.PloneMeeting.migrations.migrate_to_4_1 import Migrate_To_4_1 as PMMigrate_To_4_1

logger = logging.getLogger('MeetingLiege')


# The migration class ----------------------------------------------------------
class Migrate_To_4_1(PMMigrate_To_4_1):

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
