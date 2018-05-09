# encoding: utf-8

from operator import attrgetter

from zope.interface import implements
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from Products.CMFPlone.utils import safe_unicode
from plone.memoize.instance import memoize
from plone import api

IGNORED_GROUP_IDS = ('scc', 'sc', 'secra-c-tariat-collage-conseil')


class GroupsOfMatterVocabulary(object):
    implements(IVocabularyFactory)

    @memoize
    def __call__(self, context):
        """List groups that are in charge of a matter (category)."""
        tool = api.portal.get_tool('portal_plonemeeting')
        cfg = tool.getMeetingConfig(context)
        categories = cfg.getCategories(onlySelectable=False)
        res = []
        existingGroupsIdsInVocab = []
        if not cfg.getUseGroupsAsCategories():
            for category in categories:
                groupsOfMatter = category.getGroupsOfMatter()
                for groupOfMatter in groupsOfMatter:
                    if groupOfMatter in existingGroupsIdsInVocab or \
                       groupOfMatter in IGNORED_GROUP_IDS:
                        continue
                    else:
                        existingGroupsIdsInVocab.append(groupOfMatter)
                        res.append(SimpleTerm(groupOfMatter,
                                              groupOfMatter,
                                              safe_unicode(getattr(tool, groupOfMatter).Title())
                                              )
                                   )
        res = sorted(res, key=attrgetter('title'))
        return SimpleVocabulary(res)

GroupsOfMatterVocabularyFactory = GroupsOfMatterVocabulary()
