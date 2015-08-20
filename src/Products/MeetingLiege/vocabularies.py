# encoding: utf-8

from operator import attrgetter

from zope.interface import implements
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode

from plone.memoize.instance import memoize


class GroupsOfMatterVocabulary(object):
    implements(IVocabularyFactory)

    @memoize
    def __call__(self, context):
        """List groups that are in charge of a matter (category)."""
        tool = getToolByName(context, 'portal_plonemeeting')
        cfg = tool.getMeetingConfig(context)
        categories = cfg.getCategories(onlySelectable=False)
        res = []
        existingGroupsIdsInVocab = []
        for category in categories:
            if not category.meta_type == 'MeetingCategory':
                continue
            groupsOfMatter = category.getGroupsOfMatter()
            for groupOfMatter in groupsOfMatter:
                if groupOfMatter in existingGroupsIdsInVocab:
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
