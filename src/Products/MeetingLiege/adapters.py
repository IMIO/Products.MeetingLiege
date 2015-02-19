# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
# File: adapters.py
#
# Copyright (c) 2014 by Imio.be
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
import string
import unicodedata
from appy.gen import No
from AccessControl import getSecurityManager, ClassSecurityInfo
from Globals import InitializeClass
from zope.annotation.interfaces import IAnnotations
from zope.component import queryUtility
from zope.interface import implements
from zope.i18n import translate
from zope.schema.interfaces import IVocabularyFactory
from plone.memoize import ram
from Products.CMFCore.permissions import ReviewPortalContent, ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.Archetypes import DisplayList
from Products.PloneMeeting.MeetingItem import MeetingItem, MeetingItemWorkflowConditions, MeetingItemWorkflowActions
from Products.PloneMeeting.config import NOT_GIVEN_ADVICE_VALUE
from Products.PloneMeeting.config import MEETING_GROUP_SUFFIXES
from Products.PloneMeeting.config import READER_USECASES
from Products.PloneMeeting.utils import checkPermission, prepareSearchValue, getLastEvent, cleanRamCacheFor
from Products.PloneMeeting.Meeting import MeetingWorkflowActions, MeetingWorkflowConditions, Meeting
from Products.PloneMeeting.MeetingCategory import MeetingCategory
from Products.PloneMeeting.MeetingConfig import MeetingConfig
from Products.PloneMeeting.MeetingGroup import MeetingGroup
from Products.PloneMeeting.ToolPloneMeeting import ToolPloneMeeting
from Products.PloneMeeting.interfaces import IMeetingCustom, IMeetingItemCustom, \
    IMeetingConfigCustom, IMeetingGroupCustom, IMeetingCategoryCustom, IToolPloneMeetingCustom
from Products.MeetingLiege.interfaces import \
    IMeetingItemCollegeLiegeWorkflowConditions, IMeetingItemCollegeLiegeWorkflowActions,\
    IMeetingCollegeLiegeWorkflowConditions, IMeetingCollegeLiegeWorkflowActions, \
    IMeetingItemCouncilLiegeWorkflowConditions, IMeetingItemCouncilLiegeWorkflowActions,\
    IMeetingCouncilLiegeWorkflowConditions, IMeetingCouncilLiegeWorkflowActions
from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.config import FINANCE_GROUP_SUFFIXES
from Products.MeetingLiege.config import FINANCE_GIVEABLE_ADVICE_STATES

