# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
# File: adapters.py
#
# Copyright (c) 2016 by Imio.be
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
# ------------------------------------------------------------------------------
from AccessControl import ClassSecurityInfo
from appy.gen import No
from collections import OrderedDict
from collective.contact.plonegroup.config import get_registry_organizations
from collective.contact.plonegroup.utils import get_organization
from collective.contact.plonegroup.utils import get_organizations
from Globals import InitializeClass
from imio.actionspanel.utils import unrestrictedRemoveGivenObject
from imio.helpers.cache import cleanRamCacheFor
from imio.helpers.cache import cleanVocabularyCacheFor
from imio.history.adapters import BaseImioHistoryAdapter
from imio.history.interfaces import IImioHistory
from imio.history.utils import getLastAction
from imio.history.utils import getLastWFAction
from plone import api
from plone.memoize import ram
from Products.Archetypes import DisplayList
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.permissions import ReviewPortalContent
from Products.CMFCore.utils import _checkPermission
from Products.MeetingLiege.config import BOURGMESTRE_GROUP_ID
from Products.MeetingLiege.config import COUNCILITEM_DECISIONEND_SENTENCE
from Products.MeetingLiege.config import FINANCE_ADVICE_LEGAL_TEXT
from Products.MeetingLiege.config import FINANCE_ADVICE_LEGAL_TEXT_NOT_GIVEN
from Products.MeetingLiege.config import FINANCE_ADVICE_LEGAL_TEXT_PRE
from Products.MeetingLiege.config import FINANCE_GIVEABLE_ADVICE_STATES
from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.config import FINANCE_GROUP_SUFFIXES
from Products.MeetingLiege.config import GENERAL_MANAGER_GROUP_ID
from Products.MeetingLiege.config import ITEM_MAIN_INFOS_HISTORY
from Products.MeetingLiege.config import TREASURY_GROUP_ID
from Products.MeetingLiege.interfaces import IMeetingBourgmestreWorkflowActions
from Products.MeetingLiege.interfaces import IMeetingBourgmestreWorkflowConditions
from Products.MeetingLiege.interfaces import IMeetingCollegeLiegeWorkflowActions
from Products.MeetingLiege.interfaces import IMeetingCollegeLiegeWorkflowConditions
from Products.MeetingLiege.interfaces import IMeetingCouncilLiegeWorkflowActions
from Products.MeetingLiege.interfaces import IMeetingCouncilLiegeWorkflowConditions
from Products.MeetingLiege.interfaces import IMeetingItemBourgmestreWorkflowActions
from Products.MeetingLiege.interfaces import IMeetingItemBourgmestreWorkflowConditions
from Products.MeetingLiege.interfaces import IMeetingItemCollegeLiegeWorkflowActions
from Products.MeetingLiege.interfaces import IMeetingItemCollegeLiegeWorkflowConditions
from Products.MeetingLiege.interfaces import IMeetingItemCouncilLiegeWorkflowActions
from Products.MeetingLiege.interfaces import IMeetingItemCouncilLiegeWorkflowConditions
from Products.PloneMeeting.adapters import CompoundCriterionBaseAdapter
from Products.PloneMeeting.adapters import ItemPrettyLinkAdapter
from Products.PloneMeeting.adapters import MeetingPrettyLinkAdapter
from Products.PloneMeeting.config import PMMessageFactory as _
from Products.PloneMeeting.config import NOT_GIVEN_ADVICE_VALUE
from Products.PloneMeeting.config import READER_USECASES
from Products.PloneMeeting.content.advice import MeetingAdvice
from Products.PloneMeeting.interfaces import IMeetingCategoryCustom
from Products.PloneMeeting.interfaces import IMeetingConfigCustom
from Products.PloneMeeting.interfaces import IMeetingCustom
from Products.PloneMeeting.interfaces import IMeetingItemCustom
from Products.PloneMeeting.interfaces import IToolPloneMeetingCustom
from Products.PloneMeeting.Meeting import Meeting
from Products.PloneMeeting.Meeting import MeetingWorkflowActions
from Products.PloneMeeting.Meeting import MeetingWorkflowConditions
from Products.PloneMeeting.MeetingCategory import MeetingCategory
from Products.PloneMeeting.MeetingConfig import MeetingConfig
from Products.PloneMeeting.MeetingItem import MeetingItem
from Products.PloneMeeting.MeetingItem import MeetingItemWorkflowActions
from Products.PloneMeeting.MeetingItem import MeetingItemWorkflowConditions
from Products.PloneMeeting.model import adaptations
from Products.PloneMeeting.ToolPloneMeeting import ToolPloneMeeting
from Products.PloneMeeting.utils import org_id_to_uid
from zope.annotation.interfaces import IAnnotations
from zope.component import getAdapter
from zope.i18n import translate
from zope.interface import implements

import string
import unicodedata


# disable every wfAdaptations but 'return_to_proposing_group'
customWfAdaptations = ('return_to_proposing_group', )
MeetingConfig.wfAdaptations = customWfAdaptations

# use the 'itemcreated' state from college item WF to patch council item WF
RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE = {'meetingitemcollegeliege_workflow':
                                            'meetingitemcollegeliege_workflow.itemcreated',
                                            'meetingitemcouncilliege_workflow':
                                            'meetingitemcollegeliege_workflow.itemcreated',
                                            'meetingitembourgmestre_workflow':
                                            'meetingitembourgmestre_workflow.itemcreated'}
adaptations.RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE = RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE


