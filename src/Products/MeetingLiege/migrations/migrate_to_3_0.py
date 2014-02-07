# ------------------------------------------------------------------------------
import logging
logger = logging.getLogger('MeetingLalouviere')
from Products.PloneMeeting.migrations import Migrator
from Products.PloneMeeting.config import TOPIC_SEARCH_SCRIPT, POWEROBSERVERS_GROUP_SUFFIX


# The migration class ----------------------------------------------------------
class Migrate_To_3_0(Migrator):

    def _createUsersFromLDAP(self):
        # get every existing users, look at the Creator index
        CreatorIndex = self.portal.restrictedTraverse('portal_catalog/Indexes/Creator')
        source_users = self.portal.acl_users.source_users
        for userId in CreatorIndex._index:
            if source_users.getUserById(userId):
                continue
            # create the user
            source_users.addUser(userId, userId, 'unknown_password')
        # update mutable_properties
        mutable_properties = self.portal.acl_users.mutable_properties

        # update isGroup key
        for principal in mutable_properties._storage.items():
            if not 'isGroup' in principal[1]:
                principal[1]['isGroup'] = True

    def _adaptItemsToValidateTopic(self):
        """
          Old versions of the searchitemstovalidate topic did not use a search script, correct this!
        """
        logger.info("Adding a searchScript to the 'searchitemstovalidate' topic")
        for cfg in self.portal.portal_plonemeeting.objectValues('MeetingConfig'):
            topic = getattr(cfg.topics, 'searchitemstovalidate', None)
            if topic:
                if not topic.hasProperty(TOPIC_SEARCH_SCRIPT):
                    topic.manage_addProperty(TOPIC_SEARCH_SCRIPT, 'searchItemsToValidate', 'string')
                else:
                    topic.manage_changeProperties(topic_search_script='searchItemsToValidate')

    def _removeGlobalPowerObservers(self):
        """
          Before, PowerObservers where global to every meetingConfig, now
          that PowerObservers are locally defined for each meetingConfig,
          remove the useless 'MeetingPowerObserver' role, remove the useless
          'meetingpowerobservers' group and put users of these groups in relevant
          '_powerobservers' suffixed groups for active meetingConfigs.
        """
        logger.info("Migrating from global PowerObservers to local PowerObservers")
        # remove the 'meetingpowerobservers' group
        # put every users of this group to '_powerobservers' suffixed groups of active meetingConfigs
        # generate a list of groups to transfer users to
        localPowerObserversGroupIds = []
        for cfg in self.portal.portal_plonemeeting.getActiveConfigs():
            localPowerObserversGroupIds.append("%s_%s" % (cfg.getId(), POWEROBSERVERS_GROUP_SUFFIX))

        powerObserverGroup = self.portal.portal_groups.getGroupById('meetingpowerobservers')
        existingPowerObserverUserIds = powerObserverGroup and powerObserverGroup.getGroupMemberIds() or ()
        for localPowerObserversGroupId in localPowerObserversGroupIds:
            for existingPowerObserverUserId in existingPowerObserverUserIds:
                self.portal.portal_groups.addPrincipalToGroup(existingPowerObserverUserId, localPowerObserversGroupId)

        # remove the 'meetingpowerobservers' group
        # first remove every role given to the 'meetingpowerobservers' group
        meetingpowerobservers = self.portal.portal_groups.getGroupById('meetingpowerobservers')
        if meetingpowerobservers:
            for role in self.portal.acl_users.portal_role_manager.getRolesForPrincipal(meetingpowerobservers):
                self.portal.acl_users.portal_role_manager.removeRoleFromPrincipal(role, 'meetingpowerobservers')
            # remove the group
            self.portal.portal_groups.removeGroup('meetingpowerobservers')
        # remove the 'MeetingPowerObserver' role
        data = list(self.portal.__ac_roles__)
        if 'MeetingPowerObserver' in data:
            # first on the portal
            data.remove('MeetingPowerObserver')
            self.portal.__ac_roles__ = tuple(data)
            # then in portal_role_manager
            try:
                self.portal.acl_users.portal_role_manager.removeRole('MeetingPowerObserver')
            except KeyError:
                pass

    def run(self):
        logger.info('Migrating to MeetingLalouviere 3.0...')
        self._adaptItemsToValidateTopic()
        self._removeGlobalPowerObservers()

        # reinstall regarding changes in workflows
        self.reinstall(profiles=[u'profile-Products.MeetingLalouviere:default', ])
        self.finish()


# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function:

       1) Adapt itemsToValidate topics;
       2) Remove global PowerObserver role;
       3) Reinstall MeetingLalouviere
    '''
    Migrate_To_3_0(context).run()
# ------------------------------------------------------------------------------
