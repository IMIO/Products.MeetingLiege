# -*- coding: utf-8 -*-
#
# File: testFaceted.py
#
# Copyright (c) 2007-2015 by imio.be
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

from zope.component import queryUtility
from zope.schema.interfaces import IVocabularyFactory
from plone.memoize.instance import Memojito

from imio.helpers.cache import cleanVocabularyCacheFor
from Products.MeetingLiege.tests.MeetingLiegeTestCase import MeetingLiegeTestCase
from Products.MeetingCommunes.tests.testFaceted import testFaceted as mctf

memPropName = Memojito.propname


class testFaceted(MeetingLiegeTestCase, mctf):
    '''Tests the faceted navigation.'''

    def _setupGroupsOfMatter(self):
        """ """
        self.changeUser('siteadmin')
        pmFolder = self.getMeetingFolder()
        cfg = self.meetingConfig
        cfg.useGroupsAsCategories = False
        cfg.categories.deployment.setGroupsOfMatter(('vendors', 'developers', ))
        cfg.categories.development.setGroupsOfMatter(('vendors', ))
        cfg.categories.maintenance.setGroupsOfMatter(('developers', ))
        return cfg, pmFolder, queryUtility(IVocabularyFactory,
                                           "Products.MeetingLiege.vocabularies.groupsofmattervocabulary")

    def test_subproduct_GroupsOfMatterVocabularyCache(self):
        '''Test the "Products.MeetingLiege.vocabularies.groupsofmattervocabulary"
           vocabulary, especially because it is cached.'''
        # memoizing instance is kept across tests...
        cleanVocabularyCacheFor("Products.MeetingLiege.vocabularies.groupsofmattervocabulary")
        cfg, pmFolder, vocab = self._setupGroupsOfMatter()
        self.assertFalse(getattr(vocab, memPropName, {}))
        # once get, it is cached
        vocab(pmFolder)
        self.assertTrue(getattr(vocab, memPropName))

        # if we add/remove/edit a category, then the cache is cleaned
        # add a category
        newCatId = cfg.categories.invokeFactory('MeetingCategory', id='new-category', title='New category')
        newCat = getattr(cfg.categories, newCatId)
        newCat.at_post_create_script()
        # cache was cleaned
        self.assertFalse(getattr(vocab, memPropName, {}))
        vocab(pmFolder)
        self.assertTrue(getattr(vocab, memPropName))

        # edit a category
        newCat.at_post_edit_script()
        # cache was cleaned
        self.assertFalse(getattr(vocab, memPropName, {}))
        vocab(pmFolder)
        self.assertTrue(getattr(vocab, memPropName))

        # remove a category
        self.portal.restrictedTraverse('@@delete_givenuid')(newCat.UID())
        # cache was cleaned
        self.assertFalse(getattr(vocab, memPropName, {}))

    def test_subproduct_GroupsOfMatterVocabulary(self):
        """Returns groupsOfMatter defined on categories."""
        cfg, pmFolder, vocab = self._setupGroupsOfMatter()
        self.assertEquals([term.token for term in vocab(pmFolder)._terms],
                          ['developers', 'vendors'])

        # some groupIds are ignored, like "ssc"
        self.tool.invokeFactory('MeetingGroup', id='scc', title='SCC')
        cfg.categories.maintenance.setGroupsOfMatter(('developers', 'scc'))
        cfg.categories.maintenance.at_post_edit_script()
        self.assertFalse('scc' in [term.token for term in vocab(pmFolder)._terms])

        # clean cache and test when cfg.useGroupsAsCategories is True, vocab will be empty
        cfg.setUseGroupsAsCategories(True)
        cleanVocabularyCacheFor("Products.MeetingLiege.vocabularies.groupsofmattervocabulary")
        self.assertEquals([term.token for term in vocab(pmFolder)._terms],
                          [])


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testFaceted, prefix='test_subproduct_'))
    return suite
