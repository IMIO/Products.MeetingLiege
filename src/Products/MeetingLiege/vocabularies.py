# encoding: utf-8

from collective.contact.plonegroup.utils import get_organization
from operator import attrgetter
from plone import api
from plone.memoize.instance import memoize
from Products.CMFPlone.utils import safe_unicode
from Products.PloneMeeting.utils import org_id_to_uid
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


IGNORED_GROUP_IDS = ('scc', 'sc', 'secra-c-tariat-collage-conseil')


class GroupsOfMatterVocabulary(object):
    implements(IVocabularyFactory)

    def _ignored_group_uids(self):
        """ """
        return [org_id_to_uid(group_id) for group_id in IGNORED_GROUP_IDS]

    @memoize
    def __call__(self, context):
        """List groups that are in charge of a matter (category)."""
        tool = api.portal.get_tool('portal_plonemeeting')
        cfg = tool.getMeetingConfig(context)
        categories = cfg.getCategories(onlySelectable=False)
        res = []
        existingGroupsIdsInVocab = []
        ignored_group_uids = self._ignored_group_uids()
        if not cfg.getUseGroupsAsCategories():
            for category in categories:
                groupsOfMatter = category.getGroupsOfMatter()
                for groupOfMatter in groupsOfMatter:
                    if groupOfMatter in existingGroupsIdsInVocab or \
                       groupOfMatter in ignored_group_uids:
                        continue
                    else:
                        existingGroupsIdsInVocab.append(groupOfMatter)
                        res.append(
                            SimpleTerm(groupOfMatter,
                                       groupOfMatter,
                                       safe_unicode(get_organization(groupOfMatter).Title())))
        res = sorted(res, key=attrgetter('title'))
        return SimpleVocabulary(res)

GroupsOfMatterVocabularyFactory = GroupsOfMatterVocabulary()