class CustomMeeting(Meeting):
    '''Adapter that adapts a meeting implementing IMeeting to the
       interface IMeetingCustom.'''

    implements(IMeetingCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    security.declarePublic('isDecided')

    def isDecided(self):
        """
          The meeting is supposed 'decided', if at least in state :
          - 'in_council' for MeetingCouncil
          - 'decided' for MeetingCollege
        """
        meeting = self.getSelf()
        return meeting.queryState() in ('in_council', 'decided', 'closed', 'archived')

    # Implements here methods that will be used by templates
    def _insertItemInCategory(self, categoryList, item, byProposingGroup, groupPrefixes, groups):
        '''This method is used by the next one for inserting an item into the
           list of all items of a given category. if p_byProposingGroup is True,
           we must add it in a sub-list containing items of a given proposing
           group. Else, we simply append it to p_category.'''
        if not byProposingGroup:
            categoryList.append(item)
        else:
            group = item.getProposingGroup(True)
            self._insertGroupInCategory(categoryList, group, groupPrefixes, groups, item)

    security.declarePublic('getPrintableItemsByCategory')

    def getPrintableItemsByCategory(self, itemUids=[], listTypes=['normal'],
                                    ignore_review_states=[], by_proposing_group=False, group_prefixes={},
                                    privacy='*', oralQuestion='both', toDiscuss='both', categories=[],
                                    excludedCategories=[], groupIds=[], firstNumber=1, renumber=False,
                                    includeEmptyCategories=False, includeEmptyGroups=False, withCollege=False,
                                    forCommission=False, groupByCategory=True):
        '''Returns a list of (late-)items (depending on p_late) ordered by
           category. Items being in a state whose name is in
           p_ignore_review_state will not be included in the result.
           If p_by_proposing_group is True, items are grouped by proposing group
           within every category. In this case, specifying p_group_prefixes will
           allow to consider all groups whose acronym starts with a prefix from
           this param prefix as a unique group. p_group_prefixes is a dict whose
           keys are prefixes and whose values are names of the logical big
           groups. A privacy,A toDiscuss and oralQuestion can also be given, the item is a
           toDiscuss (oralQuestion) or not (or both) item.
           If p_groupIds are given, we will only consider these proposingGroups.
           If p_includeEmptyCategories is True, categories for which no
           item is defined are included nevertheless. If p_includeEmptyGroups
           is True, proposing groups for which no item is defined are included
           nevertheless.Some specific categories can be given or some categories to exclude.
           These 2 parameters are exclusive.  If renumber is True, a list of tuple
           will be return with first element the number and second element, the item.
           In this case, the firstNumber value can be used.
           If p_groupByCategory is False, results are still sorted by categories, but only
           items are returned.'''
        # The result is a list of lists, where every inner list contains:
        # - at position 0: the category object (MeetingCategory or MeetingGroup)
        # - at position 1 to n: the items in this category
        # If by_proposing_group is True, the structure is more complex.
        # oralQuestion can be 'both' or False or True
        # toDiscuss can be 'both' or 'False' or 'True'
        # privacy can be '*' or 'public' or 'secret'
        # Every inner list contains:
        # - at position 0: the category object
        # - at positions 1 to n: inner lists that contain:
        #   * at position 0: the proposing group object
        #   * at positions 1 to n: the items belonging to this group.
        def _comp(v1, v2):
            if v1[1] < v2[1]:
                return -1
            elif v1[1] > v2[1]:
                return 1
            else:
                return 0
        res = []
        items = []
        tool = api.portal.get_tool('portal_plonemeeting')
        # Retrieve the list of items
        for elt in itemUids:
            if elt == '':
                itemUids.remove(elt)

        items = self.context.getItems(uids=itemUids, listTypes=listTypes, ordered=True)

        if withCollege:
            meetingDate = self.context.getDate()
            tool = api.portal.get_tool('portal_plonemeeting')
            cfg = tool.getMeetingConfig(self.context)
            insertMethods = cfg.getInsertingMethodsOnAddItem()
            catalog = api.portal.get_tool('portal_catalog')
            brains = catalog(portal_type='MeetingCollege',
                             getDate={'query': meetingDate - 60,
                                      'range': 'min'}, sort_on='getDate',
                             sort_order='reverse')
            for brain in brains:
                obj = brain.getObject()
                isInNextCouncil = obj.getAdoptsNextCouncilAgenda()
                if obj.getDate() < meetingDate and isInNextCouncil:
                    collegeMeeting = obj
                    break
            if collegeMeeting:
                collegeMeeting = collegeMeeting.getObject()
            collegeItems = collegeMeeting.getItems(ordered=True)
            itemList = []
            for collegeItem in collegeItems:
                if 'meeting-config-council' in collegeItem.getOtherMeetingConfigsClonableTo() and not \
                        collegeItem._checkAlreadyClonedToOtherMC('meeting-config-council'):
                    itemPrivacy = collegeItem.getPrivacyForCouncil()
                    itemProposingGroup = collegeItem.getProposingGroup()
                    councilCategoryId = collegeItem.getCategory(theObject=True).\
                        getCategoryMappingsWhenCloningToOtherMC()
                    itemCategory = getattr(tool.getMeetingConfig(self.context).categories,
                                           councilCategoryId[0].split('.')[1])
                    meeting = self.context.getSelf()
                    parent = meeting.aq_inner.aq_parent
                    parent._v_tempItem = MeetingItem('')
                    parent._v_tempItem.setPrivacy(itemPrivacy)
                    parent._v_tempItem.setProposingGroup(itemProposingGroup)
                    parent._v_tempItem.setCategory(itemCategory.getId())
                    itemOrder = parent._v_tempItem.adapted().getInsertOrder(insertMethods)
                    itemList.append((collegeItem, itemOrder))
                    delattr(parent, '_v_tempItem')
            councilItems = self.context.getItems(uids=itemUids, ordered=True)
            for councilItem in councilItems:
                itemOrder = councilItem.adapted().getInsertOrder(insertMethods)
                itemList.append((councilItem, itemOrder))

            itemList.sort(cmp=_comp)
            items = [i[0] for i in itemList]
        if by_proposing_group:
            groups = get_organizations()
        else:
            groups = None
        if items:
            for item in items:
                # Check if the review_state has to be taken into account
                if item.queryState() in ignore_review_states:
                    continue
                elif not withCollege and not (privacy == '*' or item.getPrivacy() == privacy):
                    continue
                elif withCollege and not (privacy == '*' or
                                          (item.portal_type == 'MeetingItemCollege' and
                                           item.getPrivacyForCouncil() == privacy) or
                                          (item.portal_type == 'MeetingItemCouncil' and
                                           item.getPrivacy() == privacy)):
                    continue
                elif not (oralQuestion == 'both' or item.getOralQuestion() == oralQuestion):
                    continue
                elif not (toDiscuss == 'both' or item.getToDiscuss() == toDiscuss):
                    continue
                elif groupIds and not item.getProposingGroup() in groupIds:
                    continue
                elif categories and not item.getCategory() in categories:
                    continue
                elif excludedCategories and item.getCategory() in excludedCategories:
                    continue
                if not withCollege or item.portal_type == 'MeetingItemCouncil':
                    currentCat = item.getCategory(theObject=True)
                else:
                    councilCategoryId = item.getCategory(theObject=True).getCategoryMappingsWhenCloningToOtherMC()
                    currentCat = getattr(tool.getMeetingConfig(self.context).categories,
                                         councilCategoryId[0].split('.')[1])
                # Add the item to a new category, excepted if the
                # category already exists.
                catExists = False
                for catList in res:
                    if catList[0] == currentCat:
                        catExists = True
                        break
                if catExists:
                    self._insertItemInCategory(catList,
                                               item,
                                               by_proposing_group,
                                               group_prefixes, groups)
                else:
                    res.append([currentCat])
                    self._insertItemInCategory(res[-1],
                                               item,
                                               by_proposing_group,
                                               group_prefixes,
                                               groups)
        if includeEmptyCategories:
            meetingConfig = tool.getMeetingConfig(
                self.context)
            allCategories = meetingConfig.getCategories()
            usedCategories = [elem[0] for elem in res]
            for cat in allCategories:
                if cat not in usedCategories:
                    # Insert the category among used categories at the right
                    # place.
                    categoryInserted = False
                    for i in range(len(usedCategories)):
                        if allCategories.index(cat) < \
                           allCategories.index(usedCategories[i]):
                            usedCategories.insert(i, cat)
                            res.insert(i, [cat])
                            categoryInserted = True
                            break
                    if not categoryInserted:
                        usedCategories.append(cat)
                        res.append([cat])
        if by_proposing_group and includeEmptyGroups:
            # Include, in every category list, not already used groups.
            # But first, compute "macro-groups": we will put one group for
            # every existing macro-group.
            macroGroups = []  # Contains only 1 group of every "macro-group"
            consumedPrefixes = []
            for group in groups:
                prefix = self._getAcronymPrefix(group, group_prefixes)
                if not prefix:
                    group._v_printableName = group.Title()
                    macroGroups.append(group)
                else:
                    if prefix not in consumedPrefixes:
                        consumedPrefixes.append(prefix)
                        group._v_printableName = group_prefixes[prefix]
                        macroGroups.append(group)
            # Every category must have one group from every macro-group
            for catInfo in res:
                for group in macroGroups:
                    self._insertGroupInCategory(catInfo, group, group_prefixes,
                                                groups)
                    # The method does nothing if the group (or another from the
                    # same macro-group) is already there.
        if withCollege and privacy == 'public':
            num = 0
            for items in res:
                num += len(items[1:])
            self.context.REQUEST.set('renumber_first_number', num)
        if renumber:
            # return a list of tuple with first element the number and second
            # element the item itself
            final_res = []
            if privacy == 'secret':
                item_num = self.context.REQUEST.get('renumber_first_number', firstNumber - 1)
            else:
                item_num = firstNumber - 1
            for elts in res:
                final_items = []
                # we received a list of tuple (cat, items_list)
                for item in elts[1:]:
                    if withCollege or forCommission:
                        item_num = item_num + 1
                    else:
                        item_num = self.context.getItemNumsForActe()[item.UID()]
                    final_items.append((item_num, item))
                final_res.append([elts[0], final_items])
            res = final_res
        # allow to return the list of items only, without the list of categories.
        if not groupByCategory:
            alt_res = []
            for category in res:
                for item in category[1:]:
                    alt_res.append(item)
            res = alt_res
        return res

    security.declarePublic('getItemsForAM')

    def getItemsForAM(self, itemUids=[], listTypes=['normal'],
                      ignore_review_states=[], by_proposing_group=False, group_prefixes={},
                      privacy='*', oralQuestion='both', toDiscuss='both', categories=[],
                      excludedCategories=[], firstNumber=1, renumber=False,
                      includeEmptyCategories=False, includeEmptyGroups=False):
        '''Return item's based on getPrintableItemsByCategory. The structure of result is :
           for each element of list
           element[0] = (cat, department) department only if new
           element[1:] = (N°, items, 'LE COLLEGE PROPOSE AU CONSEIL') [if first item to send to council] or
                         (N°, items, 'LE COLLEGE UNIQUEMENT') [if first item to didn't send to college] or
                         (N°, items, '') [if not first items]
        '''
        res = []
        lst = []
        tool = api.portal.get_tool('portal_plonemeeting')
        cfg = tool.getMeetingConfig(self.context)
        for category in cfg.getCategories(onlySelectable=False):
            lst.append(self.getPrintableItemsByCategory(itemUids=itemUids, listTypes=listTypes,
                                                        ignore_review_states=ignore_review_states,
                                                        by_proposing_group=by_proposing_group,
                                                        group_prefixes=group_prefixes,
                                                        privacy=privacy, oralQuestion=oralQuestion,
                                                        toDiscuss=toDiscuss, categories=[category.getId(), ],
                                                        excludedCategories=excludedCategories,
                                                        firstNumber=firstNumber, renumber=renumber,
                                                        includeEmptyCategories=includeEmptyCategories,
                                                        includeEmptyGroups=includeEmptyGroups))
            # we can find department in description
        pre_dpt = '---'
        for intermlst in lst:
            for sublst in intermlst:
                if (pre_dpt == '---') or (pre_dpt != sublst[0].Description()):
                    pre_dpt = sublst[0].Description()
                    dpt = pre_dpt
                else:
                    dpt = ''
                sub_rest = [(sublst[0], dpt)]
                prev_to_send = '---'
                for elt in sublst[1:]:
                    if renumber:
                        for sub_elt in elt:
                            item = sub_elt[1]
                            if (prev_to_send == '---') or (prev_to_send != item.getOtherMeetingConfigsClonableTo()):
                                if item.getOtherMeetingConfigsClonableTo():
                                    txt = 'LE COLLEGE PROPOSE AU CONSEIL D\'ADOPTER LES DECISIONS SUIVANTES'
                                else:
                                    txt = 'LE COLLEGE UNIQUEMENT'
                                prev_to_send = item.getOtherMeetingConfigsClonableTo()
                            else:
                                txt = ''
                            sub_rest.append((sub_elt[0], item, txt))
                    else:
                        item = elt
                        if (prev_to_send == '---') or (prev_to_send != item.getOtherMeetingConfigsClonableTo()):
                            if item.getOtherMeetingConfigsClonableTo():
                                txt = 'LE COLLEGE PROPOSE AU CONSEIL D\'ADOPTER LES DECISIONS SUIVANTES'
                            else:
                                txt = 'LE COLLEGE UNIQUEMENT'
                            prev_to_send = item.getOtherMeetingConfigsClonableTo()
                        else:
                            txt = ''
                        sub_rest.append((item.getItemNumber(relativeTo='meeting'), item, txt))
                res.append(sub_rest)
        return res

    security.declarePublic('getItemNumsForActe')

    def getItemNumsForActe(self):
        '''Create a dict that stores item number regarding the used category.'''
        # for "normal" items, the item number depends on the used category
        # store this in an annotation on the meeting, we only recompte it if meeting was modified
        ann = IAnnotations(self)
        if 'MeetingLiege-getItemNumsForActe' not in ann:
            ann['MeetingLiege-getItemNumsForActe'] = {}
        itemNums = ann['MeetingLiege-getItemNumsForActe']
        if 'modified' in itemNums and itemNums['modified'] == self.modified():
            return itemNums['nums']
        else:
            del ann['MeetingLiege-getItemNumsForActe']
            ann['MeetingLiege-getItemNumsForActe'] = {}
            ann['MeetingLiege-getItemNumsForActe']['modified'] = self.modified()

        tmp_res = {}
        brains = self.getItems(listTypes=['normal'],
                               ordered=True,
                               theObjects=False,
                               unrestricted=True)

        for brain in brains:
            cat = brain.category_id
            if cat in tmp_res:
                tmp_res[cat][brain.UID] = len(tmp_res[cat]) + 1
            else:
                tmp_res[cat] = {}
                tmp_res[cat][brain.UID] = 1

        # initialize res, we need a dict UID/item_num and we have
        # {'Cat1': {'329da4b791b147b1820437e89bee529d': 1,
        #           '41e54c99415b4cc581fbb46afd6ade42': 2},
        #  'Cat2': {'7c65bc5e213e4cde9dfb5538f7558f91': 1}}
        res = {}
        [res.update(v) for v in tmp_res.values()]

        # for "late" items, item number is continuous (HOJ1, HOJ2, HOJ3,... HOJn)
        brains = self.getItems(listTypes=['late'],
                               ordered=True,
                               theObjects=False,
                               unrestricted=True)
        item_num = 1
        for brain in brains:
            res[brain.UID] = item_num
            item_num = item_num + 1
        ann['MeetingLiege-getItemNumsForActe']['nums'] = res.copy()
        ann._p_changed = True
        return res
    Meeting.getItemNumsForActe = getItemNumsForActe

    def getRepresentative(self, sublst, itemUids, privacy='public',
                          listTypes=['normal'], oralQuestion='both', by_proposing_group=False,
                          withCollege=False, renumber=False, firstNumber=1):
        '''Checks if the given category is the same than the previous one. Return none if so and the new one if not.'''
        previousCat = ''
        for sublist in self.getPrintableItemsByCategory(itemUids, privacy=privacy, listTypes=listTypes,
                                                        oralQuestion=oralQuestion,
                                                        by_proposing_group=by_proposing_group,
                                                        withCollege=withCollege,
                                                        renumber=renumber,
                                                        firstNumber=firstNumber):

            if sublist == sublst:
                if sublist[0].Description() != previousCat:
                    return sublist[0].Description()
            previousCat = sublist[0].Description()
        return None

    def getCategoriesByRepresentative(self):
        '''
        Gives a list of list of categories where the first element
        is the description
        '''
        catByRepr = {}
        previousDesc = 'not-an-actual-description'
        tool = api.portal.get_tool('portal_plonemeeting')
        meetingConfig = tool.getMeetingConfig(self.context)
        allCategories = meetingConfig.getCategories(onlySelectable=False)
        # Makes a dictionnary with representative as key and
        # a list of categories as value.
        for category in allCategories:
            if category.Description() not in catByRepr:
                catByRepr[category.Description()] = []
            catByRepr[category.Description()].append(category.getId())
        # Because we need the category to be ordered as in the config,
        # we make a list with representatives in the good order
        representatives = []
        for category in allCategories:
            if category.Description() != previousDesc:
                representatives.append(category.Description())
                previousDesc = category.Description()
        # Finally matches the representatives and categs together
        # and puts everything in a list of list where every first
        # element of the inner list is the representative.
        finalList = []
        catList = []
        for representative in representatives:
            catList.append(representative)
            for category in catByRepr[representative]:
                catList.append(category)
            finalList.append(catList)
            catList = []
        return finalList

    def getCategoriesIdByNumber(self, numCateg):
        '''Returns categories filtered by their roman numerals'''
        tool = api.portal.get_tool('portal_plonemeeting')
        cfg = tool.getMeetingConfig(self.context)
        allCategories = cfg.getCategories()
        categsId = [item.getId() for item in allCategories
                    if item.Title().split('.')[0] == numCateg]
        return categsId

old_checkAlreadyClonedToOtherMC = MeetingItem._checkAlreadyClonedToOtherMC
old_getGroupInCharge = MeetingItem.getGroupInCharge


class CustomMeetingItem(MeetingItem):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCustom.'''
    implements(IMeetingItemCustom)
    security = ClassSecurityInfo()

    customItemDecidedStates = ('accepted',
                               'accepted_but_modified',
                               'delayed',
                               'refused',
                               'marked_not_applicable', )
    MeetingItem.itemDecidedStates = customItemDecidedStates
    customBeforePublicationStates = ('itemcreated',
                                     'proposed_to_administrative_reviewer',
                                     'proposed_to_internal_reviewer',
                                     'proposed_to_director',
                                     'proposed_to_finance',
                                     'validated', )
    MeetingItem.beforePublicationStates = customBeforePublicationStates

    BOURGMESTRE_PROPOSING_GROUP_STATES = [
        'itemcreated', 'proposed_to_administrative_reviewer',
        'proposed_to_internal_reviewer', 'proposed_to_director',
        'proposed_to_director_waiting_advices']

    def __init__(self, item):
        self.context = item

    def is_general_manager(self):
        """Is current user a general manager?"""
        group_id = '{0}_reviewers'.format(org_id_to_uid(GENERAL_MANAGER_GROUP_ID))
        tool = api.portal.get_tool('portal_plonemeeting')
        userGroups = tool.get_plone_groups_for_user()
        return group_id in userGroups

    def is_cabinet_manager(self):
        """Is current user a cabinet manager?"""
        group_id = '{0}_creators'.format(org_id_to_uid(BOURGMESTRE_GROUP_ID))
        tool = api.portal.get_tool('portal_plonemeeting')
        userGroups = tool.get_plone_groups_for_user()
        return group_id in userGroups

    def is_cabinet_reviewer(self):
        """Is current user a cabinet reviewer?"""
        group_id = '{0}_reviewers'.format(org_id_to_uid(BOURGMESTRE_GROUP_ID))
        tool = api.portal.get_tool('portal_plonemeeting')
        userGroups = tool.get_plone_groups_for_user()
        return group_id in userGroups

    security.declarePublic('showOtherMeetingConfigsClonableToEmergency')

    def showOtherMeetingConfigsClonableToEmergency(self):
        '''Widget condition used for field 'otherMeetingConfigsClonableToEmergency'.
           Show it if:
           - optional field is used;
           - is clonable to other MC;
           - item cloned to the other MC will be automatically presented in an available meeting;
           - isManager;
           - or if it was selected so if a MeetingManager selects the emergency for a destination,
             another user editing the item after may not remove 'otherMeetingConfigsClonableTo' without
             removing the 'otherMeetingConfigsClonableToEmergency'.
        '''
        item = self.getSelf()
        # is used?
        if not item.attributeIsUsed('otherMeetingConfigsClonableToEmergency'):
            return False

        tool = api.portal.get_tool('portal_plonemeeting')
        hasStoredEmergencies = item.getOtherMeetingConfigsClonableToEmergency()
        return hasStoredEmergencies or \
            (item.showClonableToOtherMeetingConfigs() and tool.isManager(item))

    security.declarePrivate('validate_archivingRef')

    def validate_archivingRef(self, value):
        '''Field is required.'''
        tool = api.portal.get_tool('portal_plonemeeting')
        cfg = tool.getMeetingConfig(self)
        # Value could be '_none_' if it was displayed as listbox or None if
        # it was displayed as radio buttons...  Use 'flex' format
        if (not self.isDefinedInTool()) and \
           ('archivingRef' in cfg.getUsedItemAttributes()) and \
           (value == '_none_' or not value):
            return translate('archivingRef_required',
                             domain='PloneMeeting',
                             context=self.REQUEST)
    MeetingItem.validate_archivingRef = validate_archivingRef

    security.declareProtected(ModifyPortalContent, 'setCategory')

    def setCategory(self, value, **kwargs):
        '''Overrides the field 'category' mutator to remove stored
           result of the Meeting.getItemNumsForActe on the corresponding meeting.
           If the category of an item in a meeting changed, invaildate also
           MeetingItem.getItemRefForActe ram cache.'''
        current = self.getField('category').get(self)
        meeting = self.getMeeting()
        if current != value and meeting:
            ann = IAnnotations(meeting)
            if 'MeetingLiege-getItemNumsForActe' in ann:
                ann['MeetingLiege-getItemNumsForActe'] = {}
            cleanRamCacheFor('Products.MeetingLiege.adapters.getItemRefForActe')
            # add a value in the REQUEST to specify that updateItemReferences is needed
            self.REQUEST.set('need_Meeting_updateItemReferences', True)
        self.getField('category').set(self, value, **kwargs)
    MeetingItem.setCategory = setCategory

    security.declarePublic('showAdvices')

    def showAdvices(self):
        """We show advices in every case on MeetingItemCollege and MeetingItemCouncil."""
        return True

    security.declarePublic('getExtraFieldsToCopyWhenCloning')

    def getExtraFieldsToCopyWhenCloning(self, cloned_to_same_mc, cloned_from_item_template):
        '''
          Keep some new fields when item is cloned (to another mc or from itemtemplate).
        '''
        res = ['labelForCouncil', 'financeAdvice',
               'decisionSuite', 'decisionEnd', 'toDiscuss']
        if cloned_to_same_mc:
            res = res + ['archivingRef', 'textCheckList']
        return res

    def getCustomAdviceMessageFor(self, advice):
        '''If we are on a finance advice that is still not giveable because
           the item is not 'complete', we display a clear message.'''
        item = self.getSelf()
        tool = api.portal.get_tool('portal_plonemeeting')
        financial_group_uids = tool.financialGroupUids()
        if advice['id'] in financial_group_uids and \
           advice['delay'] and \
           not advice['delay_started_on']:
            # item in state giveable but item not complete
            if item.queryState() in FINANCE_GIVEABLE_ADVICE_STATES:
                return {'displayDefaultComplementaryMessage': False,
                        'customAdviceMessage':
                        translate('finance_advice_not_giveable_because_item_not_complete',
                                  domain="PloneMeeting",
                                  context=item.REQUEST)}
            elif getLastWFAction(item, 'proposeToFinance') and \
                item.queryState() in ('itemcreated',
                                      'itemcreated_waiting_advices',
                                      'proposed_to_internal_reviewer',
                                      'proposed_to_internal_reviewer_waiting_advices',
                                      'proposed_to_director',):
                # advice was already given but item was returned back to the service
                return {'displayDefaultComplementaryMessage': False,
                        'customAdviceMessage': translate(
                            'finance_advice_suspended_because_item_sent_back_to_proposing_group',
                            domain="PloneMeeting",
                            context=item.REQUEST)}
        return {'displayDefaultComplementaryMessage': True,
                'customAdviceMessage': None}

    def getFinanceGroupUIDForItem(self, checkAdviceIndex=False):
        '''Return the finance group UID the advice is asked
           on current item.  It only returns automatically asked advices.
           If p_checkAdviceIndex is True, it will try to get a finance advice
           from the adviceIndex in case financeAdvice is '_none_', it means
           that advice was asked and given at certain time and financeAdvice
           was set back to '_none_' after.'''
        item = self.getSelf()
        finance_advice = item.getFinanceAdvice()
        if finance_advice != '_none_' and \
           finance_advice in item.adviceIndex and \
           not item.adviceIndex[finance_advice]['optional']:
            return finance_advice
        if checkAdviceIndex:
            tool = api.portal.get_tool('portal_plonemeeting')
            financial_group_uids = tool.financialGroupUids()
            for advice_uid, advice_info in item.adviceIndex.items():
                if advice_uid in financial_group_uids and not advice_info['optional']:
                    return advice_uid
        return None

    def _adviceIsEditableByCurrentUser(self, org_uid):
        '''Depending on advice WF state, it is only editable by relevant level.
           This is used by MeetingItem.getAdvicesGroupsInfosForUser.'''
        item = self.getSelf()
        tool = api.portal.get_tool('portal_plonemeeting')
        financial_group_uids = tool.financialGroupUids()

        if org_uid in financial_group_uids:
            member = api.user.get_current()
            adviceObj = item.getAdviceObj(org_uid)
            if not member.has_role('MeetingFinanceEditor', adviceObj):
                return False
        return True

    def _advicePortalTypeForAdviser(self, org_uid):
        """Return the meetingadvicefinances for financial groups, meetingadvice for others."""
        tool = api.portal.get_tool('portal_plonemeeting')
        financial_group_uids = tool.financialGroupUids()
        if org_uid in financial_group_uids:
            return "meetingadvicefinances"
        else:
            return "meetingadvice"

    def _adviceTypesForAdviser(self, meeting_advice_portal_type):
        """Return the advice types (positive, negative, ...) for given p_meeting_advice_portal_type.
           By default we always use every MeetingConfig.usedAdviceTypes but this is useful
           when using several portal_types for meetingadvice and some may use particular advice types."""
        item = self.getSelf()
        tool = api.portal.get_tool('portal_plonemeeting')
        cfg = tool.getMeetingConfig(item)
        if meeting_advice_portal_type == 'meetingadvice':
            return [t for t in cfg.getUsedAdviceTypes() if not t.endswith('_finance')]
        else:
            return [t for t in cfg.getUsedAdviceTypes() if t.endswith('_finance')]

    def _sendAdviceToGiveToGroup(self, org_uid):
        """Do not send an email to FINANCE_GROUP_IDS."""
        tool = api.portal.get_tool('portal_plonemeeting')
        financial_group_uids = tool.financialGroupUids()
        if org_uid in financial_group_uids:
            return False
        return True

    security.declarePublic('mayEvaluateCompleteness')

    def mayEvaluateCompleteness(self):
        '''Condition for editing 'completeness' field,
           being able to define if item is 'complete' or 'incomplete'.
           Completeness can be evaluated by the finance controller.'''
        # user must be a finance controller
        item = self.getSelf()
        if item.isDefinedInTool():
            return
        member = api.user.get_current()
        # bypass for Managers
        if member.has_role('Manager'):
            return True

        financeGroupId = item.adapted().getFinanceGroupUIDForItem()
        # a finance controller may evaluate if advice is actually asked
        # and may not change completeness if advice is currently given or has been given
        tool = api.portal.get_tool('portal_plonemeeting')
        userGroups = tool.get_plone_groups_for_user()
        if not financeGroupId or \
           not '%s_financialcontrollers' % financeGroupId in userGroups:
            return False

        # item must be still in a state where the advice can be given
        # and advice must still not have been given
        if not item.queryState() in FINANCE_GIVEABLE_ADVICE_STATES:
            return False
        return True

    security.declarePublic('mayAskCompletenessEvalAgain')

    def mayAskCompletenessEvalAgain(self):
        '''Condition for editing 'completeness' field,
           being able to ask completeness evaluation again when completeness
           was 'incomplete'.
           Only the 'internalreviewer' and 'reviewer' may ask completeness
           evaluation again and again and again...'''
        # user must be able to edit current item
        item = self.getSelf()
        if item.isDefinedInTool():
            return
        tool = api.portal.get_tool('portal_plonemeeting')
        member = api.user.get_current()
        # user must be able to edit the item and must have 'MeetingInternalReviewer'
        # or 'MeetingReviewer' role
        if not item.getCompleteness() == 'completeness_incomplete' or \
           not member.has_permission(ModifyPortalContent, item) or \
           not (member.has_role('MeetingInternalReviewer', item) or
                member.has_role('MeetingReviewer', item) or tool.isManager(item)):
            return False
        return True

    security.declarePublic('mayAskEmergency')

    def mayAskEmergency(self):
        '''Only directors may ask emergency.'''
        item = self.getSelf()
        member = api.user.get_current()
        if (item.queryState() == 'proposed_to_director' and member.has_role('MeetingReviewer', item)) or \
           member.has_role('Manager', item):
            return True
        return False

    security.declarePublic('mayAcceptOrRefuseEmergency')

    def mayAcceptOrRefuseEmergency(self):
        '''Returns True if current user may accept or refuse emergency if asked for an item.
           Emergency can be accepted only by financial managers.'''
        # by default, only MeetingManagers can accept or refuse emergency
        item = self.getSelf()
        tool = api.portal.get_tool('portal_plonemeeting')
        if tool.isManager(item, realManagers=True) or \
           '%s_financialmanagers' % self.getFinanceGroupUIDForItem() in tool.get_plone_groups_for_user():
            return True
        return False

    security.declarePublic('mayTakeOver')

    def mayTakeOver(self):
        '''Condition for editing 'takenOverBy' field.
           We still use default behaviour :
           A member may take an item over if he his able to change the review_state.
           But when the item is 'proposed_to_finance', the item can be taken over by who can :
           - evaluate completeness;
           - add the advice;
           - change transition of already added advice.'''
        item = self.getSelf()
        if item.queryState() == 'proposed_to_finance':
            # financial controller that may evaluate completeness?
            if item.adapted().mayEvaluateCompleteness():
                return True
            # advice addable or editable?
            (toAdd, toEdit) = item.getAdvicesGroupsInfosForUser()
            if item.getFinanceAdvice() in toAdd or \
               item.getFinanceAdvice() in toEdit:
                return True
        else:
            # original behaviour
            return item.mayTakeOver()

    security.declarePublic('mayAskAdviceAgain')

    def mayAskAdviceAgain(self, advice):
        '''Do not let advice 'asked_again' for FINANCE_GROUP_IDS.
           TREASURY_GROUP_ID advice may be asked again by proposing group
           if it is accepted/accepted_but_modified.
           '''
        tool = api.portal.get_tool('portal_plonemeeting')
        financial_group_uids = tool.financialGroupUids()
        if advice.advice_group in financial_group_uids:
            return False
        if advice.advice_group == org_id_to_uid(TREASURY_GROUP_ID) and \
           self.context.queryState() in ('accepted', 'accepted_but_modified'):
            mGroup = self.context.getProposingGroup(theObject=True)
            if mGroup.userPloneGroups(suffixes=['internalreviewers', 'reviewers']):
                return True
        return self.context.mayAskAdviceAgain(advice)

    security.declarePrivate('listFinanceAdvices')

    def listFinanceAdvices(self):
        '''Vocabulary for the 'financeAdvice' field.'''
        res = []
        res.append(('_none_', translate('no_financial_impact',
                                        domain='PloneMeeting',
                                        context=self.REQUEST)))
        tool = api.portal.get_tool('portal_plonemeeting')
        financial_group_uids = tool.financialGroupUids()
        for finance_group_uid in financial_group_uids:
            res.append((finance_group_uid, get_organization(finance_group_uid).Title()))
        return DisplayList(tuple(res))
    MeetingItem.listFinanceAdvices = listFinanceAdvices

    security.declarePrivate('listArchivingRefs')

    def listArchivingRefs(self):
        '''Vocabulary for the 'archivingRef' field.'''
        res = []
        tool = api.portal.get_tool('portal_plonemeeting')
        cfg = tool.getMeetingConfig(self)
        userGroups = set([group.getId() for group in tool.get_orgs_for_user()])
        isManager = tool.isManager(self)
        storedArchivingRef = self.getArchivingRef()
        for ref in cfg.getArchivingRefs():
            # if ref is not active, continue
            if ref['active'] == '0':
                continue
            # only keep an active archiving ref if :
            # current user isManager
            # it is the currently selected archiving ref
            # if ref is restricted to some groups and current member of this group
            if not isManager and \
               not ref['row_id'] == storedArchivingRef and \
               (ref['restrict_to_groups'] and not set(ref['restrict_to_groups']).intersection(userGroups)):
                continue
            res.append((ref['row_id'], ref['label']))
        res.insert(0, ('_none_', translate('make_a_choice',
                                           domain='PloneMeeting',
                                           context=self.REQUEST)))
        return DisplayList(tuple(res))
    MeetingItem.listArchivingRefs = listArchivingRefs

    security.declarePublic('needFinanceAdviceOf')

    def needFinanceAdviceOf(self, financeGroupId):
        '''
          Method that returns True if current item needs advice of
          given p_financeGroupId.
          We will check if given p_financeGroupId correspond to the selected
          value of MeetingItem.financeAdvice.
        '''
        item = self.getSelf()
        # automatically ask finance advice if it is the currently selected financeAdvice
        # and if the advice given on a predecessor is still not valid for this item
        if item.getFinanceAdvice() == org_id_to_uid(financeGroupId) and \
           item.adapted().getItemWithFinanceAdvice() == item:
            return True
        return False

    security.declarePublic('getFinancialAdviceStuff')

    def getFinancialAdviceStuff(self):
        '''Get the financial advice signature date, advice type and comment'''
        res = {}
        item = self.getSelf()
        financialAdvice = item.getFinanceAdvice()
        adviceData = item.getAdviceDataFor(item, financialAdvice)
        res['comment'] = 'comment' in adviceData\
            and adviceData['comment'] or ''
        advice_id = 'advice_id' in adviceData\
            and adviceData['advice_id'] or ''
        signature_event = advice_id and getLastWFAction(getattr(item, advice_id), 'signFinancialAdvice') or ''
        res['out_of_financial_dpt'] = 'time' in signature_event and signature_event['time'] or ''
        res['out_of_financial_dpt_localized'] = res['out_of_financial_dpt']\
            and res['out_of_financial_dpt'].strftime('%d/%m/%Y') or ''
        # "positive_with_remarks_finance" will be printed "positive_finance"
        if adviceData['type'] == 'positive_with_remarks_finance':
            type_translated = translate('positive_finance',
                                        domain='PloneMeeting',
                                        context=item.REQUEST).encode('utf-8')
        else:
            type_translated = adviceData['type_translated'].encode('utf-8')
        res['advice_type'] = '<p><u>Type d\'avis:</u>  %s</p>' % type_translated
        res['delay_started_on_localized'] = 'delay_started_on_localized' in adviceData['delay_infos']\
            and adviceData['delay_infos']['delay_started_on_localized'] or ''
        res['delay_started_on'] = 'delay_started_on' in adviceData\
            and adviceData['delay_started_on'] or ''
        return res

    def getItemRefForActe_cachekey(method, self, acte=True):
        '''cachekey method for self.getItemRefForActe.'''
        # invalidate cache if passed parameter changed or if item was modified
        item = self.getSelf()
        meeting = item.getMeeting()
        return (item, acte, item.modified(), meeting.modified())

    security.declarePublic('getItemRefForActe')

    @ram.cache(getItemRefForActe_cachekey)
    def getItemRefForActe(self, acte=True):
        '''the reference is cat id/itemnumber in this cat/PA if it's not to discuss'''
        item = self.getSelf()
        item_num = item.getMeeting().getItemNumsForActe()[item.UID()]
        if not item.isLate():
            res = '%s' % item.getCategory(True).getCategoryId()
            res = '%s%s' % (res, item_num)
        else:
            res = 'HOJ.%s' % item_num
        if not item.getToDiscuss():
            res = '%s (PA)' % res
        if item.getSendToAuthority() and acte is False:
            res = '%s (TG)' % res
        return res

    def isCurrentUserInFDGroup(self, finance_group_id):
        '''
          Returns True if the current user is in the given p_finance_group_id.
        '''
        tool = api.portal.get_tool('portal_plonemeeting')
        userGroups = tool.get_plone_groups_for_user()
        suffixedGroups = []
        for suffix in FINANCE_GROUP_SUFFIXES:
            suffixedGroups.append("{0}_{1}".format(finance_group_id, suffix))
        if set(userGroups).intersection(suffixedGroups):
            return True
        return False

    def mayGenerateFDAdvice(self):
        '''
          Returns True if the current user has the right to generate the
          Financial Director Advice template.
        '''
        adviceHolder = self.adapted().getItemWithFinanceAdvice()

        if adviceHolder.getFinanceAdvice() != '_none_' and \
            (adviceHolder.adviceIndex[adviceHolder.getFinanceAdvice()]['hidden_during_redaction'] is False or
             self.isCurrentUserInFDGroup(adviceHolder.getFinanceAdvice()) is True or
             adviceHolder.adviceIndex[adviceHolder.getFinanceAdvice()]['advice_editable'] is False):
            return True
        return False

    def _checkAlreadyClonedToOtherMC(self, destMeetingConfigId):
        ''' '''
        res = old_checkAlreadyClonedToOtherMC(self, destMeetingConfigId)
        if not res and not getLastWFAction(self, 'Duplicate and keep link'):
            # if current item is not linked automatically using a 'Duplicate and keep link'
            # double check if a predecessor was not already sent to the other meetingConfig
            # this can be the case when using 'accept_and_return' transition, the item is sent
            # and another item is cloned with same informations.  Check also that if a predecessor
            # was already sent to the council, this item in the council is not 'delayed' or 'marked_not_applicable'
            # in this case, we will send it again
            predecessor = self.getPredecessor()
            while predecessor:
                if predecessor.queryState() == 'accepted_and_returned' and \
                   old_checkAlreadyClonedToOtherMC(predecessor, destMeetingConfigId):
                    # if item was sent to council, check that this item is not 'delayed' or 'returned'
                    councilClonedItem = predecessor.getItemClonedToOtherMC(destMeetingConfigId)
                    if councilClonedItem and not councilClonedItem.queryState() in ('delayed', 'returned'):
                        return True
                # break the loop if we encounter an item that was 'Duplicated and keep link'
                # and it is not an item that is 'accepted_and_returned'
                if getLastWFAction(predecessor, 'Duplicate and keep link'):
                    return res
                predecessor = predecessor.getPredecessor()
        return res
    MeetingItem._checkAlreadyClonedToOtherMC = _checkAlreadyClonedToOtherMC

    def getItemWithFinanceAdvice(self):
        '''
          Make sure we have the item containing the finance advice.
          Indeed, in case an item is created as a result of a 'return_college',
          the advice itself is left on the original item (that is in state 'returned' or 'accepted_and_returned')
          and no more on the current item.  In this case, get the advice on the predecessor item.
        '''
        def _predecessorIsValid(current, predecessor, financeAdvice):
            """ """
            # predecessor is valid only if 'returned' or sent back to council/back to college
            if not (getLastWFAction(current, 'return') or
                    getLastWFAction(current, 'accept_and_return') or
                    getLastWFAction(current, 'create_to_meeting-config-college_from_meeting-config-council') or
                    getLastWFAction(current, 'create_to_meeting-config-council_from_meeting-config-college')):
                return False

            # council item and predecessor is a College item
            # in any case, the finance advice is kept
            if current.portal_type == 'MeetingItemCouncil' and predecessor.portal_type == 'MeetingItemCollege':
                return True
            # college item and predecessor council item in state 'returned'
            if current.portal_type == 'MeetingItemCollege' and \
               (predecessor.portal_type == 'MeetingItemCouncil' and
                    predecessor.queryState() in ('returned', )):
                return True
            # college item and predecessor college item in state ('accepted_returned', 'returned')
            if current.portal_type == 'MeetingItemCollege' and \
               (predecessor.portal_type == 'MeetingItemCollege' and
                    predecessor.queryState() in ('returned', 'accepted_and_returned')):
                return True

        item = self.context
        # check if current self.context does not contain the given advice
        # and if it is an item as result of a return college
        # in case we use the finance advice of another item,
        # the getFinanceAdvice is not _none_
        # but the financeAdvice is not in adviceIndex
        financeAdvice = item.getFinanceAdvice()
        # no finance advice, return self.context
        if financeAdvice == '_none_':
            return item
        # finance advice on self
        # and item was not returned (from college or council), return item
        if (financeAdvice in item.adviceIndex and
           item.adviceIndex[financeAdvice]['type'] != NOT_GIVEN_ADVICE_VALUE):
            return item

        # we will walk predecessors until we found a finance advice that has been given
        # if we do not find a given advice, we will return the oldest item (last predecessor)
        predecessor = item.getPredecessor()
        currentItem = item
        # consider only if predecessor is in state 'accepted_and_returned' or 'returned' (College or Council item)
        # otherwise, the predecessor could have been edited and advice is no longer valid
        while predecessor and _predecessorIsValid(currentItem, predecessor, financeAdvice):
            current_finance_advice = predecessor.getFinanceAdvice()
            # check if finance_advice is selected if if it is not an optional one
            # indeed it may occur that the optional finance advice is asked
            if current_finance_advice and \
               current_finance_advice in predecessor.adviceIndex and \
               not predecessor.adviceIndex[current_finance_advice]['optional']:
                return predecessor
            currentItem = predecessor
            predecessor = predecessor.getPredecessor()
        # either we found a valid predecessor, or we return self.context
        return item

    def getItemCollege(self):
        """Called on a Council item, will return the linked College item."""
        predecessor = self.context.getPredecessor()
        while predecessor and not predecessor.portal_type == 'MeetingItemCollege':
            predecessor = predecessor.getPredecessor()
        return predecessor

    def getLegalTextForFDAdvice(self, isMeeting=False):
        '''
        Helper method. Return legal text for each advice type.
        '''
        adviceHolder = self.adapted().getItemWithFinanceAdvice()
        if not adviceHolder.adapted().mayGenerateFDAdvice():
            return ''

        financialStuff = adviceHolder.adapted().getFinancialAdviceStuff()
        adviceInd = adviceHolder.adviceIndex[adviceHolder.getFinanceAdvice()]
        advice = adviceHolder.getAdviceDataFor(adviceHolder, adviceHolder.getFinanceAdvice())
        hidden = advice['hidden_during_redaction']
        statusWhenStopped = advice['delay_infos']['delay_status_when_stopped']
        adviceType = adviceInd['type']
        comment = financialStuff['comment']
        adviceGivenOnLocalized = advice['advice_given_on_localized']
        delayStartedOnLocalized = advice['delay_infos']['delay_started_on_localized']
        if not delayStartedOnLocalized:
            adviceHolder_completeness_changes_adapter = getAdapter(
                adviceHolder, IImioHistory, 'completeness_changes')
            last_completeness_complete_action = getLastAction(
                adviceHolder_completeness_changes_adapter,
                action='completeness_complete')
            if last_completeness_complete_action:
                delayStartedOnLocalized = adviceHolder.toLocalizedTime(last_completeness_complete_action['time'])
        delayStatus = advice['delay_infos']['delay_status']
        outOfFinancialdptLocalized = financialStuff['out_of_financial_dpt_localized']
        limitDateLocalized = advice['delay_infos']['limit_date_localized']

        if not isMeeting:
            res = FINANCE_ADVICE_LEGAL_TEXT_PRE.format(delayStartedOnLocalized)

        if not hidden and \
           adviceGivenOnLocalized and \
           (adviceType in (u'positive_finance', u'positive_with_remarks_finance', u'negative_finance')):
            if adviceType in (u'positive_finance', u'positive_with_remarks_finance'):
                adviceTypeFr = 'favorable'
            else:
                adviceTypeFr = 'défavorable'
            # if it's a meetingItem, return the legal bullshit.
            if not isMeeting:
                res = res + FINANCE_ADVICE_LEGAL_TEXT.format(
                    adviceTypeFr,
                    outOfFinancialdptLocalized
                )
            # if it's a meeting, returns only the type and date of the advice.
            else:
                res = "<p>Avis {0} du Directeur Financier du {1}</p>".format(
                    adviceTypeFr, outOfFinancialdptLocalized)

            if comment and adviceType == u'negative_finance':
                res = res + "<p>{0}</p>".format(comment)
        elif statusWhenStopped == 'stopped_timed_out' or delayStatus == 'timed_out':
            if not isMeeting:
                res = res + FINANCE_ADVICE_LEGAL_TEXT_NOT_GIVEN
            else:
                res = "<p>Avis du Directeur financier expiré le {0}</p>".format(limitDateLocalized)
        else:
            res = ''
        return res

    security.declarePublic('adaptCouncilItemDecisionEnd')

    def adaptCouncilItemDecisionEnd(self):
        """When a council item is 'presented', we automatically append a sentence
           to the 'decisionEnd' field, this is managed by MeetingConfig.onTransitionFieldTransforms
           that calls this method."""
        item = self.getSelf()
        transforms = api.portal.get_tool('portal_transforms')
        rawDecisionEnd = item.getDecisionEnd(mimetype='text/plain').strip()
        # COUNCILITEM_DECISIONEND_SENTENCE is HTML
        rawSentence = transforms.convertTo('text/plain', COUNCILITEM_DECISIONEND_SENTENCE)._data.strip()
        if rawSentence not in rawDecisionEnd:
            return item.getDecisionEnd() + COUNCILITEM_DECISIONEND_SENTENCE
        else:
            return item.getDecisionEnd()

    def updateFinanceAdvisersAccess(self, old_local_roles={}):
        """ """
        item = self.getSelf()
        item.adapted()._updateFinanceAdvisersAccessToAutoLinkedItems()
        item.adapted()._updateFinanceAdvisersAccessToManuallyLinkedItems(old_local_roles)

    def _updateFinanceAdvisersAccessToManuallyLinkedItems(self, old_local_roles):
        '''
          Make sure finance advisers have access to every items that are manually linked
          between each other in any case, this have to manage :
          - current item has finance advice, make sure other items are accessible;
          - current item does not have a finance advice but we do a link to an item that has
            a finance advice, current item must be accessible;
          - when a linked item is removed (link to an item is removed), we need to update it
            if finance adviser access must be removed.
        '''
        item = self.getSelf()

        # avoid circular calls, avoid updateLocalRoles here under to enter further
        if item.REQUEST.get('_updateFinanceAdvisersAccessToManuallyLinkedItems', False):
            return
        item.REQUEST.set('_updateFinanceAdvisersAccessToManuallyLinkedItems', True)

        # first step, walk every items including self to check what finance adviser
        # should have access to every items
        linkedItems = item.getManuallyLinkedItems()
        finance_accesses = []
        for linkedItem in linkedItems + [item]:
            financeAdvice = linkedItem.getFinanceAdvice()
            if financeAdvice != '_none_' and financeAdvice not in finance_accesses:
                # only add it if finance advisers have already access to the linkedItem
                groupId = "{0}_advisers".format(financeAdvice)
                if groupId in linkedItem.__ac_local_roles__ and \
                   READER_USECASES['advices'] in linkedItem.__ac_local_roles__[groupId]:
                    finance_accesses.append(groupId)
                    # already update self so here under every local_roles for self are computed
                    item.manage_addLocalRoles(groupId, (READER_USECASES['advices'], ))

        # we finished to compute all local_roles for self, compare to finance access
        # that were given in old local_roles if it is the same,
        # it means that we do not need to update linked items
        tool = api.portal.get_tool('portal_plonemeeting')
        financial_group_uids = tool.financialGroupUids()
        potentialFinanceAccesses = set(["{0}_advisers".format(finance_advice_uid) for
                                        finance_advice_uid in financial_group_uids])
        financeInOldLocalRoles = potentialFinanceAccesses.intersection(set(old_local_roles.keys()))
        financeInNewLocalRoles = potentialFinanceAccesses.intersection(set(item.__ac_local_roles__.keys()))

        itemsToUpdate = []
        catalog = api.portal.get_tool('portal_catalog')
        if financeInOldLocalRoles != financeInNewLocalRoles:
            # we need to update every linked items
            itemsToUpdate = linkedItems
        else:
            # just need to update newly linked items
            newLinkedUids = item.REQUEST.get('manuallyLinkedItems_newLinkedUids', [])
            if newLinkedUids:
                # newLinkedUids is a set(), it does not work with catalog, cast to list
                brains = catalog.unrestrictedSearchResults(UID=list(newLinkedUids))
                itemsToUpdate = [brain._unrestrictedGetObject() for brain in brains]

        for itemToUpdate in itemsToUpdate:
            itemToUpdate.updateLocalRoles()
            for finance_access in finance_accesses:
                if finance_access not in itemToUpdate.__ac_local_roles__:
                    itemToUpdate.manage_addLocalRoles(finance_access, (READER_USECASES['advices'], ))
                    itemToUpdate.reindexObjectSecurity()

        # now we need removeUids to be updated too, we will call updateLocalRoles on removeUids
        removedUids = item.REQUEST.get('manuallyLinkedItems_removedUids', [])
        for removeUid in removedUids:
            removedBrain = catalog.unrestrictedSearchResults(UID=removeUid)
            if removedBrain:
                removedItem = removedBrain[0]._unrestrictedGetObject()
                removedItem.updateLocalRoles()

        # cancel manuallyLinkedItems_... values
        item.REQUEST.set('manuallyLinkedItems_newLinkedUids', [])
        item.REQUEST.set('manuallyLinkedItems_removedUids', [])
        item.REQUEST.set('_updateFinanceAdvisersAccessToManuallyLinkedItems', False)

    def _updateFinanceAdvisersAccessToAutoLinkedItems(self):
        '''
          Make sure finance advisers have still access to items linked to an item for which they
          give an advice on.  This could be the case :
          - when an item is 'returned', the finance advice given on the 'returned' item is still
            the advice we consider, also for the new item that is directly validated;
          - when an item is sent to the council.
          In both cases, the finance advice is not asked anymore
          but we need to give a read access to the corresponding finance advisers.
        '''
        item = self.getSelf()
        if item.getFinanceAdvice() == '_none_':
            return

        # make sure finance advisers have access to an item
        # that is not the itemWithFinanceAdvice holder
        itemWithFinanceAdvice = item.adapted().getItemWithFinanceAdvice()
        if itemWithFinanceAdvice != item:
            # ok, we have a predecessor with finance access, give access to current item also
            groupId = "{0}_advisers".format(itemWithFinanceAdvice.getFinanceAdvice())
            item.manage_addLocalRoles(groupId, (READER_USECASES['advices'], ))

    def getGroupInCharge(self, theObject=False, **kwargs):
        '''Redefine getGroupInCharge to return the group in charge of matter.'''
        item = self.getSelf()
        category = item.getCategory(theObject=True)
        if category and category.meta_type == 'MeetingCategory':
            for groupOfMatter in category.getGroupsOfMatter():
                res = groupOfMatter
                if theObject:
                    res = get_organization(groupOfMatter)
                return res
        return ''

    MeetingItem.getGroupInCharge = getGroupInCharge

    def _getAllGroupsManagingItem(self):
        """ """
        item = self.getSelf()
        res = [item.getProposingGroup(True)]
        if item.portal_type == 'MeetingItemBourgmestre':
            review_state = item.queryState()
            if review_state not in self.BOURGMESTRE_PROPOSING_GROUP_STATES:
                res.append(get_organization(org_id_to_uid(GENERAL_MANAGER_GROUP_ID)))
                if review_state not in ['proposed_to_general_manager']:
                    res.append(get_organization(org_id_to_uid(BOURGMESTRE_GROUP_ID)))
        return res

    def _getGroupManagingItem(self, review_state, theObject=True):
        """ """
        item = self.getSelf()
        if item.portal_type != 'MeetingItemBourgmestre':
            return item.getProposingGroup(theObject=theObject)
        else:
            # administrative states or item presented to a meeting,
            # proposingGroup is managing the item
            if review_state in self.BOURGMESTRE_PROPOSING_GROUP_STATES + ['validated'] or item.hasMeeting():
                return item.getProposingGroup(theObject=theObject)
            # general manager, we take the _reviewers group
            elif review_state in ['proposed_to_general_manager']:
                gm_uid = org_id_to_uid(GENERAL_MANAGER_GROUP_ID)
                return theObject and get_organization(gm_uid) or gm_uid
            else:
                bg_uid = org_id_to_uid(BOURGMESTRE_GROUP_ID)
                return theObject and get_organization(bg_uid) or bg_uid

    def _setBourgmestreGroupsReadAccess(self):
        """Depending on item's review_state, we need to give Reader role to the proposing group
           and general manager so it keeps Read access to item when it is managed by the Cabinet."""
        item = self.getSelf()
        item_state = item.queryState()
        # give 'Reader' role for every suffixes except 'observers' that
        # only gets access when item is positively decided
        item_managing_group = item.adapted()._getGroupManagingItem(item_state)
        proposingGroup = item.getProposingGroup(theObject=True)
        # when proposingGroup is no more the managing group, it means item is at least
        # proposed to general manager, give read access to proposingGroup and to general manager
        # if it is not the managing group
        if item_managing_group != proposingGroup:
            item._assign_roles_to_group_suffixes(proposingGroup, ignored_suffixes=['observers'])
        # access for GENERAL_MANAGER_GROUP_ID groups
        if item_state not in self.BOURGMESTRE_PROPOSING_GROUP_STATES + ['proposed_to_general_manager']:
            gm_org = get_organization(org_id_to_uid(GENERAL_MANAGER_GROUP_ID))
            item._assign_roles_to_group_suffixes(gm_org, ignored_suffixes=['observers'])
        # access for BOURGMESTRE_GROUP_ID groups
        if item_state not in self.BOURGMESTRE_PROPOSING_GROUP_STATES + \
                ['proposed_to_general_manager',
                 'proposed_to_cabinet_manager',
                 'proposed_to_cabinet_reviewer']:
            bg_org = get_organization(org_id_to_uid(BOURGMESTRE_GROUP_ID))
            item._assign_roles_to_group_suffixes(bg_org, ignored_suffixes=['observers'])

    def _findCustomOneLevelFor(self, insertMethod):
        '''Manage our custom inserting method 'on_decision_first_word'.'''
        if insertMethod == 'on_decision_first_word':
            return 262626262626
        raise NotImplementedError

    def _findCustomOrderFor(self, insertMethod):
        '''Manage our custom inserting method 'on_decision_first_word'.'''
        item = self.getSelf()
        if insertMethod == 'on_decision_first_word':
            decision = item.getDecision(mimetype='text/plain').strip()
            # make sure we do not have accents anymore and a lowerized string
            if not isinstance(decision, unicode):
                decision = unicode(decision, 'utf-8')
            decision = ''.join(x for x in unicodedata.normalize('NFKD', decision) if x in string.ascii_letters).lower()
            word = decision.split(' ')[0]
            word = word[0:6]
            # make sure first is a 6 characters long word
            word = word.ljust(6, 'a')
            # now that we have a 6 characters long string, we will build index by
            # computing ord() for each char and making a long integer with it
            index = []
            for char in word:
                # translate received value to less integer
                # in theory, we have only lowercased chars in word
                # ord('a') is 97, and ord('z') is 122, so remove 96...
                index.append(str(ord(char) - 96).zfill(2))
            return int(''.join(index))
        raise NotImplementedError

    def getOfficeManager(self):
        '''
        Allows to get the office manager's name, even if the item is
        returned multiple times.
        '''
        # If we have the name of the office manager, we just return it.
        if getLastWFAction(self.context, 'proposeToDirector'):
            offMan = getLastWFAction(self.context, 'proposeToDirector')['actor']
        # Else we look for a predecessor which can have the intel.
        elif self.context.getPredecessor():
            offMan = ''
            predecessor = self.context.getPredecessor()
            # loops while the item has no office manager
            while predecessor and not offMan:
                if getLastWFAction(predecessor, 'proposeToDirector'):
                    offMan = getLastWFAction(predecessor, 'proposeToDirector')['actor']
                predecessor = predecessor.getPredecessor()
        else:
            return ''

        user = {}
        membershipTool = api.portal.get_tool('portal_membership')
        user['fullname'] = membershipTool.getMemberInfo(str(offMan))['fullname']
        memberInfos = membershipTool.getMemberById(offMan)
        user['phone'] = memberInfos.getProperty('description').split("     ")[0]
        user['email'] = memberInfos.getProperty('email')
        return user

    def _itemIsSignedStates(self):
        """In which states must we show the itemIsSigned widget?
           Default (item is decided) and presented/itemfrozen."""
        item = self.getSelf()
        return ('presented', 'itemfrozen') + item._itemIsSignedStates()

    def _isViewableByPowerObservers(self, restrictedPowerObservers=False):
        """Restricted power observers may not have access to 'late' items in Council
           until it is decided."""
        item = self.getSelf()
        if restrictedPowerObservers and \
           item.portal_type == 'MeetingItemCouncil' and \
           item.getListType() in ('late', ) and \
           item.queryState() in ('presented', 'itemfrozen', 'returned_to_proposing_group'):
            return False
        return True

    def treasuryCopyGroup(self):
        """Manage fact that group TREASURY_GROUP_ID _observers must be automatically
           set as copyGroup of items for which the finances advice was asked.
           It will have access from the 'validated' and 'sent_to_council_emergency'
           state and beyond.
           This is used in the MeetingGroup.asCopyGroupOn field."""
        item = self.getSelf()
        if item.getFinanceAdvice() != '_none_' and \
           (item.queryState() in ('validated', 'sent_to_council_emergency') or item.hasMeeting()):
            return ['observers']
        else:
            return []


old_listAdviceTypes = MeetingConfig.listAdviceTypes


class CustomMeetingConfig(MeetingConfig):
    '''Adapter that adapts a meetingConfig implementing IMeetingConfig to the
       interface IMeetingConfigCustom.'''

    implements(IMeetingConfigCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    security.declarePrivate('listArchivingReferenceFinanceAdvices')

    def listArchivingReferenceFinanceAdvices(self):
        tool = api.portal.get_tool('portal_plonemeeting')
        res = []
        res.append(("no_finance_advice",
                    translate('no_finance_advice',
                              domain='PloneMeeting',
                              context=self.REQUEST,
                              default='No finance advice')))
        tool = api.portal.get_tool('portal_plonemeeting')
        financial_group_uids = tool.financialGroupUids()
        for org_uid in financial_group_uids:
            res.append((org_uid, get_organization(org_uid).Title()))
        return DisplayList(res)
    MeetingConfig.listArchivingReferenceFinanceAdvices = listArchivingReferenceFinanceAdvices

    security.declarePrivate('listActiveOrgsForArchivingRefs')

    def listActiveOrgsForArchivingRefs(self):
        """
          Vocabulary for the archivingRefs.restrict_to_orgs DatagridField attribute.
          It returns every active organizations.
        """
        res = []
        for org in get_organizations():
            res.append((org.UID(), org.Title()))
        # make sure that if a configuration was defined for a group
        # that is now inactive, it is still displayed
        storedArchivingRefsOrgs = [archivingRef['restrict_to_groups'] for archivingRef in self.getArchivingRefs()]
        if storedArchivingRefsOrgs:
            orgsInVocab = [org[0] for org in res]
            for storedArchivingRefsOrg in storedArchivingRefsOrgs:
                for org_uid in storedArchivingRefsOrg:
                    if org_uid not in orgsInVocab:
                        org = get_organization(org_uid)
                        res.append((org_uid, org.Title()))
        return DisplayList(res).sortedByValue()
    MeetingConfig.listActiveOrgsForArchivingRefs = listActiveOrgsForArchivingRefs

    security.declareProtected('Modify portal content', 'setArchivingRefs')

    def setArchivingRefs(self, value, **kwargs):
        '''Overrides the field 'archivingRefs' mutator to manage
           the 'row_id' column manually.  If empty, we need to add a
           unique id into it.'''
        # value contains a list of 'ZPublisher.HTTPRequest', to be compatible
        # if we receive a 'dict' instead, we use v.get()
        for v in value:
            # don't process hidden template row as input data
            if v.get('orderindex_', None) == "template_row_marker":
                continue
            if not v.get('row_id', None):
                if isinstance(v, dict):
                    v['row_id'] = self.generateUniqueId()
                else:
                    v.row_id = self.generateUniqueId()
        self.getField('archivingRefs').set(self, value, **kwargs)
    MeetingConfig.setArchivingRefs = setArchivingRefs

    def _dataForArchivingRefRowId(self, row_id):
        '''Returns the data for the given p_row_id from the field 'archivingRefs'.'''
        cfg = self.getSelf()
        for archivingRef in cfg.getArchivingRefs():
            if archivingRef['row_id'] == row_id:
                return dict(archivingRef)

    def _extraSearchesInfo(self, infos):
        """Add some specific searches."""
        cfg = self.getSelf()
        extra_infos = OrderedDict(
            [
                # Items in state 'proposed_to_finance' for which
                # completeness is not 'completeness_complete'
                ('searchitemstocontrolcompletenessof',
                    {
                        'subFolderId': 'searches_items',
                        'active': True,
                        'query':
                        [
                            {'i': 'CompoundCriterion',
                             'o': 'plone.app.querystring.operation.compound.is',
                             'v': 'items-to-control-completeness-of'},
                        ],
                        'sort_on': u'created',
                        'sort_reversed': True,
                        'tal_condition': "python: (here.REQUEST.get('fromPortletTodo', False) and "
                                         "tool.userIsAmong(['financialcontrollers'])) "
                                         "or (not here.REQUEST.get('fromPortletTodo', False) and "
                                         "tool.isFinancialUser())",
                        'roles_bypassing_talcondition': ['Manager', ]
                    }
                 ),
                # Items having advice in state 'proposed_to_financial_controller'
                ('searchadviceproposedtocontroller',
                    {
                        'subFolderId': 'searches_items',
                        'active': True,
                        'query':
                        [
                            {'i': 'CompoundCriterion',
                             'o': 'plone.app.querystring.operation.compound.is',
                             'v': 'items-with-advice-proposed-to-financial-controller'},
                        ],
                        'sort_on': u'created',
                        'sort_reversed': True,
                        'tal_condition': "python: (here.REQUEST.get('fromPortletTodo', False) and "
                                         "tool.userIsAmong(['financialcontrollers'])) "
                                         "or (not here.REQUEST.get('fromPortletTodo', False) and "
                                         "tool.isFinancialUser())",
                        'roles_bypassing_talcondition': ['Manager', ]
                    }
                 ),
                # Items having advice in state 'proposed_to_financial_reviewer'
                ('searchadviceproposedtoreviewer',
                    {
                        'subFolderId': 'searches_items',
                        'active': True,
                        'query':
                        [
                            {'i': 'CompoundCriterion',
                             'o': 'plone.app.querystring.operation.compound.is',
                             'v': 'items-with-advice-proposed-to-financial-reviewer'},
                        ],
                        'sort_on': u'created',
                        'sort_reversed': True,
                        'tal_condition': "python: (here.REQUEST.get('fromPortletTodo', False) and "
                                         "tool.userIsAmong(['financialreviewers'])) "
                                         "or (not here.REQUEST.get('fromPortletTodo', False) and "
                                         "tool.isFinancialUser())",
                        'roles_bypassing_talcondition': ['Manager', ]
                    }
                 ),
                # Items having advice in state 'proposed_to_financial_manager'
                ('searchadviceproposedtomanager',
                    {
                        'subFolderId': 'searches_items',
                        'active': True,
                        'query':
                        [
                            {'i': 'CompoundCriterion',
                             'o': 'plone.app.querystring.operation.compound.is',
                             'v': 'items-with-advice-proposed-to-financial-manager'},
                        ],
                        'sort_on': u'created',
                        'sort_reversed': True,
                        'tal_condition': "python: (here.REQUEST.get('fromPortletTodo', False) and "
                                         "tool.userIsAmong(['financialmanagers'])) "
                                         "or (not here.REQUEST.get('fromPortletTodo', False) and "
                                         "tool.isFinancialUser())",
                        'roles_bypassing_talcondition': ['Manager', ]
                    }
                 ),
            ]
        )

        infos.update(extra_infos)
        # add the 'searchitemswithfinanceadvice' for 'meeting-config-college'
        if cfg.getId() in ('meeting-config-college'):
            finance_infos = OrderedDict(
                [
                    # Items for finance advices synthesis
                    ('searchitemswithfinanceadvice',
                        {
                            'subFolderId': 'searches_items',
                            'active': True,
                            'query':
                            [
                                {'i': 'portal_type',
                                 'o': 'plone.app.querystring.operation.selection.is',
                                 'v': ['MeetingItemCollege']},
                                {'i': 'indexAdvisers',
                                 'o': 'plone.app.querystring.operation.selection.is',
                                 'v': ['delay_real_group_id__2014-06-05.5584062390',
                                       'delay_real_group_id__2014-06-05.5584062584',
                                       'delay_real_group_id__2014-06-05.5584070070',
                                       'delay_real_group_id__2014-06-05.5584074805',
                                       'delay_real_group_id__2014-06-05.5584079907',
                                       'delay_real_group_id__2014-06-05.5584080681']}
                            ],
                            'sort_on': u'created',
                            'sort_reversed': True,
                            'tal_condition': "python: tool.isFinancialUser() or tool.isManager(here)",
                            'roles_bypassing_talcondition': ['Manager', ]
                        }
                     ),
                ]
            )
            infos.update(finance_infos)
        return infos

    def extraAdviceTypes(self):
        '''See doc in interfaces.py.'''
        return ("positive_finance", "positive_with_remarks_finance",
                "negative_finance", "not_required_finance")

    def extraInsertingMethods(self):
        '''See doc in interfaces.py.'''
        return ['on_decision_first_word']


class CustomMeetingCategory(MeetingCategory):
    '''Adapter that adapts a meetingCategory implementing IMeetingCategory to the
       interface IMeetingCategoryCustom.'''

    implements(IMeetingCategoryCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    security.declarePrivate('listGroupsOfMatter')

    def listGroupsOfMatter(self):
        """
          Vocabulary for the MeetingCategory.groupsOfMatter field.
          It returns every active organizations.
        """
        res = []
        for org in get_organizations():
            res.append((org.UID(), org.Title()))
        # make sure that if a configuration was defined for an organization
        # that is now inactive, it is still displayed
        storedGroupsOfMatter = self.getGroupsOfMatter()
        if storedGroupsOfMatter:
            orgsInVocab = [org[0] for org in res]
            for org_uid in storedGroupsOfMatter:
                if org_uid not in orgsInVocab:
                    org = get_organization(org_uid)
                    if org:
                        res.append((org_uid, org.Title()))
                    else:
                        res.append((org_uid, org_uid))
        return DisplayList(res).sortedByValue()
    MeetingCategory.listGroupsOfMatter = listGroupsOfMatter

    security.declareProtected('Modify portal content', 'onEdit')

    def onEdit(self, isCreated):
        '''Clean cache for "Products.MeetingLiege.vocabularies.groupsofmattervocabulary",
           no matter category is created or edited.'''
        cleanVocabularyCacheFor("Products.MeetingLiege.vocabularies.groupsofmattervocabulary")


class CustomToolPloneMeeting(ToolPloneMeeting):
    '''Adapter that adapts portal_plonemeeting.'''

    implements(IToolPloneMeetingCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    security.declarePublic('isFinancialUser')

    def isFinancialUser(self):
        '''Is current user a financial user, so in groups 'financialcontrollers',
           'financialreviewers' or 'financialmanagers'.'''
        tool = api.portal.get_tool('portal_plonemeeting')
        for groupId in tool.get_plone_groups_for_user():
            for suffix in FINANCE_GROUP_SUFFIXES:
                if groupId.endswith('_%s' % suffix):
                    return True
        return False
    ToolPloneMeeting.isFinancialUser = isFinancialUser

    def financialGroupUids_cachekey(method, self):
        '''cachekey method for self.financialGroupUids.'''
        return get_registry_organizations()

    @ram.cache(financialGroupUids_cachekey)
    def financialGroupUids(self):
        """ """
        res = []
        for org_id in FINANCE_GROUP_IDS:
            try:
                org_uid = org_id_to_uid(org_id)
            except KeyError:
                continue
            res.append(org_uid)
        return res
    ToolPloneMeeting.financialGroupUids = financialGroupUids

    security.declarePublic('isUrbanismUser')

    def isUrbanismUser(self):
        '''
        Is current user an urbanism user, so in groups 'urba-gestion-administrative',
        urba-affaires-ga-c-na-c-rales', 'urba-service-de-lurbanisme',
        'urbanisme-et-ama-c-nagement-du-territoire',
        'echevinat-de-la-culture-et-de-lurbanisme' or 'urba'
        '''
        userGroups = set([gr.getId() for gr in self.context.get_orgs_for_user()])
        allowedGroups = set(['urba-gestion-administrative',
                             'urba-affaires-ga-c-na-c-rales',
                             'urba-service-de-lurbanisme',
                             'urbanisme-et-ama-c-nagement-du-territoire',
                             'echevinat-de-la-culture-et-de-lurbanisme',
                             'urba'])
        if userGroups.intersection(allowedGroups):
            return True
        return False


class MeetingCollegeLiegeWorkflowActions(MeetingWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingCollegeWorkflowActions'''

    implements(IMeetingCollegeLiegeWorkflowActions)
    security = ClassSecurityInfo()


class MeetingCollegeLiegeWorkflowConditions(MeetingWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingCollegeWorkflowConditions'''

    implements(IMeetingCollegeLiegeWorkflowConditions)
    security = ClassSecurityInfo()

    security.declarePublic('mayDecide')

    def mayDecide(self):
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayCorrect')

    def mayCorrect(self, destinationState=None):
        '''See docstring in interfaces.py'''
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            return True
        return res


class MeetingItemCollegeLiegeWorkflowActions(MeetingItemWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCollegeWorkflowActions'''

    implements(IMeetingItemCollegeLiegeWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doAskAdvicesByItemCreator')

    def doAskAdvicesByItemCreator(self, stateChange):
        pass

    security.declarePrivate('doProposeToAdministrativeReviewer')

    def doProposeToAdministrativeReviewer(self, stateChange):
        ''' '''
        pass

    security.declarePrivate('doProposeToInternalReviewer')

    def doProposeToInternalReviewer(self, stateChange):
        ''' '''
        pass

    security.declarePrivate('doAskAdvicesByInternalReviewer')

    def doAskAdvicesByInternalReviewer(self, stateChange):
        pass

    security.declarePrivate('doProposeToDirector')

    def doProposeToDirector(self, stateChange):
        pass

    security.declarePrivate('doProposeToFinance')

    def doProposeToFinance(self, stateChange):
        '''When an item is proposed to finance again, make sure the item
           completeness si no more in ('completeness_complete', 'completeness_evaluation_not_required')
           so advice is not addable/editable when item come back again to the finance.'''
        # if we found an event 'proposeToFinance' in workflow_history, it means that item is
        # proposed again to the finances and we need to ask completeness evaluation again
        # current transition 'proposeToFinance' is already in workflow_history...
        wfTool = api.portal.get_tool('portal_workflow')
        # take history but leave last event apart
        history = self.context.workflow_history[wfTool.getWorkflowsFor(self.context)[0].getId()][:-1]
        # if we find 'proposeToFinance' in previous actions, then item is proposed to finance again
        for event in history:
            if event['action'] == 'proposeToFinance':
                changeCompleteness = self.context.restrictedTraverse('@@change-item-completeness')
                comment = translate('completeness_asked_again_by_app',
                                    domain='PloneMeeting',
                                    context=self.context.REQUEST)
                # change completeness even if current user is not able to set it to
                # 'completeness_evaluation_asked_again', here it is the application that set
                # it automatically
                changeCompleteness._changeCompleteness('completeness_evaluation_asked_again',
                                                       bypassSecurityCheck=True,
                                                       comment=comment)
                break

    security.declarePrivate('doSendToCouncilEmergency')

    def doSendToCouncilEmergency(self, stateChange):
        ''' '''
        pass

    security.declarePrivate('doPre_accept')

    def doPre_accept(self, stateChange):
        pass

    security.declarePrivate('doAccept_but_modify')

    def doAccept_but_modify(self, stateChange):
        pass

    security.declarePrivate('doMark_not_applicable')

    def doMark_not_applicable(self, stateChange):
        """ """
        self._deleteLinkedCouncilItem()

    security.declarePrivate('doRefuse')

    def doRefuse(self, stateChange):
        """ """
        # call original action
        super(MeetingItemCollegeLiegeWorkflowActions, self).doRefuse(stateChange)
        self._deleteLinkedCouncilItem()

    security.declarePrivate('doAccept_and_return')

    def doAccept_and_return(self, stateChange):
        self._returnCollege('accept_and_return')

    security.declarePrivate('doReturn')

    def doReturn(self, stateChange):
        '''
          When the item is 'returned', it will be automatically
          duplicated then validated for a next meeting.
        '''
        self._returnCollege('return')

    def _returnCollege(self, cloneEventAction):
        '''
          Manage 'return college', item is duplicated
          then validated for a next meeting.
        '''
        if cloneEventAction == 'return':
            self._deleteLinkedCouncilItem()

        newOwnerId = self.context.Creator()
        newItem = self.context.clone(newOwnerId=newOwnerId,
                                     cloneEventAction=cloneEventAction,
                                     keepProposingGroup=True,
                                     setCurrentAsPredecessor=True)
        # now that the item is cloned, we need to validate it
        # so it is immediately available for a next meeting
        # we will also set back correct proposingGroup if it was changed
        # we do not pass p_keepProposingGroup to clone() here above
        # because we need to validate the newItem and if we change the proposingGroup
        # maybe we could not...  So validate then set correct proposingGroup...
        wfTool = api.portal.get_tool('portal_workflow')
        self.context.REQUEST.set('mayValidate', True)
        wfTool.doActionFor(newItem, 'validate')
        self.context.REQUEST.set('mayValidate', False)

    def _deleteLinkedCouncilItem(self):
        """When a College item is delayed or returned, we need
           to delete the Council item that was already sent to Council."""
        councilItem = self.context.getItemClonedToOtherMC('meeting-config-council')
        if councilItem:
            # Make sure item is removed because MeetingManagers may not remove items...
            unrestrictedRemoveGivenObject(councilItem)
            plone_utils = api.portal.get_tool('plone_utils')
            plone_utils.addPortalMessage(_("The item that was sent to Council has been deleted."),
                                         type='warning')

    security.declarePrivate('doDelay')

    def doDelay(self, stateChange):
        '''When a College item is delayed, if it was sent to Council, delete
           the item in the Council.'''
        # call original action
        super(MeetingItemCollegeLiegeWorkflowActions, self).doDelay(stateChange)
        self._deleteLinkedCouncilItem()


class MeetingItemCollegeLiegeWorkflowConditions(MeetingItemWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCollegeWorkflowConditions'''

    implements(IMeetingItemCollegeLiegeWorkflowConditions)
    security = ClassSecurityInfo()

    security.declarePublic('mayProposeToAdministrativeReviewer')

    def mayProposeToAdministrativeReviewer(self):
        res = False
        item_state = self.context.queryState()
        member = api.user.get_current()
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
            # MeetingManager must be able to propose to administrative
            # reviewer.
            if self.tool.isManager(self.context):
                return True
            isReviewer = member.has_role('MeetingReviewer', self.context)
            isInternalReviewer = member.has_role('MeetingInternalReviewer', self.context)
            isAdminReviewer = member.has_role('MeetingAdminReviewer', self.context)
            # Item in creation, or in creation waiting for advice can only
            # be sent to administrative reviewer by creators.
            if item_state in ['itemcreated', 'itemcreated_waiting_advices'] and \
               (isReviewer or isInternalReviewer or isAdminReviewer):
                res = False
            # If there is no administrative reviewer, do not show the
            # transition.
            if not self._groupIsNotEmpty('administrativereviewers'):
                res = False
            if not self.context.getCategory() and res:
                return No(_('required_category_ko'))
        return res

    security.declarePublic('mayProposeToInternalReviewer')

    def mayProposeToInternalReviewer(self):
        res = False
        item_state = self.context.queryState()
        member = api.user.get_current()
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
            # MeetingManager must be able to propose to internal reviewer.
            if self.tool.isManager(self.context):
                return True
            # Only administrative reviewers might propose to internal reviewer,
            # but creators can do it too if there is no administrative
            # reviewer.
            isAdminReviewer = member.has_role('MeetingAdminReviewer', self.context)
            if not isAdminReviewer:
                aRNotEmpty = self._groupIsNotEmpty('administrativereviewers')
                if item_state in ['itemcreated', 'itemcreated_waiting_advices'] and\
                   aRNotEmpty:
                    res = False
            # If there is no internal reviewer or if the current user
            # is internal reviewer or director, do not show the transition.
            isReviewer = member.has_role('MeetingReviewer', self.context)
            isInternalReviewer = member.has_role('MeetingInternalReviewer', self.context)
            iRNotEmpty = self._groupIsNotEmpty('internalreviewers')
            if not iRNotEmpty or isReviewer or isInternalReviewer:
                res = False
            if not self.context.getCategory() and res:
                return No(_('required_category_ko'))
        return res

    security.declarePublic('mayProposeToDirector')

    def mayProposeToDirector(self):
        '''
        An item can be proposed directly from any state to director
        by an internal reviewer or a director.
        It's also possible, when there are no administrative and internal
        reviewers, to send item from creation to direction, even
        if the user is only a creator.
        The same shortcut exists from "proposed to administrative reviewer"
        to "proposed to director" if there is no internal reviewer.
        '''
        res = False
        item_state = self.context.queryState()
        member = api.user.get_current()
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
            # MeetingManager must be able to propose to director.
            if self.tool.isManager(self.context):
                return True
            isReviewer = member.has_role('MeetingReviewer', self.context)
            isInternalReviewer = member.has_role('MeetingInternalReviewer', self.context)
            # Director and internal reviewer can propose items to director in
            # any state.
            if not (isReviewer or isInternalReviewer):
                aRNotEmpty = self._groupIsNotEmpty('administrativereviewers')
                iRNotEmpty = self._groupIsNotEmpty('internalreviewers')
                isAdminReviewer = member.has_role('MeetingAdminReviewer', self.context)

                # An administrative reviewer can propose to director if there
                # is no internal reviewer and a creator can do it too if there
                # is neither administrative nor internal reviewers.
                if item_state in ['itemcreated', 'itemcreated_waiting_advices']:
                    if (aRNotEmpty or iRNotEmpty) and \
                       (iRNotEmpty or not isAdminReviewer):
                        res = False
                # Else if the item is proposed to administrative reviewer and
                # there is no internal reviewer in the group, an administrative
                # reviewer can also send the item to director.
                elif item_state == 'proposed_to_administrative_reviewer' and \
                        (not isAdminReviewer or iRNotEmpty):
                    res = False
            if not self.context.getCategory() and res:
                return No(_('required_category_ko'))
        return res

    security.declarePublic('mayProposeToFinance')

    def mayProposeToFinance(self):
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            # check if one of the finance group needs to give advice on
            # the item, if it is the case, the item must go to finance before being validated
            if self.context.adapted().getFinanceGroupUIDForItem():
                return True
        return res

    def _hasAdvicesToGive(self, destination_state):
        """ """
        # check if aksed advices are giveable in state 'proposed_to_internal_reviewer_waiting_advices'
        cfg = self.tool.getMeetingConfig(self.context)
        hasAdvicesToGive = False
        for org_uid, adviceInfo in self.context.adviceIndex.items():
            # only consider advices to give
            if adviceInfo['type'] not in (NOT_GIVEN_ADVICE_VALUE, 'asked_again', ):
                continue
            org = get_organization(org_uid)
            adviceStates = org.get_item_advice_states(cfg)
            if destination_state in adviceStates:
                hasAdvicesToGive = True
                break
        return hasAdvicesToGive

    def _mayAskAdvices(self, item_state):
        """ """
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            # check if asked advices are giveable in state item_state
            hasAdvicesToGive = self._hasAdvicesToGive(item_state)

            if hasAdvicesToGive:
                res = True
                if not self.context.getCategory():
                    return No(_('required_category_ko'))
            else:
                # return a 'No' instance explaining that no askable advice is selected on this item
                res = No(_('advice_required_to_ask_advices'))
        return res

    security.declarePublic('mayAskAdvicesByItemCreator')

    def mayAskAdvicesByItemCreator(self):
        '''May advices be asked by item creator.'''
        return self._mayAskAdvices('itemcreated_waiting_advices')

    security.declarePublic('mayAskAdvicesByInternalReviewer')

    def mayAskAdvicesByInternalReviewer(self):
        '''May advices be asked by internal reviewer.'''
        res = self._mayAskAdvices('proposed_to_internal_reviewer_waiting_advices')
        if res:
            # double check that current user isInternalReviewer as this
            # transition may be triggered from the 'itemcreated' state
            member = api.user.get_current()
            isInternalReviewer = member.has_role('MeetingInternalReviewer', self.context)
            if not isInternalReviewer and not self.tool.isManager(self.context):
                res = False
        return res

    security.declarePublic('mayValidate')

    def mayValidate(self):
        """
          This differs if the item needs finance advice or not.
          - it does NOT have finance advice : either the Director or the MeetingManager
            can validate, the MeetingManager can bypass the validation process
            and validate an item that is in the state 'itemcreated';
          - it does have a finance advice : it will be automatically validated when
            the advice will be 'signed' by the finance group if the advice type
            is 'positive_finance/positive_with_remarks_finance' or 'not_required_finance' or it can be manually
            validated by the director if item emergency has been asked and motivated on the item.
        """
        res = False
        # very special case, we can bypass the guard if a 'mayValidate'
        # value is found to True in the REQUEST
        if self.context.REQUEST.get('mayValidate', False):
            return True
        # first of all, the use must have the 'Review portal content permission'
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
            item_state = self.context.queryState()
            finance_advice = self.context.adapted().getFinanceGroupUIDForItem()
            # if the current item state is 'itemcreated', only the MeetingManager can validate
            if item_state == 'itemcreated' and not self.tool.isManager(self.context):
                res = False
            # special case for item having finance advice that was still under redaction when delay timed out
            # a MeetingManager mut be able to validate it
            elif item_state in ['proposed_to_finance', 'proposed_to_director', ] and \
                    finance_advice and self.context._adviceDelayIsTimedOut(finance_advice):
                res = True
            # director may validate an item if no finance advice
            # or finance advice and emergency is asked
            elif item_state == 'proposed_to_director' and \
                    finance_advice and \
                    self.context.getEmergency() == 'no_emergency':
                res = False
            # special case for item being validable when emergency is asked on it
            elif item_state == 'proposed_to_finance' and self.context.getEmergency() == 'no_emergency':
                res = False

            if res and not self.context.getCategory():
                return No(_('required_category_ko'))
        return res

    security.declarePublic('maySendToCouncilEmergency')

    def maySendToCouncilEmergency(self):
        '''Sendable to Council without being in a meeting for MeetingManagers,
           and if emergency was asked for sending item to Council.'''
        res = False
        if _checkPermission(ReviewPortalContent, self.context) and \
           'meeting-config-council' in self.context.getOtherMeetingConfigsClonableToEmergency():
            res = True
        return res

    security.declarePublic('mayDecide')

    def mayDecide(self):
        '''We may decide an item if the linked meeting is in relevant state.'''
        res = False
        meeting = self.context.getMeeting()
        if _checkPermission(ReviewPortalContent, self.context) and \
           meeting and (meeting.queryState() in ['decided', 'closed', ]):
            res = True
        return res

    security.declarePublic('mayAcceptAndReturn')

    def mayAcceptAndReturn(self):
        ''' '''
        return self.mayDecide()

    security.declarePublic('mayCorrect')

    def mayCorrect(self, destinationState=None):
        '''See docstring in interfaces.py'''
        res = super(MeetingItemCollegeLiegeWorkflowConditions, self).mayCorrect(destinationState)
        return res

    security.declarePublic('mayBackToProposedToDirector')

    def mayBackToProposedToDirector(self):
        '''
          Item may back to proposedToDirector if a value 'mayBackToProposedToDirector' is
          found and True in the REQUEST.  It means that the item is 'proposed_to_finance' and that the
          freshly signed advice was negative.
          It is also the case for MeetingItemBourgmestre if 'everyAdvicesAreGiven' found and True in the REQUEST.
          If the item is 'validated', a MeetingManager can send it back to the director.
        '''
        res = False
        # special case when automatically sending back an item to 'proposed_to_director'
        # when every advices are given (coming from waiting_advices)
        if (self.context.REQUEST.get('everyAdvicesAreGiven', False) and
            self.context.queryState() == 'proposed_to_director_waiting_advices') or \
           self.context.REQUEST.get('mayBackToProposedToDirector', False) or \
           _checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayBackToItemCreated')

    def mayBackToItemCreated(self):
        '''
            A proposedToDirector item may be directly sent back to the
            'itemCreated' state if the user is reviewer and there are no
            administrative or internal reviewers.
        '''
        res = False
        item_state = self.context.queryState()
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
            # A director can directly send back to creation an item which is
            # proposed to director if there are neither administrative nor
            # internal reviewers.
            if item_state == 'proposed_to_director' and \
                    (self._groupIsNotEmpty('administrativereviewers') or
                     self._groupIsNotEmpty('internalreviewers')):
                res = False
            # An internal reviewer can send back to creation if there is
            # no administrative reviewer.
            elif item_state == 'proposed_to_internal_reviewer' and \
                    self._groupIsNotEmpty('administrativereviewers'):
                res = False
        # special case when automatically sending back an item to 'itemcreated' or
        # 'proposed_to_internal_reviewer' when every advices are given (coming from waiting_advices)
        elif self.context.REQUEST.get('everyAdvicesAreGiven', False) and \
                self.context.queryState() == 'itemcreated_waiting_advices':
            res = True
        return res

    security.declarePublic('mayBackToProposedToAdministrativeReviewer')

    def mayBackToProposedToAdministrativeReviewer(self):
        '''
            An item can be sent back to administrative reviewer if it is
            proposed to internal reviewer or if it is proposed to director
            and there is no internal reviewer. The transition is only
            available if there is an administrative reviewer.
        '''
        res = False
        item_state = self.context.queryState()
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
            # do not show the transition if there is no administrative reviewer
            # or if the item is proposed to director and there is an internal
            # reviewer.
            if (item_state == 'proposed_to_director' and
                self._groupIsNotEmpty('internalreviewers')) or \
               not self._groupIsNotEmpty('administrativereviewers'):
                res = False
        return res

    security.declarePublic('mayBackToProposedToInternalReviewer')

    def mayBackToProposedToInternalReviewer(self):
        '''
            An item can be sent back to internal reviewer if it is
            proposed to director. The transition is only available
            if there is an internal reviewer.
        '''
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
            if not self._groupIsNotEmpty('internalreviewers'):
                res = False
        # special case for financial controller that can send an item back to
        # the internal reviewer if it is in state 'proposed_to_finance' and
        # item is incomplete
        elif self.context.queryState() == 'proposed_to_finance':
            # user must be a member of the finance group the advice is asked to
            financeGroupId = self.context.adapted().getFinanceGroupUIDForItem()
            tool = api.portal.get_tool('portal_plonemeeting')
            memberGroups = tool.get_plone_groups_for_user()
            for suffix in FINANCE_GROUP_SUFFIXES:
                financeSubGroupId = '%s_%s' % (financeGroupId, suffix)
                if financeSubGroupId in memberGroups:
                    res = True
                    break
        # special case when automatically sending back an item to 'proposed_to_internal_reviewer'
        # when every advices are given (coming from waiting_advices)
        elif self.context.REQUEST.get('everyAdvicesAreGiven', False) and \
                self.context.queryState() == 'proposed_to_internal_reviewer_waiting_advices':
            return True
        return res


class MeetingCouncilLiegeWorkflowActions(MeetingWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingCouncilWorkflowActions'''

    implements(IMeetingCouncilLiegeWorkflowActions)
    security = ClassSecurityInfo()


class MeetingCouncilLiegeWorkflowConditions(MeetingWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingCouncilWorkflowConditions'''

    implements(IMeetingCouncilLiegeWorkflowConditions)
    security = ClassSecurityInfo()

    security.declarePublic('mayDecide')

    def mayDecide(self):
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayCorrect')

    def mayCorrect(self, destinationState=None):
        '''See docstring in interfaces.py'''
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            return True
        return res


class MeetingItemCouncilLiegeWorkflowActions(MeetingItemWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCouncilWorkflowActions'''

    implements(IMeetingItemCouncilLiegeWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doAccept_pre_accept')

    def doAccept_pre_accept(self, stateChange):
        pass

    security.declarePrivate('doAccept_but_modify')

    def doAccept_but_modify(self, stateChange):
        pass

    security.declarePrivate('doDelay')

    def doDelay(self, stateChange):
        '''When an item is delayed, it is sent back to the College, so activate
           the fact that this item has to be sent to the College.'''
        # specify that item must be sent to the College, the configuration will do the job
        # as 'delayed' state is in MeetingConfig.itemAutoSentToOtherMCStates
        self.context.setOtherMeetingConfigsClonableTo(('meeting-config-college', ))

    def doReturn(self, stateChange):
        '''
          When the item is 'returned', it will be automatically
          sent back to the College in state 'validated'.
          Activate the fact that it must be sent to the College so it it sent.
        '''
        self.context.setOtherMeetingConfigsClonableTo(('meeting-config-college', ))

    security.declarePrivate('doMark_not_applicable')

    def doMark_not_applicable(self, stateChange):
        ''' '''
        pass


class MeetingItemCouncilLiegeWorkflowConditions(MeetingItemWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCouncilWorkflowConditions'''

    implements(IMeetingItemCouncilLiegeWorkflowConditions)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item  # Implements IMeetingItem

    security.declarePublic('mayCorrect')

    def mayCorrect(self, destinationState=None):
        '''See docstring in interfaces.py'''
        res = super(MeetingItemCouncilLiegeWorkflowConditions, self).mayCorrect(destinationState)
        return res

    security.declarePublic('mayDecide')

    def mayDecide(self):
        '''We may decide an item if the linked meeting is in relevant state.'''
        res = False
        meeting = self.context.getMeeting()
        if _checkPermission(ReviewPortalContent, self.context) and \
           meeting and (meeting.queryState() in ['decided', 'closed', ]):
            res = True
        return res


class MeetingBourgmestreWorkflowActions(MeetingWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingBourgmestreWorkflowActions'''

    implements(IMeetingBourgmestreWorkflowActions)
    security = ClassSecurityInfo()


class MeetingBourgmestreWorkflowConditions(MeetingWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingBourgmestreWorkflowConditions'''

    implements(IMeetingBourgmestreWorkflowConditions)
    security = ClassSecurityInfo()


class MeetingItemBourgmestreWorkflowActions(MeetingItemWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemBourgmestreWorkflowActions'''

    implements(IMeetingItemBourgmestreWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doProposeToAdministrativeReviewer')

    def doProposeToAdministrativeReviewer(self, stateChange):
        ''' '''
        pass

    security.declarePrivate('doProposeToInternalReviewer')

    def doProposeToInternalReviewer(self, stateChange):
        ''' '''
        pass

    security.declarePrivate('doAskAdvicesByInternalReviewer')

    def doAskAdvicesByInternalReviewer(self, stateChange):
        pass

    security.declarePrivate('doProposeToDirector')

    def doProposeToDirector(self, stateChange):
        pass

    security.declarePrivate('doAskAdvicesByDirector')

    def doAskAdvicesByDirector(self, stateChange):
        pass

    security.declarePrivate('doProposeToGeneralManager')

    def doProposeToGeneralManager(self, stateChange):
        pass

    security.declarePrivate('doProposeToCabinetManager')

    def doProposeToCabinetManager(self, stateChange):
        pass

    security.declarePrivate('doProposeToCabinetReviewer')

    def doProposeToCabinetReviewer(self, stateChange):
        pass

    security.declarePrivate('doMark_not_applicable')

    def doMark_not_applicable(self, stateChange):
        """ """
        pass

    security.declarePrivate('doRefuse')

    def doRefuse(self, stateChange):
        """ """
        pass

    security.declarePrivate('doDelay')

    def doDelay(self, stateChange):
        '''When a Bourgmestre item is delayed, it is duplicated in initial_state.'''
        # take original behavior, aka duplicate in it's initial_state
        super(MeetingItemBourgmestreWorkflowActions, self).doDelay(stateChange)


class MeetingItemBourgmestreWorkflowConditions(MeetingItemCollegeLiegeWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemBourgmestreWorkflowConditions'''

    implements(IMeetingItemBourgmestreWorkflowConditions)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item  # Implements IMeetingItem

    security.declarePublic('mayProposeToGeneralManager')

    def mayProposeToGeneralManager(self):
        ''' '''
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayProposeToCabinetManager')

    def mayProposeToCabinetManager(self):
        ''' '''
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayProposeToCabinetReviewer')

    def mayProposeToCabinetReviewer(self):
        ''' '''
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
            # if item is itemcreated, only Cabinet Manager may propose to cabinet reviewer directly
            if self.context.queryState() == 'itemcreated' and not self.context.adapted().is_cabinet_manager():
                res = False
        return res

    security.declarePublic('mayAskAdvicesByDirector')

    def mayAskAdvicesByDirector(self):
        ''' '''
        return self._mayAskAdvices('proposed_to_director_waiting_advices')

    security.declarePublic('mayDecide')

    def mayDecide(self):
        ''' '''
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
        return res


old_get_advice_given_on = MeetingAdvice.get_advice_given_on


def get_advice_given_on(self):
    '''Monkeypatch the meetingadvice.get_advice_given_on method, if it is
       a finance advice, we will return date of last transition 'sign_advice'.'''
    tool = api.portal.get_tool('portal_plonemeeting')
    financial_group_uids = tool.financialGroupUids()
    if self.advice_group in financial_group_uids:
        lastEvent = getLastWFAction(self, 'signFinancialAdvice')
        if not lastEvent:
            return self.modified()
        else:
            return lastEvent['time']
    else:
        return old_get_advice_given_on(self)
MeetingAdvice.get_advice_given_on = get_advice_given_on

# ------------------------------------------------------------------------------
InitializeClass(CustomMeeting)
InitializeClass(CustomMeetingCategory)
InitializeClass(CustomMeetingConfig)
InitializeClass(CustomMeetingItem)
InitializeClass(CustomToolPloneMeeting)
InitializeClass(MeetingBourgmestreWorkflowActions)
InitializeClass(MeetingBourgmestreWorkflowConditions)
InitializeClass(MeetingItemBourgmestreWorkflowActions)
InitializeClass(MeetingItemBourgmestreWorkflowConditions)
InitializeClass(MeetingCollegeLiegeWorkflowActions)
InitializeClass(MeetingCollegeLiegeWorkflowConditions)
InitializeClass(MeetingItemCollegeLiegeWorkflowActions)
InitializeClass(MeetingItemCollegeLiegeWorkflowConditions)
InitializeClass(MeetingCouncilLiegeWorkflowActions)
InitializeClass(MeetingCouncilLiegeWorkflowConditions)
InitializeClass(MeetingItemCouncilLiegeWorkflowActions)
InitializeClass(MeetingItemCouncilLiegeWorkflowConditions)
# ------------------------------------------------------------------------------


class ItemsToControlCompletenessOfAdapter(CompoundCriterionBaseAdapter):

    @property
    def query(self):
        '''Queries all items for which there is completeness to evaluate, so where completeness
           is not 'completeness_complete'.'''
        groupIds = []
        tool = api.portal.get_tool('portal_plonemeeting')
        userGroups = tool.get_plone_groups_for_user()
        financial_group_uids = tool.financialGroupUids()
        for financeGroup in financial_group_uids:
            # only keep finance groupIds the current user is controller for
            if '%s_financialcontrollers' % financeGroup in userGroups:
                # advice not given yet
                groupIds.append('delay__%s_advice_not_giveable' % financeGroup)
                # advice was already given once and come back to the finance
                groupIds.append('delay__%s_proposed_to_financial_controller' % financeGroup)
        return {'portal_type': {'query': self.cfg.getItemTypeName()},
                'getCompleteness': {'query': ('completeness_not_yet_evaluated',
                                              'completeness_incomplete',
                                              'completeness_evaluation_asked_again')},
                'indexAdvisers': {'query': groupIds},
                'review_state': {'query': 'proposed_to_finance'}}


class ItemsWithAdviceProposedToFinancialControllerAdapter(CompoundCriterionBaseAdapter):

    @property
    def query(self):
        '''Queries all items for which there is an advice in state 'proposed_to_financial_controller'.
           We only return items for which completeness has been evaluated to 'complete'.'''
        groupIds = []
        tool = api.portal.get_tool('portal_plonemeeting')
        userGroups = tool.get_plone_groups_for_user()
        financial_group_uids = tool.financialGroupUids()
        for financeGroup in financial_group_uids:
            # only keep finance groupIds the current user is controller for
            if '%s_financialcontrollers' % financeGroup in userGroups:
                groupIds.append('delay__%s_proposed_to_financial_controller' % financeGroup)
        # Create query parameters
        return {'portal_type': {'query': self.cfg.getItemTypeName()},
                'getCompleteness': {'query': 'completeness_complete'},
                'indexAdvisers': {'query': groupIds}}


class ItemsWithAdviceProposedToFinancialReviewerAdapter(CompoundCriterionBaseAdapter):

    @property
    def query(self):
        '''Queries all items for which there is an advice in state 'proposed_to_financial_reviewer'.'''
        groupIds = []
        tool = api.portal.get_tool('portal_plonemeeting')
        userGroups = tool.get_plone_groups_for_user()
        financial_group_uids = tool.financialGroupUids()
        for financeGroup in financial_group_uids:
            # only keep finance groupIds the current user is reviewer for
            if '%s_financialreviewers' % financeGroup in userGroups:
                groupIds.append('delay__%s_proposed_to_financial_reviewer' % financeGroup)
        return {'portal_type': {'query': self.cfg.getItemTypeName()},
                'indexAdvisers': {'query': groupIds}}


class ItemsWithAdviceProposedToFinancialManagerAdapter(CompoundCriterionBaseAdapter):

    @property
    def query(self):
        '''Queries all items for which there is an advice in state 'proposed_to_financial_manager'.'''
        groupIds = []
        tool = api.portal.get_tool('portal_plonemeeting')
        userGroups = tool.get_plone_groups_for_user()
        financial_group_uids = tool.financialGroupUids()
        for financeGroup in financial_group_uids:
            # only keep finance groupIds the current user is manager for
            if '%s_financialmanagers' % financeGroup in userGroups:
                groupIds.append('delay__%s_proposed_to_financial_manager' % financeGroup)
        return {'portal_type': {'query': self.cfg.getItemTypeName()},
                'indexAdvisers': {'query': groupIds}}


class MLItemPrettyLinkAdapter(ItemPrettyLinkAdapter):
    """
      Override to take into account MeetingLiege use cases...
    """

    def _leadingIcons(self):
        """
          Manage icons to display before the icons managed by PrettyLink._icons.
        """
        # Default PM item icons
        icons = super(MLItemPrettyLinkAdapter, self)._leadingIcons()

        if self.context.isDefinedInTool():
            return icons

        itemState = self.context.queryState()
        # Add our icons for some review states
        if itemState == 'accepted_and_returned':
            icons.append(('accepted_and_returned.png',
                          translate('icon_help_accepted_and_returned',
                                    domain="PloneMeeting",
                                    context=self.request)))
        elif itemState == 'returned':
            icons.append(('returned.png',
                          translate('icon_help_returned',
                                    domain="PloneMeeting",
                                    context=self.request)))
        elif itemState == 'proposed_to_administrative_reviewer':
            icons.append(('proposeToAdministrativeReviewer.png',
                          translate('icon_help_proposed_to_administrative_reviewer',
                                    domain="PloneMeeting",
                                    context=self.request)))
        elif itemState == 'proposed_to_internal_reviewer':
            icons.append(('proposeToInternalReviewer.png',
                          translate('icon_help_proposed_to_internal_reviewer',
                                    domain="PloneMeeting",
                                    context=self.request)))
        elif itemState == 'proposed_to_internal_reviewer_waiting_advices':
            icons.append(('askAdvicesByInternalReviewer.png',
                          translate('icon_help_proposed_to_internal_reviewer_waiting_advices',
                                    domain="PloneMeeting",
                                    context=self.request)))
        elif itemState == 'proposed_to_director':
            icons.append(('proposeToDirector.png',
                          translate('icon_help_proposed_to_director',
                                    domain="PloneMeeting",
                                    context=self.request)))
        elif itemState == 'proposed_to_director_waiting_advices':
            icons.append(('askAdvicesByDirector.png',
                          translate('icon_help_proposed_to_director_waiting_advices',
                                    domain="PloneMeeting",
                                    context=self.request)))
        elif itemState == 'proposed_to_finance':
            icons.append(('proposeToFinance.png',
                          translate('icon_help_proposed_to_finance',
                                    domain="PloneMeeting",
                                    context=self.request)))
        elif itemState == 'proposed_to_general_manager':
            icons.append(('proposeToGeneralManager.png',
                          translate('icon_help_proposed_to_general_manager',
                                    domain="PloneMeeting",
                                    context=self.request)))
        elif itemState == 'proposed_to_cabinet_manager':
            icons.append(('proposeToCabinetManager.png',
                          translate('icon_help_proposed_to_cabinet_manager',
                                    domain="PloneMeeting",
                                    context=self.request)))
        elif itemState == 'proposed_to_cabinet_reviewer':
            icons.append(('proposeToCabinetReviewer.png',
                          translate('icon_help_proposed_to_cabinet_reviewer',
                                    domain="PloneMeeting",
                                    context=self.request)))

        # add an icon if item is down the workflow from the finances
        # if item was ever gone the the finances and now it is down to the
        # services, then it is considered as down the wf from the finances
        # so take into account every states before 'validated/proposed_to_finance'
        if not self.context.hasMeeting() and itemState not in ['proposed_to_finance', 'validated']:
            wfTool = api.portal.get_tool('portal_workflow')
            itemWF = wfTool.getWorkflowsFor(self.context)[0]
            history = self.context.workflow_history[itemWF.getId()]
            for event in history:
                if event['action'] == 'proposeToFinance':
                    icons.append(('wf_down_finances.png',
                                  translate('icon_help_wf_down_finances',
                                            domain="PloneMeeting",
                                            context=self.request)))
                    break
        return icons


class MLMeetingPrettyLinkAdapter(MeetingPrettyLinkAdapter):
    """
      Override to take into account MeetingLiege use cases...
    """

    def _trailingIcons(self):
        """
          Manage icons to display before the icons managed by PrettyLink._icons.
        """
        # Default PM item icons
        icons = super(MLMeetingPrettyLinkAdapter, self)._trailingIcons()

        if not self.context.portal_type == 'MeetingCollege':
            return icons

        if self.context.getAdoptsNextCouncilAgenda():
            icons.append(('adopts_next_council_agenda.gif',
                          translate('icon_help_adopts_next_council_agenda',
                                    domain="PloneMeeting",
                                    context=self.request)))
        return icons


class MLItemMainInfosHistoryAdapter(BaseImioHistoryAdapter):
    """ """

    history_type = 'main_infos'
    history_attr_name = ITEM_MAIN_INFOS_HISTORY