# disable every wfAdaptations but 'return_to_proposing_group'
customWfAdaptations = ('return_to_proposing_group', )
MeetingConfig.wfAdaptations = customWfAdaptations


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
    security.declarePublic('getPrintableItems')

    def getPrintableItems(self, itemUids, late=False, ignore_review_states=[],
                          privacy='*', oralQuestion='both', categories=[],
                          excludedCategories=[], firstNumber=1, renumber=False):
        '''Returns a list of items.
           An extra list of review states to ignore can be defined.
           A privacy can also be given, and the fact that the item is an
           oralQuestion or not (or both).
           Some specific categories can be given or some categories to exchude.
           These 2 parameters are exclusive.  If renumber is True, a list of tuple
           will be returned with first element the number and second element, the item.
           In this case, the firstNumber value can be used.'''
        # We just filter ignore_review_states here and privacy and call
        # getItemsInOrder(uids), passing the correct uids and removing empty
        # uids.
        # privacy can be '*' or 'public' or 'secret'
        # oralQuestion can be 'both' or False or True
        for elt in itemUids:
            if elt == '':
                itemUids.remove(elt)
        #no filtering, returns the items ordered
        if not categories and not ignore_review_states and privacy == '*' and oralQuestion == 'both':
            return self.context.getItemsInOrder(late=late, uids=itemUids)
        # Either, we will have to filter the state here and check privacy
        filteredItemUids = []
        uid_catalog = self.context.uid_catalog
        for itemUid in itemUids:
            obj = uid_catalog(UID=itemUid)[0].getObject()
            if obj.queryState() in ignore_review_states:
                continue
            elif not (privacy == '*' or obj.getPrivacy() == privacy):
                continue
            elif not (oralQuestion == 'both' or obj.getOralQuestion() == oralQuestion):
                continue
            elif categories and not obj.getCategory() in categories:
                continue
            elif excludedCategories and obj.getCategory() in excludedCategories:
                continue
            filteredItemUids.append(itemUid)
        #in case we do not have anything, we return an empty list
        if not filteredItemUids:
            return []
        else:
            items = self.context.getItemsInOrder(late=late, uids=filteredItemUids)
            if renumber:
                #returns a list of tuple with first element the number
                #and second element the item itself
                i = firstNumber
                res = []
                for item in items:
                    res.append((i, item))
                    i = i + 1
                items = res
            return items

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

    def getPrintableItemsByCategory(self, itemUids=[], late=False,
                                    ignore_review_states=[], by_proposing_group=False, group_prefixes={},
                                    privacy='*', oralQuestion='both', toDiscuss='both', categories=[],
                                    excludedCategories=[], groupIds=[], firstNumber=1, renumber=False,
                                    includeEmptyCategories=False, includeEmptyGroups=False, withCollege=False):
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
           In this case, the firstNumber value can be used.'''
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
            if v1[1]<v2[1]:
                return -1
            elif v1[1]>v2[1]:
                return 1
            else:
                return 0
        res = []
        items = []
        previousCatId = None
        tool = getToolByName(self.context, 'portal_plonemeeting')
        # Retrieve the list of items
        for elt in itemUids:
            if elt == '':
                itemUids.remove(elt)
        if late == 'both':
            items = self.context.getItemsInOrder(late=False, uids=itemUids)
            items += self.context.getItemsInOrder(late=True, uids=itemUids)
        else:
            items = self.context.getItemsInOrder(late=late, uids=itemUids)
        if withCollege:
            meetingDate = self.context.getDate()
            tool = getToolByName(self.context, 'portal_plonemeeting')
            cfg = tool.getMeetingConfig(self.context)
            insertMethods = cfg.getInsertingMethodsOnAddItem()
            catalog = getToolByName(self.context, 'portal_catalog')
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
            collegeItems = collegeMeeting.getItemsInOrder()
            itemList = []
            for collegeItem in collegeItems:
                if 'meeting-config-council' in collegeItem.getOtherMeetingConfigsClonableTo() and not\
                                collegeItem._checkAlreadyClonedToOtherMC('meeting-config-council'):
                    itemPrivacy=collegeItem.getPrivacyForCouncil()
                    itemProposingGroup=collegeItem.getProposingGroup()
                    councilCategoryId = collegeItem.getCategory(theObject=True).getCategoryMappingsWhenCloningToOtherMC()
                    itemCategory = getattr(tool.getMeetingConfig(self.context).categories, councilCategoryId[0].split('.')[1])
                    meeting = self.context.getSelf()
                    parent = meeting.aq_inner.aq_parent
                    parent._v_tempItem = MeetingItem('')
                    parent._v_tempItem.setPrivacy(itemPrivacy)
                    parent._v_tempItem.setProposingGroup(itemProposingGroup)
                    parent._v_tempItem.setCategory(itemCategory.getId())
                    itemOrder = parent._v_tempItem.adapted().getInsertOrder(insertMethods)
                    itemList.append((collegeItem, itemOrder))
                    delattr(parent, '_v_tempItem')
            councilItems = self.context.getItemsInOrder(uids=itemUids)
            for councilItem in councilItems:
                itemOrder = councilItem.adapted().getInsertOrder(insertMethods)
                itemList.append((councilItem, itemOrder))

            itemList.sort(cmp=_comp)
            items = [i[0] for i in itemList]
        if by_proposing_group:
            groups = tool.getMeetingGroups()
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
                                          (item.portal_type=='MeetingItemCollege' and item.getPrivacyForCouncil() == privacy) or
                                          (item.portal_type=='MeetingItemCouncil' and item.getPrivacy() == privacy)):
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
                currentItemMeetingConfig = tool.getMeetingConfig(item)
                if not withCollege or item.portal_type == 'MeetingItemCouncil':
                    currentCat = item.getCategory(theObject=True)
                else:
                    councilCategoryId = item.getCategory(theObject=True).getCategoryMappingsWhenCloningToOtherMC()
                    currentCat = getattr(tool.getMeetingConfig(self.context).categories, councilCategoryId[0].split('.')[1])
                # Add the item to a new category, excepted if the
                # category already exists.
                catExists = False
                for catList in res:
                    if catList[0] == currentCat:
                        catExists = True
                        break
                if catExists:
                    self._insertItemInCategory(catList, item,
                                                by_proposing_group, group_prefixes, groups)
                else:
                    res.append([currentCat])
                    self._insertItemInCategory(res[-1], item,
                                                by_proposing_group, group_prefixes, groups)
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
        if renumber:
            # return a list of tuple with first element the number and second
            # element the item itself
            final_res = []
            item_num = firstNumber-1
            for elts in res:
                final_items = []
                # we received a list of tuple (cat, items_list)
                for item in elts[1:]:
                    if withCollege:
                        item_num = item_num + 1
                    else:
                        item_num = self.context.getItemNumsForActe()[item.UID()]
                    final_items.append((item_num, item))
                final_res.append([elts[0], final_items])
            res = final_res
        return res

    security.declarePublic('getItemsForAM')
    def getItemsForAM(self, itemUids=[], late=False,
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
        tool = getToolByName(self.context, 'portal_plonemeeting')
        cfg = tool.getMeetingConfig(self.context)
        for category in cfg.getCategories(onlySelectable=False):
            lst.append(self.getPrintableItemsByCategory(itemUids=itemUids, late=late,
                                                        ignore_review_states=ignore_review_states,
                                                        by_proposing_group=by_proposing_group,
                                                        group_prefixes=group_prefixes,
                                                        privacy=privacy, oralQuestion=oralQuestion,
                                                        toDiscuss=toDiscuss, categories=[category.getId(), ],
                                                        excludedCategories=excludedCategories,
                                                        firstNumber=firstNumber, renumber=renumber,
                                                        includeEmptyCategories=includeEmptyCategories,
                                                        includeEmptyGroups=includeEmptyGroups))
            #we can find department in description
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
        '''Create a dict that store item number regarding the used category.'''
        # for "normal" items, the item number depends on the used category
        # store this in an annotation on the meeting, we only recompte it if meeting was modified
        ann = IAnnotations(self)
        if not 'MeetingLiege-getItemNumsForActe' in ann:
            ann['MeetingLiege-getItemNumsForActe'] = {}
        itemNums = ann['MeetingLiege-getItemNumsForActe']
        if 'modified' in itemNums and itemNums['modified'] == self.modified():
            return itemNums['nums']
        else:
            itemNums['modified'] = self.modified()

        items = self.getItemsInOrder()
        res = {}
        for item in items:
            item_num = 0
            cat = item.getCategory(True).getCategoryId()
            for item2 in items:
                if item2.getCategory(True).getCategoryId() != cat:
                    continue
                item_num = item_num + 1
                if item == item2:
                    res[item.UID()] = item_num
                    break
        # for "late" items, item number is continuous (HOJ1, HOJ2, HOJ3,... HOJn)
        items = self.getItemsInOrder(late=True)
        item_num = 1
        for item in items:
            if item.UID() in res:
                continue
            res[item.UID()] = item_num
            item_num = item_num + 1
        itemNums['nums'] = res
        return res
    Meeting.getItemNumsForActe = getItemNumsForActe

    def getRepresentative(self, sublst, itemUids, privacy='public',
                          late=False, oralQuestion='both', by_proposing_group=False, withCollege=False, renumber=False):
        '''Checks if the given category is the same than the previous one. Return none if so and the new one if not.'''
        previousCat = ''
        for sublist in self.getPrintableItemsByCategory(itemUids, privacy=privacy, late=late,
                                                        oralQuestion=oralQuestion,
                                                        by_proposing_group=by_proposing_group,
                                                        withCollege=withCollege,
                                                        renumber=renumber):
            if sublist == sublst:
                if sublist[0].Description() != previousCat:
                    return sublist[0].Description()
            previousCat = sublist[0].Description()
        return None

    def getCategoriesIdByNumber(self, numCateg):
        '''Returns categories filtered by their roman numerals'''
        tool = getToolByName(self.context, 'portal_plonemeeting')
        meetingConfig = tool.getMeetingConfig(self.context)
        allCategories = meetingConfig.getCategories()
        categsId = [item.getId() for item in allCategories
                    if item.Title().split('.')[0] == numCateg]
        return categsId

old_showDuplicateItemAction = MeetingItem.showDuplicateItemAction
old_checkAlreadyClonedToOtherMC = MeetingItem._checkAlreadyClonedToOtherMC


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

    def __init__(self, item):
        self.context = item

    security.declareProtected('Modify portal content', 'setCategory')

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
        self.getField('category').set(self, value, **kwargs)
    MeetingItem.setCategory = setCategory

    security.declareProtected('View', 'getFinanceAdvice')

    def getFinanceAdvice(self, checkPredecessors=False, **kwargs):
        '''Overrides the field 'financeAdvice' accessor to be able to pass
           a p_checkPredecessors parameter that will also query predecessor if it is
           in state 'return_college'.  Indeed, a finance advice is still valid if
           predecessor was 'return_college', the advice is not asked again.'''
        res = self.getField('financeAdvice').get(self)
        if checkPredecessors:
            pass
        return res
    MeetingItem.getFinanceAdvice = getFinanceAdvice

    def showDuplicateItemAction_cachekey(method, self, brain=False):
        '''cachekey method for self.showDuplicateItemAction.'''
        return (self, str(self.REQUEST.debug))

    security.declarePublic('showDuplicateItemAction')

    @ram.cache(showDuplicateItemAction_cachekey)
    def showDuplicateItemAction(self):
        '''Do not display the action in Council.'''
        # Conditions for being able to see the "duplicate an item" action:
        # - the user is not Plone-disk-aware;
        # - the user is creator in some group;
        # - the user must be able to see the item if it is private.
        # The user will duplicate the item in his own folder.
        if self.portal_type == 'MeetingItemCouncil':
            return False
        return old_showDuplicateItemAction(self)
    MeetingItem.showDuplicateItemAction = showDuplicateItemAction

    security.declarePublic('itemPositiveDecidedStates')

    def itemPositiveDecidedStates(self):
        '''See doc in interfaces.py.'''
        return ('accepted', 'accepted_but_modified', 'accepted_and_returned')

    def getExtraFieldsToCopyWhenCloning(self, cloned_to_same_mc):
        '''
          Keep some new fields when item is cloned (to another mc or from itemtemplate).
        '''
        res = ['labelForCouncil', 'privacyForCouncil', 'decisionSuite', 'decisionEnd']
        if cloned_to_same_mc:
            res = res + ['financeAdvice', 'archivingRef', 'textCheckList']
        return res

    def getCustomAdviceMessageFor(self, advice):
        '''If we are on a finance advice that is still not giveable because
           the item is not 'complete', we display a clear message.'''
        item = self.getSelf()
        if advice['id'] in FINANCE_GROUP_IDS and \
           advice['delay'] and \
           not advice['delay_started_on']:
            # item in state giveable but item not complete
            if item.queryState() in FINANCE_GIVEABLE_ADVICE_STATES:
                return {'displayDefaultComplementaryMessage': False,
                        'customAdviceMessage': translate('finance_advice_not_giveable_because_item_not_complete',
                                                         domain="PloneMeeting",
                                                         context=item.REQUEST)}
            elif getLastEvent(item, 'proposeToFinance') and item.queryState() in ('proposed_to_director',
                                                                                  'proposed_to_internal_reviewer'):
                # advice was already given but item was returned back to the service
                return {'displayDefaultComplementaryMessage': False,
                        'customAdviceMessage': translate(
                            'finance_advice_suspended_because_item_sent_back_to_proposing_group',
                            domain="PloneMeeting",
                            context=item.REQUEST)}
        return {'displayDefaultComplementaryMessage': True,
                'customAdviceMessage': None}

    def getFinanceGroupIdsForItem(self):
        '''Return the finance group ids the advice is asked
           on current item.  It only returns automatically asked advices.'''
        item = self.getSelf()
        for advice_id, advice_info in item.adviceIndex.items():
            if advice_id in FINANCE_GROUP_IDS and not advice_info['optional']:
                return advice_id
        return None

    security.declarePublic('getIcons')

    def getIcons(self, inMeeting, meeting):
        '''Check docstring in PloneMeeting interfaces.py.'''
        item = self.getSelf()
        res = []
        itemState = item.queryState()
        tool = getToolByName(item, 'portal_plonemeeting')
        cfg = tool.getMeetingConfig(item)
        # Default PM item icons
        res = res + MeetingItem.getIcons(item, inMeeting, meeting)
        # Add our icons for some review states
        if itemState == 'accepted_but_modified':
            res.insert(0, ('accepted_but_modified.png', 'icon_help_accepted_but_modified'))
        elif itemState == 'accepted_and_returned':
            res.insert(0, ('accepted_and_returned.png', 'icon_help_accepted_and_returned'))
        elif itemState == 'returned':
            res.insert(0, ('returned.png', 'icon_help_returned'))
        elif itemState == 'pre_accepted':
            res.insert(0, ('pre_accepted.png', 'icon_help_pre_accepted'))
        elif itemState == 'itemcreated_waiting_advices':
            res.insert(0, ('askAdvicesByItemCreator.png', 'icon_help_itemcreated_waiting_advices'))
        elif itemState == 'proposed_to_administrative_reviewer':
            res.insert(0, ('proposeToAdministrativeReviewer.png',
                           'icon_help_proposed_to_administrative_reviewer'))
        elif itemState == 'proposed_to_internal_reviewer':
            res.insert(0, ('proposeToInternalReviewer.png', 'icon_help_proposed_to_internal_reviewer'))
        elif itemState == 'proposed_to_internal_reviewer_waiting_advices':
            res.insert(0, ('askAdvicesByInternalReviewer.png',
                           'icon_help_proposed_to_internal_reviewer_waiting_advices'))
        elif itemState == 'proposed_to_director':
            res.insert(0, ('proposeToDirector.png', 'icon_help_proposed_to_director'))
        elif itemState == 'proposed_to_finance':
            res.insert(0, ('proposeToFinance.png', 'icon_help_proposed_to_finance'))
        elif itemState == 'marked_not_applicable':
            res.insert(0, ('marked_not_applicable.png', 'icon_help_marked_not_applicable'))
        # add an icon if item is down the workflow from the finances
        # if item was ever gone the the finances and now it is down to the
        # services, then it is considered as down the wf from the finances
        # so take into account every states before 'validated/proposed_to_finance'
        if not item.hasMeeting() and not itemState in ['proposed_to_finance', 'validated']:
            history = item.workflow_history[cfg.getItemWorkflow()]
            for event in history:
                if event['action'] == 'proposeToFinance':
                    res.append(('wf_down_finances.png', 'icon_help_wf_down_finances'))
                    break
        return res

    security.declarePublic('getAdvicesGroupsInfosForUser')

    def getAdvicesGroupsInfosForUser(self):
        '''Monkeypatch the MeetingItem.getAdvicesGroupsInfosForUser, look for XXX.'''
        tool = self.portal_plonemeeting
        cfg = tool.getMeetingConfig(self)
        # Advices must be enabled
        if not cfg.getUseAdvices():
            return ([], [])
        # Logged user must be an adviser
        meetingGroups = tool.getGroupsForUser(suffix='advisers')
        if not meetingGroups:
            return ([], [])
        # Produce the lists of groups to which the user belongs and for which,
        # - no advice has been given yet (list of advices to add)
        # - an advice has already been given (list of advices to edit/delete).
        toAdd = []
        toEdit = []
        powerAdvisers = cfg.getPowerAdvisersGroups()
        itemState = self.queryState()
        for group in meetingGroups:
            groupId = group.getId()
            if groupId in self.adviceIndex:
                advice = self.adviceIndex[groupId]
                if advice['type'] == NOT_GIVEN_ADVICE_VALUE and advice['advice_addable']:
                    toAdd.append((groupId, group.getName()))
                if advice['type'] != NOT_GIVEN_ADVICE_VALUE and advice['advice_editable']:
                    # XXX if we are a finance group, check if current member can edit the advice
                    # begin change by Products.MeetingLiege
                    if groupId in FINANCE_GROUP_IDS:
                        member = getToolByName(self, 'portal_membership').getAuthenticatedMember()
                        adviceObj = getattr(self, self.adviceIndex[groupId]['advice_id'])
                        if not member.has_role('MeetingFinanceEditor', adviceObj):
                            continue
                    # end change by Products.MeetingLiege
                    toEdit.append(groupId)
            # if not in self.adviceIndex, aka not already given
            # check if group is a power adviser and if he is allowed
            # to add an advice in current item state
            elif groupId in powerAdvisers and itemState in group.getItemAdviceStates(cfg):
                toAdd.append((groupId, group.getName()))
        return (toAdd, toEdit)
    MeetingItem.getAdvicesGroupsInfosForUser = getAdvicesGroupsInfosForUser

    security.declarePublic('mayEvaluateCompleteness')

    def mayEvaluateCompleteness(self):
        '''Condition for editing 'completeness' field,
           being able to define if item is 'complete' or 'incomplete'.
           Completeness can be evaluated by the finance controller.'''
        # user must be a finance controller
        item = self.getSelf()
        if item.isDefinedInTool():
            return
        membershipTool = getToolByName(item, 'portal_membership')
        member = membershipTool.getAuthenticatedMember()
        # bypass for Managers
        if member.has_role('Manager'):
            return True

        financeGroupId = item.adapted().getFinanceGroupIdsForItem()
        # a finance controller may evaluate if advice is actually asked
        # and may not change completeness if advice is currently given or has been given
        if not financeGroupId or \
           not '%s_financialcontrollers' % financeGroupId in member.getGroups():
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
        tool = getToolByName(item, 'portal_plonemeeting')
        membershipTool = getToolByName(item, 'portal_membership')
        member = membershipTool.getAuthenticatedMember()
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
        membershipTool = getToolByName(item, 'portal_membership')
        member = membershipTool.getAuthenticatedMember()
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
        tool = getToolByName(item, 'portal_plonemeeting')
        membershipTool = getToolByName(item, 'portal_membership')
        member = membershipTool.getAuthenticatedMember()
        if tool.isManager(item, realManagers=True) or \
           '%s_financialmanagers' % self.getFinanceGroupIdsForItem() in member.getGroups():
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
        wfTool = getToolByName(item, 'portal_workflow')
        if not item.queryState() == 'proposed_to_finance':
            return bool(wfTool.getTransitionsFor(item))
        else:
            # financial controller that may evaluate completeness?
            if item.adapted().mayEvaluateCompleteness():
                return True
            # advice addable or editable?
            (toAdd, toEdit) = item.getAdvicesGroupsInfosForUser()
            if item.getFinanceAdvice() in toAdd or \
               item.getFinanceAdvice() in toEdit:
                return True
        return False

    security.declarePrivate('listFinanceAdvices')

    def listFinanceAdvices(self):
        '''Vocabulary for the 'financeAdvice' field.'''
        tool = getToolByName(self, 'portal_plonemeeting')
        res = []
        res.append(('_none_', translate('no_financial_impact',
                                        domain='PloneMeeting',
                                        context=self.REQUEST)))
        for finance_group_id in FINANCE_GROUP_IDS:
            res.append((finance_group_id, getattr(tool, finance_group_id).getName()))
        return DisplayList(tuple(res))
    MeetingItem.listFinanceAdvices = listFinanceAdvices

    security.declarePrivate('listArchivingRefs')

    def listArchivingRefs(self):
        '''Vocabulary for the 'archivingRef' field.'''
        res = []
        tool = getToolByName(self, 'portal_plonemeeting')
        cfg = tool.getMeetingConfig(self)
        userGroups = set([group.getId() for group in tool.getGroupsForUser()])
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
        if item.getFinanceAdvice() == financeGroupId and \
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
        signature_event = advice_id and getLastEvent(getattr(item, advice_id), 'signFinancialAdvice') or ''
        res['out_of_financial_dpt'] = 'time' in signature_event and signature_event['time'] or ''
        res['out_of_financial_dpt_localized'] = res['out_of_financial_dpt']\
            and res['out_of_financial_dpt'].strftime('%d/%m/%Y') or ''
        res['advice_type'] = '<p><u>Type d\'avis:</u>  %s</p>' % \
                             (adviceData['type'].encode('utf-8'))
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
        Returns true if the current user has sufficient permission in
        the finance group passed as parameter.
        '''
        user = self.context.portal_membership.getAuthenticatedMember()
        userGroups = user.getGroups()
        for suffixe in FINANCE_GROUP_SUFFIXES:
            finance_group = finance_group_id + '_' + suffixe
            for group in userGroups:
                if finance_group == group:
                    return True
        return False

    def mayGenerateFDAdvice(self):
        '''
        Returns True if the current user has the right to generate the
        Financial Director Advice template.
        '''
        adviceHolder = self.getItemWithFinanceAdvice()

        if (adviceHolder.getFinanceAdvice() != '_none_' and
            (adviceHolder.adviceIndex[adviceHolder.getFinanceAdvice()]['hidden_during_redaction'] is False or
             self.isCurrentUserInFDGroup(adviceHolder.getFinanceAdvice()) is True)):
            return True
        return False

    def _checkAlreadyClonedToOtherMC(self, destMeetingConfigId):
        ''' '''
        res = old_checkAlreadyClonedToOtherMC(self, destMeetingConfigId)
        if not res:
            # double check if a predecessor was not already sent to the other meetingConfig
            # this can be the case when using 'accept_and_return' transition, the item is sent
            # and another item is cloned with same informations.  Check also that if a predecessor
            # was already sent to the council, this item in the council is not 'delayed' or 'marked_not_applicable'
            # in this case, we will send it again
            predecessor = self.getPredecessor()
            while predecessor:
                if predecessor.queryState() == 'accepted_and_returned' and \
                   old_checkAlreadyClonedToOtherMC(predecessor, destMeetingConfigId):
                    # if item was sent to council, check that this item is not 'delayed' or 'marked_not_applicable'
                    clonedItem = predecessor.getItemClonedToOtherMC(destMeetingConfigId)
                    if clonedItem and not clonedItem.queryState() in ('delayed', 'marked_not_applicable'):
                        return True
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
        # check if current self.context does not contain the given advice
        # and if it is an item as result of a return college
        # in case we use the finance advice of another item, the getFinanceAdvice is not _none_
        # but the financeAdvice is not in adviceIndex
        financeAdvice = self.context.getFinanceAdvice()
        if financeAdvice == '_none_' or \
           (financeAdvice in self.context.adviceIndex and
            self.context.adviceIndex[financeAdvice]['type'] != NOT_GIVEN_ADVICE_VALUE) or \
           not getLastEvent(self.context, 'return'):
            return self.context

        # we will walk predecessors until we found a finance advice that has been given
        # if we do not find a given advice, we will return the oldest item (last predecessor)
        predecessor = self.context.getPredecessor()
        validPredecessor = None
        # consider only if predecessor is in state 'accepted_and_returned' or 'returned'
        # otherwise, the predecessor could have been edited and advice is no longer valid
        while predecessor and predecessor.queryState() in ('accepted_and_returned', 'returned'):
            if predecessor.getFinanceAdvice() and \
               predecessor.getFinanceAdvice() in predecessor.adviceIndex:
                    validPredecessor = predecessor
                    # return immediately the validPredecessor if advice was given on it
                    if validPredecessor.adviceIndex[financeAdvice]['type'] != NOT_GIVEN_ADVICE_VALUE:
                        return validPredecessor
            predecessor = predecessor.getPredecessor()
        # either we found a valid predecessor, or we return self.context
        return validPredecessor or self.context

    def getLegalTextForFDAdvice(self):
        '''
        Helper method. Return legal text for each advice type.
        '''
        adviceHolder = self.getItemWithFinanceAdvice()
        financialStuff = adviceHolder.adapted().getFinancialAdviceStuff()
        res = ("<p>Attendu la demande d'avis adressée sur base d'un "
               "dossier complet au directeur financier en date du "
               "{0}.<br/></p>".format(financialStuff['out_of_financial_dpt_localized']))
        advice = adviceHolder.getAdviceDataFor(adviceHolder, adviceHolder.getFinanceAdvice())
        hidden = advice['hidden_during_redaction']
        statusWhenStopped = advice['delay_infos']['delay_status_when_stopped']
        adviceType = advice['type'].encode('utf-8').replace('Avis finances', '')
        comment = financialStuff['comment']
        adviceGivenOnLocalized = advice['advice_given_on_localized']
        delayStatus = advice['delay_infos']['delay_status']

        if not hidden and \
           adviceHolder.adapted().mayGenerateFDAdvice() and \
           adviceGivenOnLocalized and \
           (adviceType == ' défavorable' or adviceType == ' favorable'):
            res = res + "<p>Attendu l'avis {0} du Directeur financier annexé à la présente décision et " \
                "rendu conformément à l'article L1124-40 du Code de la " \
                "Démocratie locale et de la Décentralisation,</p>".format(adviceType.strip())
            if comment and adviceType == ' défavorable':
                res = res + "<p>{0}</p>".format(comment)
        elif statusWhenStopped == 'stopped_timed_out' or delayStatus == 'timed_out':
            res = res + "<p>Attendu l'absence d'avis du Directeur " \
                "financier rendu dans le délai prescrit à l'article " \
                "L1124-40 du Code de la Démocratie " \
                "locale et de la Décentralisation,</p>"
        else:
            res = ''
        return res

    security.declareProtected('Modify portal content', 'onEdit')

    def onEdit(self, isCreated):
        '''Update local_roles regarding the matterOfGroups and access of finance advisers
           to an item that has a predecessor that is 'returned' or 'accepted_and_returned'.'''
        item = self.getSelf()
        item._updateFinanceAdvisersAccessOfReturnedItem()
        item._updateMatterOfGroupsLocalRoles()

    def _updateFinanceAdvisersAccessOfReturnedItem(self):
        '''
          When an item is 'returned', if a finance advice was asked, the finance advice
          given on the 'returned' item is still the advice we consider, also for the new item
          that is directly validated.  But on this new item, finance advice is not asked anymore
          but we need to give a read access to the corresponding finance advisers.
        '''
        # do only that is there is a itemWithFinanceAdvice
        itemWithFinanceAdvice = self.adapted().getItemWithFinanceAdvice()
        if itemWithFinanceAdvice == self:
            return

        # ok, we have a predecessor with finance access, given access to current item also
        groupId = "{0}_advisers".format(self.getFinanceAdvice())
        self.manage_addLocalRoles(groupId, (READER_USECASES['advices'], ))
    MeetingItem._updateFinanceAdvisersAccessOfReturnedItem = _updateFinanceAdvisersAccessOfReturnedItem

    def _updateMatterOfGroupsLocalRoles(self):
        '''
          When an item is edited or it's review_state changed, we will update
          local_roles that give read access to the item once the item is at least
          validated.  Read access is given to the _observers Plone group of the selected
          matterOfGroups groups on the category used for the item.
        '''
        # when we are here, MeetingItem.updateLocalRoles already removed every unnecessary
        # local roles given to Plone _subgroups, re-add if necessary
        if not self.queryState() == 'validated' and not self.hasMeeting():
            return

        # compute _observers groups we will give local roles to
        category = self.getCategory(theObject=True)
        if not category or not category.meta_type == 'MeetingCategory':
            return

        # if we have a category, loop on groups of this matter
        # and give 'Reader' local role to the item
        for groupOfMatter in category.getGroupsOfMatter():
            groupId = '%s_observers' % groupOfMatter
            self.manage_addLocalRoles(groupId, ('Reader', ))
    MeetingItem._updateMatterOfGroupsLocalRoles = _updateMatterOfGroupsLocalRoles

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


class CustomMeetingConfig(MeetingConfig):
    '''Adapter that adapts a meetingConfig implementing IMeetingConfig to the
       interface IMeetingConfigCustom.'''

    implements(IMeetingConfigCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    def listAdviceTypes(self):
        d = "PloneMeeting"
        res = DisplayList((
            ("positive_finance", translate('positive_finance', domain=d, context=self.REQUEST)),
            ("negative_finance", translate('negative_finance', domain=d, context=self.REQUEST)),
            ("not_required_finance", translate('not_required_finance', domain=d, context=self.REQUEST)),
            ("positive", translate('positive', domain=d, context=self.REQUEST)),
            ("positive_with_remarks", translate('positive_with_remarks', domain=d, context=self.REQUEST)),
            ("negative", translate('negative', domain=d, context=self.REQUEST)),
            ("nil", translate('nil', domain=d, context=self.REQUEST)),
        ))
        return res
    MeetingConfig.listAdviceTypes = listAdviceTypes

    security.declarePrivate('listArchivingReferenceFinanceAdvices')

    def listArchivingReferenceFinanceAdvices(self):
        tool = getToolByName(self, 'portal_plonemeeting')
        res = []
        res.append(("no_finance_advice",
                    translate('no_finance_advice',
                              domain='PloneMeeting',
                              context=self.REQUEST,
                              default='No finance advice')))
        for groupId in FINANCE_GROUP_IDS:
            res.append((groupId, getattr(tool, groupId).getName()))
        return DisplayList(res)
    MeetingConfig.listArchivingReferenceFinanceAdvices = listArchivingReferenceFinanceAdvices

    security.declarePrivate('listActiveMeetingGroupsForArchivingRefs')

    def listActiveMeetingGroupsForArchivingRefs(self):
        """
          Vocabulary for the archivingRefs.restrict_to_groups DatagridField attribute.
          It returns every active MeetingGroups.
        """
        res = []
        tool = getToolByName(self, 'portal_plonemeeting')
        for mGroup in tool.getMeetingGroups():
            res.append((mGroup.getId(), mGroup.getName()))
        # make sure that if a configuration was defined for a group
        # that is now inactive, it is still displayed
        storedArchivingRefsGroups = [archivingRef['restrict_to_groups'] for archivingRef in self.getArchivingRefs()]
        if storedArchivingRefsGroups:
            groupsInVocab = [group[0] for group in res]
            for storedArchivingRefsGroup in storedArchivingRefsGroups:
                for group in storedArchivingRefsGroup:
                    if not group in groupsInVocab:
                        mGroup = getattr(tool, group)
                        res.append((mGroup.getId(), mGroup.getName()))
        return DisplayList(res).sortedByValue()
    MeetingConfig.listActiveMeetingGroupsForArchivingRefs = listActiveMeetingGroupsForArchivingRefs

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

    security.declarePublic('getDefaultAdviceHiddenDuringRedaction')

    def getDefaultAdviceHiddenDuringRedaction(self, **kwargs):
        '''
          Override the accessor of field MeetingConfig.defaultAdviceHiddenDuringRedaction
          to force to 'True' when used for a finance group.
        '''
        factory = queryUtility(IVocabularyFactory, u'Products.PloneMeeting.content.advice.advice_group_vocabulary')
        published = self.REQUEST.get('PUBLISHED', '')
        if not published:
            return False
        if not hasattr(published, 'context'):
            # we are on the MeetingConfig, return the stored value
            return self.getField('defaultAdviceHiddenDuringRedaction').get(self, **kwargs)
        context = published.context
        groupVocab = factory(context)
        groupIds = set([group.value for group in groupVocab._terms])
        if set(FINANCE_GROUP_IDS).intersection(groupIds):
            return True
        return self.getField('defaultAdviceHiddenDuringRedaction').get(self, **kwargs)
    MeetingConfig.getDefaultAdviceHiddenDuringRedaction = getDefaultAdviceHiddenDuringRedaction

    security.declarePublic('searchItemsToControlCompletenessOf')

    def searchItemsToControlCompletenessOf(self, sortKey, sortOrder, filterKey, filterValue, **kwargs):
        '''Queries all items for which there is completeness to evaluate, so where completeness
           is not 'completeness_complete'.'''
        # Create query parameters
        # only query elements the current user may evaluate completeness of
        groupIds = []
        membershipTool = getToolByName(self, 'portal_membership')
        userGroups = membershipTool.getAuthenticatedMember().getGroups()
        for financeGroup in FINANCE_GROUP_IDS:
            # only keep finance groupIds the current user is controller for
            if '%s_financialcontrollers' % financeGroup in userGroups:
                groupIds.append('delay__%s_advice_not_giveable' % financeGroup)
        params = {'portal_type': self.getItemTypeName(),
                  # KeywordIndex 'getCompleteness' use 'OR' by default
                  'getCompleteness': ('completeness_not_yet_evaluated',
                                      'completeness_incomplete',
                                      'completeness_evaluation_asked_again'),
                  'indexAdvisers': groupIds,
                  'review_state': 'proposed_to_finance',
                  'sort_on': sortKey,
                  'sort_order': sortOrder, }
        # Manage filter
        if filterKey:
            params[filterKey] = prepareSearchValue(filterValue)
        # update params with kwargs
        params.update(kwargs)
        # Perform the query in portal_catalog
        return self.portal_catalog(**params)
    MeetingConfig.searchItemsToControlCompletenessOf = searchItemsToControlCompletenessOf

    security.declarePublic('searchItemsWithAdviceProposedToFinancialController')

    def searchItemsWithAdviceProposedToFinancialController(self, sortKey, sortOrder, filterKey, filterValue, **kwargs):
        '''Queries all items for which there is an advice in state 'proposed_to_financial_controller'.'''
        groupIds = []
        membershipTool = getToolByName(self, 'portal_membership')
        userGroups = membershipTool.getAuthenticatedMember().getGroups()
        for financeGroup in FINANCE_GROUP_IDS:
            # only keep finance groupIds the current user is controller for
            if '%s_financialcontrollers' % financeGroup in userGroups:
                groupIds.append('delay__%s_proposed_to_financial_controller' % financeGroup)
        # Create query parameters
        params = {'portal_type': self.getItemTypeName(),
                  # KeywordIndex 'indexAdvisers' use 'OR' by default
                  'indexAdvisers': groupIds,
                  'sort_on': sortKey,
                  'sort_order': sortOrder, }
        # Manage filter
        if filterKey:
            params[filterKey] = prepareSearchValue(filterValue)
        # update params with kwargs
        params.update(kwargs)
        # Perform the query in portal_catalog
        return self.portal_catalog(**params)
    MeetingConfig.searchItemsWithAdviceProposedToFinancialController = \
        searchItemsWithAdviceProposedToFinancialController

    security.declarePublic('searchItemsWithAdviceProposedToFinancialReviewer')

    def searchItemsWithAdviceProposedToFinancialReviewer(self, sortKey, sortOrder, filterKey, filterValue, **kwargs):
        '''Queries all items for which there is an advice in state 'proposed_to_financial_reviewer'.'''
        groupIds = []
        membershipTool = getToolByName(self, 'portal_membership')
        userGroups = membershipTool.getAuthenticatedMember().getGroups()
        for financeGroup in FINANCE_GROUP_IDS:
            # only keep finance groupIds the current user is reviewer for
            if '%s_financialreviewers' % financeGroup in userGroups:
                groupIds.append('delay__%s_proposed_to_financial_reviewer' % financeGroup)
        # Create query parameters
        params = {'portal_type': self.getItemTypeName(),
                  # KeywordIndex 'indexAdvisers' use 'OR' by default
                  'indexAdvisers': groupIds,
                  'sort_on': sortKey,
                  'sort_order': sortOrder, }
        # Manage filter
        if filterKey:
            params[filterKey] = prepareSearchValue(filterValue)
        # update params with kwargs
        params.update(kwargs)
        # Perform the query in portal_catalog
        return self.portal_catalog(**params)
    MeetingConfig.searchItemsWithAdviceProposedToFinancialReviewer = searchItemsWithAdviceProposedToFinancialReviewer

    security.declarePublic('searchItemsWithAdviceProposedToFinancialManager')

    def searchItemsWithAdviceProposedToFinancialManager(self, sortKey, sortOrder, filterKey, filterValue, **kwargs):
        '''Queries all items for which there is an advice in state 'proposed_to_financial_manager'.'''
        groupIds = []
        membershipTool = getToolByName(self, 'portal_membership')
        userGroups = membershipTool.getAuthenticatedMember().getGroups()
        for financeGroup in FINANCE_GROUP_IDS:
            # only keep finance groupIds the current user is manager for
            if '%s_financialmanagers' % financeGroup in userGroups:
                groupIds.append('delay__%s_proposed_to_financial_manager' % financeGroup)
        # Create query parameters
        params = {'portal_type': self.getItemTypeName(),
                  # KeywordIndex 'indexAdvisers' use 'OR' by default
                  'indexAdvisers': groupIds,
                  'sort_on': sortKey,
                  'sort_order': sortOrder, }
        # Manage filter
        if filterKey:
            params[filterKey] = prepareSearchValue(filterValue)
        # update params with kwargs
        params.update(kwargs)
        # Perform the query in portal_catalog
        return self.portal_catalog(**params)
    MeetingConfig.searchItemsWithAdviceProposedToFinancialManager = searchItemsWithAdviceProposedToFinancialManager

    def _dataForArchivingRefRowId(self, row_id):
        '''Returns the data for the given p_row_id from the field 'archivingRefs'.'''
        cfg = self.getSelf()
        for archivingRef in cfg.getArchivingRefs():
            if archivingRef['row_id'] == row_id:
                return dict(archivingRef)


class CustomMeetingGroup(MeetingGroup):
    '''Adapter that adapts a meetingGroup implementing IMeetingGroup to the
       interface IMeetingGroupCustom.'''

    implements(IMeetingGroupCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    security.declareProtected('Modify portal content', 'onEdit')

    def onEdit(self, isCreated):
        '''
          When a MeetingGroup is created/edited, if it is a finance group
          (it's id is in FINANCE_GROUP_IDS), we create relevant finance Plone groups.
          We do this on creation and on edit so it is checked every times the MeetingGroup
          is edited, so removed elements from config and so on are back to normal...
        '''
        group = self.getSelf()
        if not group.getId() in FINANCE_GROUP_IDS:
            return
        for groupSuffix in FINANCE_GROUP_SUFFIXES:
            groupId = group.getPloneGroupId(groupSuffix)
            portal_groups = getToolByName(group, 'portal_groups')
            ploneGroup = portal_groups.getGroupById(groupId)
            if ploneGroup:
                continue
            group._createOrUpdatePloneGroup(groupSuffix)

    def getPloneGroups(self, idsOnly=False, acl=False):
        '''Returns the list of Plone groups tied to this MeetingGroup. If
           p_acl is True, it returns True PAS groups. Else, it returns Plone
           wrappers from portal_groups.'''
        res = []
        suffixes = tuple(MEETING_GROUP_SUFFIXES)
        if self.getId() in FINANCE_GROUP_IDS:
            suffixes = suffixes + FINANCE_GROUP_SUFFIXES
        for suffix in suffixes:
            groupId = self.getPloneGroupId(suffix)
            if idsOnly:
                res.append(groupId)
            else:
                if acl:
                    group = self.acl_users.getGroupByName(groupId)
                else:
                    group = self.portal_groups.getGroupById(groupId)
                res.append(group)
        return res
    MeetingGroup.getPloneGroups = getPloneGroups


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
          It returns every active MeetingGroups.
        """
        res = []
        tool = getToolByName(self, 'portal_plonemeeting')
        for mGroup in tool.getMeetingGroups():
            res.append((mGroup.getId(), mGroup.getName()))
        # make sure that if a configuration was defined for a group
        # that is now inactive, it is still displayed
        storedGroupsOfMatter = self.getGroupsOfMatter()
        if storedGroupsOfMatter:
            groupsInVocab = [group[0] for group in res]
            for storedGroupOfMatter in storedGroupsOfMatter:
                if not storedGroupOfMatter in groupsInVocab:
                    mGroup = getattr(tool, storedGroupOfMatter)
                    res.append((mGroup.getId(), mGroup.getName()))
        return DisplayList(res).sortedByValue()
    MeetingCategory.listGroupsOfMatter = listGroupsOfMatter


old_formatMeetingDate = ToolPloneMeeting.formatMeetingDate


class CustomToolPloneMeeting(ToolPloneMeeting):
    '''Adapter that adapts portal_plonemeeting.'''

    implements(IToolPloneMeetingCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    security.declarePublic('formatMeetingDate')

    def formatMeetingDate(self, meeting, lang=None,
                          short=False, withHour=False, prefixed=None,
                          markAdoptsNextCouncilAgenda=True):
        '''
          Suffix date with '*' if given p_aDate is a Meeting brain.
        '''
        formatted_date = old_formatMeetingDate(self, meeting, lang, short, withHour, prefixed)
        adoptsNextCouncilAgenda = False
        if meeting.__class__.__name__ == 'mybrains':
            if meeting.getAdoptsNextCouncilAgenda:
                adoptsNextCouncilAgenda = True
        else:
            if meeting.getAdoptsNextCouncilAgenda():
                adoptsNextCouncilAgenda = True
        if adoptsNextCouncilAgenda and markAdoptsNextCouncilAgenda:
            formatted_date += '*'
        return formatted_date
    ToolPloneMeeting.formatMeetingDate = formatMeetingDate

    def isFinancialUser_cachekey(method, self, brain=False):
        '''cachekey method for self.isFinancialUser.'''
        return str(self.REQUEST.debug)

    security.declarePublic('isFinancialUser')

    @ram.cache(isFinancialUser_cachekey)
    def isFinancialUser(self):
        '''Is current user a financial user, so in groups 'financialcontrollers',
           'financialreviewers' or 'financialmanagers'.'''
        member = getToolByName(self, 'portal_membership').getAuthenticatedMember()
        for groupId in member.getGroups():
            for suffix in FINANCE_GROUP_SUFFIXES:
                if groupId.endswith('_%s' % suffix):
                    return True
        return False
    ToolPloneMeeting.isFinancialUser = isFinancialUser


class MeetingCollegeLiegeWorkflowActions(MeetingWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingCollegeWorkflowActions'''

    implements(IMeetingCollegeLiegeWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doBackToCreated')

    def doBackToCreated(self, stateChange):
        '''When a meeting go back to the "created" state, for example the
           meeting manager wants to add an item, we do not do anything.'''
        pass


class MeetingCollegeLiegeWorkflowConditions(MeetingWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingCollegeWorkflowConditions'''

    implements(IMeetingCollegeLiegeWorkflowConditions)
    security = ClassSecurityInfo()

    security.declarePublic('mayFreeze')

    def mayFreeze(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True  # At least at present
            if not self.context.getRawItems():
                res = No(translate('item_required_to_publish',
                                   domain='PloneMeeting',
                                   context=self.context.REQUEST))
        return res

    security.declarePublic('mayClose')

    def mayClose(self):
        res = False
        # The user just needs the "Review portal content" permission on the
        # object to close it.
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayDecide')

    def mayDecide(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayChangeItemsOrder')

    def mayChangeItemsOrder(self):
        '''We can change the order if the meeting is not closed'''
        res = False
        if checkPermission(ModifyPortalContent, self.context) and \
           self.context.queryState() not in ('closed'):
            res = True
        return res

    security.declarePublic('mayCorrect')

    def mayCorrect(self):
        '''Take the default behaviour except if the meeting is frozen
           we still have the permission to correct it.'''
        from Products.PloneMeeting.Meeting import MeetingWorkflowConditions
        res = MeetingWorkflowConditions.mayCorrect(self)
        currentState = self.context.queryState()
        if res is not True and currentState == "frozen":
            # Change the behaviour for being able to correct a frozen meeting
            # back to created.
            if checkPermission(ReviewPortalContent, self.context):
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
        wfTool = getToolByName(self.context, 'portal_workflow')
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

    security.declarePrivate('doPre_accept')

    def doPre_accept(self, stateChange):
        pass

    security.declarePrivate('doAccept_but_modify')

    def doAccept_but_modify(self, stateChange):
        pass

    security.declarePrivate('doAccept')

    def doAccept(self, stateChange):
        pass

    security.declarePrivate('doMark_not_applicable')

    def doMark_not_applicable(self, stateChange):
        pass

    security.declarePrivate('doAccept_and_return')

    def doAccept_and_return(self, stateChange):
        self._returnCollege()

    security.declarePrivate('doReturn')

    def doReturn(self, stateChange):
        '''
          When the item is 'returned', it will be automatically
          duplicated then validated for a next meeting.
        '''
        self._returnCollege()

    def _returnCollege(self):
        '''
          Manage 'return college', item is duplicated
          then validated for a next meeting.
        '''
        newItem = self.context.clone(cloneEventAction='return', keepProposingGroup=True)
        newItem.setPredecessor(self.context)
        # now that the item is cloned, we need to validate it
        # so it is immediately available for a next meeting
        # we will also set back correct proposingGroup if it was changed
        # we do not pass p_keepProposingGroup to clone() here above
        # because we need to validate the newItem and if we change the proposingGroup
        # maybe we could not...  So validate then set correct proposingGroup...
        wfTool = getToolByName(self.context, 'portal_workflow')
        self.context.REQUEST.set('mayValidate', True)
        wfTool.doActionFor(newItem, 'validate')
        self.context.REQUEST.set('mayValidate', False)


class MeetingItemCollegeLiegeWorkflowConditions(MeetingItemWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCollegeWorkflowConditions'''

    implements(IMeetingItemCollegeLiegeWorkflowConditions)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item  # Implements IMeetingItem
        self.sm = getSecurityManager()

    security.declarePublic('mayProposeToAdminstrativeReviewer')

    def mayProposeToAdminstrativeReviewer(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            if not self.context.getCategory():
                return No(translate('required_category_ko',
                                    domain="PloneMeeting",
                                    context=self.context.REQUEST))
            res = True
        return res

    security.declarePublic('mayProposeToInternalReviewer')

    def mayProposeToInternalReviewer(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayProposeToDirector')

    def mayProposeToDirector(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayProposeToFinance')

    def mayProposeToFinance(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            # check if one of the finance group needs to give advice on
            # the item, if it is the case, the item must go to finance before being validated
            if self.context.adapted().getFinanceGroupIdsForItem():
                return True
        return res

    security.declarePublic('mayAskAdvicesByItemCreator')

    def mayAskAdvicesByItemCreator(self):
        '''May advices be asked by item creator.'''
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            # if no advice to ask or only advice to ask is financial advice,
            # we do not let item creator ask advices, non sense...
            if self.context.hasAdvices(toGive=True, adviceIdsToBypass=FINANCE_GROUP_IDS):
                res = True
            else:
                # return a 'No' instance explaining that no advice is (still) asked on this item
                res = No(translate('advice_required_to_ask_advices',
                                   domain='PloneMeeting',
                                   context=self.context.REQUEST))
        return res

    security.declarePublic('mayAskAdvicesByInternalReviewer')

    def mayAskAdvicesByInternalReviewer(self):
        '''May advices be asked by internal reviewer.'''
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            if self.context.hasAdvices(toGive=True, adviceIdsToBypass=FINANCE_GROUP_IDS):
                res = True
            else:
                # return a 'No' instance explaining that no advice is (still) asked on this item
                res = No(translate('advice_required_to_ask_advices',
                                   domain='PloneMeeting',
                                   context=self.context.REQUEST))
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
            is 'positive_finance' or 'not_required_finance' or it can be manually
            validated by the director if item emergency has been asked and motivated on the item.
        """
        res = False
        # very special case, we can bypass the guard if a 'mayValidate'
        # value is found to True in the REQUEST
        if self.context.REQUEST.get('mayValidate', False):
            return True
        tool = getToolByName(self.context, 'portal_plonemeeting')
        isManager = tool.isManager(self.context)
        item_state = self.context.queryState()
        # first of all, the use must have the 'Review portal content permission'
        if checkPermission(ReviewPortalContent, self.context):
            res = True
            if not self.context.getCategory():
                return No(translate('required_category_ko',
                                    domain="PloneMeeting",
                                    context=self.context.REQUEST))
            finance_advice = self.context.adapted().getFinanceGroupIdsForItem()
            # if the current item state is 'itemcreated', only the MeetingManager can validate
            if item_state == 'itemcreated' and not isManager:
                res = False
            # special case for item having finance advice that was still under redaction when delay timed out
            # a MeetingManager mut be able to validate it
            elif item_state in ['proposed_to_finance', 'proposed_to_director', ] and \
                    finance_advice and \
                    self.context.adviceIndex[finance_advice]['delay_infos']['delay_status'] == 'timed_out':
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
        return res

    security.declarePublic('mayDecide')

    def mayDecide(self):
        '''We may decide an item if the linked meeting is in relevant state.'''
        res = False
        meeting = self.context.getMeeting()
        if checkPermission(ReviewPortalContent, self.context) and \
           meeting and (meeting.queryState() in ['decided', 'closed', ]):
            res = True
        return res

    security.declarePublic('mayAcceptAndReturn')

    def mayAcceptAndReturn(self):
        '''This is a decision only avaialble if item will be sent to council.'''
        res = False
        if self.mayDecide() and checkPermission(ReviewPortalContent, self.context) and \
           'meeting-config-council' in self.context.getOtherMeetingConfigsClonableTo():
            res = True
        return res

    security.declarePublic('mayCorrect')

    def mayCorrect(self):
        # Check with the default PloneMeeting method and our test if res is
        # False. The diffence here is when we correct an item from itemfrozen to
        # presented, we have to check if the Meeting is in the "created" state
        # and not "published".
        res = MeetingItemWorkflowConditions.mayCorrect(self)
        # Manage our own behaviour now when the item is linked to a meeting,
        # a MeetingManager can correct anything except if the meeting is closed
        if res is not True:
            if checkPermission(ReviewPortalContent, self.context):
                # Get the meeting
                meeting = self.context.getMeeting()
                if meeting:
                    # Meeting can be None if there was a wf problem leading
                    # an item to be in a "presented" state with no linked
                    # meeting.
                    meetingState = meeting.queryState()
                    # A user having ReviewPortalContent permission can correct
                    # an item in any case except if the meeting is closed.
                    if meetingState != 'closed':
                        res = True
                else:
                    res = True
            # special case for financial controller that can send an item back to
            # the internal reviewer if it is in state 'proposed_to_finance' and
            # item is incomplete
            elif self.context.queryState() == 'proposed_to_finance':
                # user must be a member of the finance group the advice is asked to
                financeGroupId = self.context.adapted().getFinanceGroupIdsForItem()
                memberGroups = getToolByName(self.context, 'portal_membership').getAuthenticatedMember().getGroups()
                for suffix in FINANCE_GROUP_SUFFIXES:
                    financeSubGroupId = '%s_%s' % (financeGroupId, suffix)
                    if financeSubGroupId in memberGroups:
                        res = True
                        break
        return res

    security.declarePublic('mayBackToProposedToDirector')

    def mayBackToProposedToDirector(self):
        '''
          Item may back to proposedToDirector if a value 'mayBackToProposedToDirector' is
          found and True in the REQUEST.  It means that the item is 'proposed_to_finance' and that the
          freshly signed advice was negative.
          If the item is 'validated', a MeetingManager can send it back to the director.
        '''
        res = False
        if self.context.REQUEST.get('mayBackToProposedToDirector', False) or \
           checkPermission(ReviewPortalContent, self.context):
            res = True
        return res


class MeetingCouncilLiegeWorkflowActions(MeetingWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingCouncilWorkflowActions'''

    implements(IMeetingCouncilLiegeWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doBackToCreated')

    def doBackToCreated(self, stateChange):
        '''When a meeting go back to the "created" state, for example the
           meeting manager wants to add an item, we do not do anything.'''
        pass


class MeetingCouncilLiegeWorkflowConditions(MeetingWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingCouncilWorkflowConditions'''

    implements(IMeetingCouncilLiegeWorkflowConditions)
    security = ClassSecurityInfo()

    security.declarePublic('mayFreeze')

    def mayFreeze(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True  # At least at present
            if not self.context.getRawItems():
                res = No(translate('item_required_to_publish',
                                   domain='PloneMeeting',
                                   context=self.context.REQUEST))
        return res

    security.declarePublic('mayClose')

    def mayClose(self):
        res = False
        # The user just needs the "Review portal content" permission on the
        # object to close it.
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayDecide')

    def mayDecide(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayChangeItemsOrder')

    def mayChangeItemsOrder(self):
        '''We can change the order if the meeting is not closed'''
        res = False
        if checkPermission(ModifyPortalContent, self.context) and \
           self.context.queryState() not in ('closed'):
            res = True
        return res

    security.declarePublic('mayCorrect')

    def mayCorrect(self):
        '''Take the default behaviour except if the meeting is frozen
           we still have the permission to correct it.'''
        from Products.PloneMeeting.Meeting import MeetingWorkflowConditions
        res = MeetingWorkflowConditions.mayCorrect(self)
        currentState = self.context.queryState()
        if res is not True and currentState == "frozen":
            # Change the behaviour for being able to correct a frozen meeting
            # back to created.
            if checkPermission(ReviewPortalContent, self.context):
                return True
        return res


class MeetingItemCouncilLiegeWorkflowActions(MeetingItemWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCouncilWorkflowActions'''

    implements(IMeetingItemCouncilLiegeWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doProposeToDirector')

    def doProposeToDirector(self, stateChange):
        pass

    security.declarePrivate('doAccept_pre_accept')

    def doAccept_pre_accept(self, stateChange):
        pass

    security.declarePrivate('doAccept_but_modify')

    def doAccept_but_modify(self, stateChange):
        pass

    security.declarePrivate('doDelay')

    def doDelay(self, stateChange):
        '''When an item is delayed, by default it is duplicated but we do not duplicate it here'''
        pass

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
        self.sm = getSecurityManager()

    security.declarePublic('mayCorrect')

    def mayCorrect(self):
        # Check with the default PloneMeeting method and our test if res is
        # False. The diffence here is when we correct an item from itemfrozen to
        # presented, we have to check if the Meeting is in the "created" state
        # and not "published".
        res = MeetingItemWorkflowConditions.mayCorrect(self)
        # Manage our own behaviour now when the item is linked to a meeting,
        # a MeetingManager can correct anything except if the meeting is closed
        if res is not True:
            if checkPermission(ReviewPortalContent, self.context):
                # Get the meeting
                meeting = self.context.getMeeting()
                if meeting:
                    # Meeting can be None if there was a wf problem leading
                    # an item to be in a "presented" state with no linked
                    # meeting.
                    meetingState = meeting.queryState()
                    # A user having ReviewPortalContent permission can correct
                    # an item in any case except if the meeting is closed.
                    if meetingState != 'closed':
                        res = True
                else:
                    res = True
        return res

    security.declarePublic('mayDecide')

    def mayDecide(self):
        '''We may decide an item if the linked meeting is in relevant state.'''
        res = False
        meeting = self.context.getMeeting()
        if checkPermission(ReviewPortalContent, self.context) and \
           meeting and (meeting.queryState() in ['decided', 'closed', ]):
            res = True
        return res

    security.declarePublic('isLateFor')

    def isLateFor(self, meeting):
        """
          No late functionnality for Council
        """
        return False


from Products.PloneMeeting.content.advice import MeetingAdvice
old_get_advice_given_on = MeetingAdvice.get_advice_given_on


def get_advice_given_on(self):
    '''Monkeypatch the meetingadvice.get_advice_given_on method, if it is
       a finance advice, we will return date of last transition 'sign_advice'.'''
    if self.advice_group in FINANCE_GROUP_IDS:
        lastEvent = getLastEvent(self, 'signFinancialAdvice')
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
InitializeClass(CustomMeetingGroup)
InitializeClass(CustomMeetingItem)
InitializeClass(CustomToolPloneMeeting)
InitializeClass(MeetingCollegeLiegeWorkflowActions)
InitializeClass(MeetingCollegeLiegeWorkflowConditions)
InitializeClass(MeetingItemCollegeLiegeWorkflowActions)
InitializeClass(MeetingItemCollegeLiegeWorkflowConditions)
InitializeClass(MeetingCouncilLiegeWorkflowActions)
InitializeClass(MeetingCouncilLiegeWorkflowConditions)
InitializeClass(MeetingItemCouncilLiegeWorkflowActions)
InitializeClass(MeetingItemCouncilLiegeWorkflowConditions)
# ------------------------------------------------------------------------------
