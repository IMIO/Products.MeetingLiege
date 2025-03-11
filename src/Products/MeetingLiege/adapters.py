# -*- coding: utf-8 -*-

from AccessControl import ClassSecurityInfo
from collections import OrderedDict
from collective.contact.plonegroup.utils import get_all_suffixes
from collective.contact.plonegroup.utils import get_organization
from collective.contact.plonegroup.utils import get_organizations
from collective.contact.plonegroup.utils import get_plone_group_id
from Globals import InitializeClass
from imio.actionspanel.utils import unrestrictedRemoveGivenObject
from imio.helpers.cache import cleanRamCacheFor
from imio.helpers.cache import get_cachekey_volatile
from imio.helpers.cache import get_plone_groups_for_user
from imio.helpers.content import safe_encode
from imio.helpers.content import uuidsToObjects
from imio.helpers.content import uuidToObject
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
from Products.MeetingLiege.config import COUNCILITEM_DECISIONEND_SENTENCE
from Products.MeetingLiege.config import COUNCILITEM_DECISIONEND_SENTENCE_RAW
from Products.MeetingLiege.config import FINANCE_ADVICE_LEGAL_TEXT
from Products.MeetingLiege.config import FINANCE_ADVICE_LEGAL_TEXT_NOT_GIVEN
from Products.MeetingLiege.config import FINANCE_ADVICE_LEGAL_TEXT_PRE
from Products.MeetingLiege.config import FINANCE_GIVEABLE_ADVICE_STATES
from Products.MeetingLiege.config import FINANCE_GROUP_SUFFIXES
from Products.MeetingLiege.config import ITEM_MAIN_INFOS_HISTORY
from Products.MeetingLiege.interfaces import IMeetingAdviceFinancesWorkflowActions
from Products.MeetingLiege.interfaces import IMeetingAdviceFinancesWorkflowConditions
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
from Products.MeetingLiege.utils import bg_group_uid
from Products.MeetingLiege.utils import finance_group_uids
from Products.MeetingLiege.utils import gm_group_uid
from Products.MeetingLiege.utils import not_copy_group_uids
from Products.MeetingLiege.utils import treasury_group_cec_uid
from Products.PloneMeeting.adapters import CompoundCriterionBaseAdapter
from Products.PloneMeeting.adapters import ItemPrettyLinkAdapter
from Products.PloneMeeting.adapters import MeetingPrettyLinkAdapter
from Products.PloneMeeting.adapters import query_user_groups_cachekey
from Products.PloneMeeting.config import MEETING_REMOVE_MOG_WFA
from Products.PloneMeeting.config import NOT_GIVEN_ADVICE_VALUE
from Products.PloneMeeting.config import PMMessageFactory as _
from Products.PloneMeeting.config import READER_USECASES
from Products.PloneMeeting.content.advice import MeetingAdvice
from Products.PloneMeeting.content.meeting import Meeting
from Products.PloneMeeting.interfaces import IMeetingConfigCustom
from Products.PloneMeeting.interfaces import IMeetingCustom
from Products.PloneMeeting.interfaces import IMeetingItemCustom
from Products.PloneMeeting.interfaces import IToolPloneMeetingCustom
from Products.PloneMeeting.MeetingConfig import MeetingConfig
from Products.PloneMeeting.MeetingItem import MeetingItem
from Products.PloneMeeting.MeetingItem import MeetingItemWorkflowActions
from Products.PloneMeeting.MeetingItem import MeetingItemWorkflowConditions
from Products.PloneMeeting.model import adaptations
from Products.PloneMeeting.model.adaptations import _addDecidedState
from Products.PloneMeeting.model.adaptations import _addIsolatedState
from Products.PloneMeeting.ToolPloneMeeting import ToolPloneMeeting
from Products.PloneMeeting.utils import get_current_user_id
from Products.PloneMeeting.utils import isPowerObserverForCfg
from Products.PloneMeeting.utils import org_id_to_uid
from Products.PloneMeeting.workflows.advice import MeetingAdviceWorkflowActions
from Products.PloneMeeting.workflows.advice import MeetingAdviceWorkflowConditions
from Products.PloneMeeting.workflows.meeting import MeetingWorkflowActions
from Products.PloneMeeting.workflows.meeting import MeetingWorkflowConditions
from zope.annotation.interfaces import IAnnotations
from zope.component import getAdapter
from zope.i18n import translate
from zope.interface import implements


# we get this list by running utils.get_enabled_ordered_wfas(tool) on a living site
# order is important, so keep the one from MeetingConfig.wfAdaptations
keptWfAdaptations = (
    'item_validation_shortcuts',
    'item_validation_no_validate_shortcuts',
    'only_creator_may_delete',
    'no_freeze',
    'no_publication',
    'no_decide',
    'accepted_but_modified',
    'mark_not_applicable',
    'refused',
    'delayed',
    'pre_accepted',
    'return_to_proposing_group',
    'waiting_advices',
    'waiting_advices_proposing_group_send_back',
    'waiting_advices_adviser_send_back',
    MEETING_REMOVE_MOG_WFA)
# add our own wfAdaptations
ownWfAdaptations = ('returned', 'accepted_and_returned', 'sent_to_council_emergency')
customWfAdaptations = keptWfAdaptations + ownWfAdaptations
MeetingConfig.wfAdaptations = customWfAdaptations

LIEGE_WAITING_ADVICES_FROM_STATES = {
    'meeting-config-college':
    (
        {'from_states': ('itemcreated', ),
         'back_states': ('itemcreated',
                         'proposed_to_administrative_reviewer',
                         'proposed_to_internal_reviewer',
                         'proposed_to_director', ),
         'use_custom_icon': False,
         # is translated to "Remove from meeting"
         'use_custom_back_transition_title_for': ('validated', ),
         # if () given, a custom transition icon is used for every back transitions
         'only_use_custom_back_transition_icon_for': ('validated', ),
         'use_custom_transition_title_for':
            {'wait_advices_from_itemcreated': 'wait_advices_from_itemcreated', },
         'adviser_may_validate': False,
         'new_state_id': 'itemcreated_waiting_advices',
         },
        {'from_states': ('itemcreated',
                         'proposed_to_administrative_reviewer',
                         'proposed_to_internal_reviewer', ),
         'back_states': ('proposed_to_internal_reviewer',
                         'proposed_to_director', ),
         'use_custom_icon': False,
         # is translated to "Remove from meeting"
         'use_custom_back_transition_title_for': ('validated', ),
         # if () given, a custom transition icon is used for every back transitions
         'only_use_custom_back_transition_icon_for': ('validated', ),
         'use_custom_transition_title_for': {
            'wait_advices_from_itemcreated__to__proposed_to_internal_reviewer_waiting_advices':
            'wait_advices_from_itemcreated__to__proposed_to_internal_reviewer_waiting_advices',
            'wait_advices_from_proposed_to_administrative_reviewer':
            'wait_advices_from_proposed_to_administrative_reviewer',
            'wait_advices_from_proposed_to_internal_reviewer':
            'wait_advices_from_proposed_to_internal_reviewer', },
         'adviser_may_validate': False,
         'new_state_id': 'proposed_to_internal_reviewer_waiting_advices',
         },
        {'from_states': ('proposed_to_director', ),
         'back_states': ('proposed_to_internal_reviewer',
                         'proposed_to_director', ),
         'use_custom_icon': True,
         # is translated to "Remove from meeting"
         'use_custom_back_transition_title_for': ("validated", ),
         # use "validate" as back transition to state "validated"
         'defined_back_transition_ids': {"validated": "validate"},
         # if () given, a custom transition icon is used for every back transitions
         'only_use_custom_back_transition_icon_for': ("validated", ),
         'use_custom_transition_title_for': {
            'wait_advices_from_proposed_to_director': 'wait_advices_proposed_to_finances', },
         'adviser_may_validate': True,
         'new_state_id': 'proposed_to_finance_waiting_advices',
         },
    ),
    'meeting-config-bourgmestre':
    (
        {'from_states': ('proposed_to_director', ),
         'back_states': ('proposed_to_director', ),
         'use_custom_icon': False,
         'use_custom_back_transition_title_for': (),
         # if () given, a custom transition icon is used for every back transitions
         'only_use_custom_back_transition_icon_for': ("dummy", ),
         # can not use custom_transition_title for wait_advices_from_proposed_to_director
         # as it is already used in College, see https://support.imio.be/browse/PM-3885
         'use_custom_transition_title_for': {
            'wait_advices_from_proposed_to_director': 'wait_advices_from_proposed_to_director', },
         'adviser_may_validate': False,
         'new_state_id': 'proposed_to_director_waiting_advices',
         },
    )
}
adaptations.WAITING_ADVICES_FROM_STATES.update(LIEGE_WAITING_ADVICES_FROM_STATES)
LIEGE_RESTRICT_ITEM_BACK_SHORTCUTS = {
    'meeting-config-bourgmestre':
    {
        '*': '*',
        'proposed_to_general_manager': [],
        'proposed_to_cabinet_reviewer': ['proposed_to_director'],
        'proposed_to_cabinet_manager': ['proposed_to_director'],
        'validated': ['proposed_to_director', 'proposed_to_cabinet_reviewer']
    }
}
adaptations.RESTRICT_ITEM_BACK_SHORTCUTS.update(LIEGE_RESTRICT_ITEM_BACK_SHORTCUTS)


class CustomMeeting(Meeting):
    '''Adapter that adapts a meeting implementing IMeeting to the
       interface IMeetingCustom.'''

    implements(IMeetingCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item
        self.tool = api.portal.get_tool('portal_plonemeeting')
        self.cfg = self.tool.getMeetingConfig(self.context)

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

    def getPrintableItemsByCategory(self, itemUids=[], list_types=['normal'],
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
        # Retrieve the list of items
        for elt in itemUids:
            if elt == '':
                itemUids.remove(elt)

        items = self.context.get_items(uids=itemUids, list_types=list_types, ordered=True)

        if withCollege:
            insertMethods = self.cfg.getInsertingMethodsOnAddItem()
            catalog = api.portal.get_tool('portal_catalog')
            brains = catalog(portal_type='MeetingCollege',
                             meeting_date={'query': self.context.date - 60,
                                           'range': 'min'},
                             sort_on='meeting_date',
                             sort_order='reverse')
            for brain in brains:
                obj = brain.getObject()
                isInNextCouncil = obj.getAdoptsNextCouncilAgenda()
                if obj.date < self.context.date and isInNextCouncil:
                    collegeMeeting = obj
                    break
            if collegeMeeting:
                collegeMeeting = collegeMeeting.getObject()
            collegeItems = collegeMeeting.get_items(ordered=True)
            itemList = []
            for collegeItem in collegeItems:
                if 'meeting-config-council' in collegeItem.getOtherMeetingConfigsClonableTo() and not \
                        collegeItem._checkAlreadyClonedToOtherMC('meeting-config-council'):
                    itemPrivacy = collegeItem.getPrivacyForCouncil()
                    itemProposingGroup = collegeItem.getProposingGroup()
                    collegeCat = collegeItem.getCategory(theObject=True)
                    councilCategoryId = collegeCat.category_mapping_when_cloning_to_other_mc
                    itemCategory = getattr(self.cfg.categories,
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
            councilItems = self.context.get_items(uids=itemUids, ordered=True)
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
                if item.query_state() in ignore_review_states:
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
                    currentCat = getattr(self.cfg.categories,
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
            allCategories = self.cfg.getCategories()
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

    def getItemsForAM(self, itemUids=[], list_types=['normal'],
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
        for category in self.cfg.getCategories(onlySelectable=False):
            lst.append(self.getPrintableItemsByCategory(itemUids=itemUids, list_types=list_types,
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
        brains = self.get_items(
            list_types=['normal'], ordered=True, the_objects=False, unrestricted=True)

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
        brains = self.get_items(
            list_types=['late'], ordered=True, the_objects=False, unrestricted=True)
        item_num = 1
        for brain in brains:
            res[brain.UID] = item_num
            item_num = item_num + 1
        ann['MeetingLiege-getItemNumsForActe']['nums'] = res.copy()
        ann._p_changed = True
        return res
    Meeting.getItemNumsForActe = getItemNumsForActe

    def getRepresentative(self, sublst, itemUids, privacy='public',
                          list_types=['normal'], oralQuestion='both', by_proposing_group=False,
                          withCollege=False, renumber=False, firstNumber=1):
        '''Checks if the given category is the same than the previous one. Return none if so and the new one if not.'''
        previousCat = ''
        for sublist in self.getPrintableItemsByCategory(itemUids, privacy=privacy, list_types=list_types,
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
        allCategories = self.cfg.getCategories(onlySelectable=False)
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
        allCategories = self.cfg.getCategories()
        categsId = [item.getId() for item in allCategories
                    if item.Title().split('.')[0] == numCateg]
        return categsId


old_checkAlreadyClonedToOtherMC = MeetingItem._checkAlreadyClonedToOtherMC


class CustomMeetingItem(MeetingItem):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCustom.'''
    implements(IMeetingItemCustom)
    security = ClassSecurityInfo()

    BOURGMESTRE_PROPOSING_GROUP_STATES = [
        'itemcreated',
        'proposed_to_administrative_reviewer',
        'proposed_to_internal_reviewer',
        'proposed_to_director',
        'proposed_to_director_waiting_advices']

    def __init__(self, item):
        self.context = item
        self.tool = api.portal.get_tool('portal_plonemeeting')
        self.cfg = self.tool.getMeetingConfig(self.context)

    def is_general_manager(self):
        """Is current user a general manager?"""
        return '{0}_reviewers'.format(gm_group_uid()) in get_plone_groups_for_user()

    def is_cabinet_manager(self):
        """Is current user a cabinet manager?"""
        return '{0}_creators'.format(bg_group_uid()) in get_plone_groups_for_user()

    def is_cabinet_reviewer(self):
        """Is current user a cabinet reviewer?"""
        return '{0}_reviewers'.format(bg_group_uid()) in get_plone_groups_for_user()

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
        if not item.attribute_is_used('otherMeetingConfigsClonableToEmergency'):
            return False

        hasStoredEmergencies = item.getOtherMeetingConfigsClonableToEmergency()
        return hasStoredEmergencies or \
            (item.showClonableToOtherMCs() and
             self.tool.isManager(self.cfg))

    security.declareProtected(ModifyPortalContent, 'setCategory')

    # we will monkeypatch MeetingItem.setCategory but we need to call original code
    MeetingItem.__old_pm_setCategory = MeetingItem.setCategory

    def setCategory(self, value, **kwargs):
        '''Overrides the field 'category' mutator to remove stored
           result of the Meeting.getItemNumsForActe on the corresponding meeting.
           If the category of an item in a meeting changed, invalidate also
           MeetingItem.getItemRefForActe ram cache.'''
        current = self.getField('category').get(self)
        meeting = self.getMeeting()
        # call original code
        self.__old_pm_setCategory(value, **kwargs)
        if current != value and meeting:
            ann = IAnnotations(meeting)
            if 'MeetingLiege-getItemNumsForActe' in ann:
                ann['MeetingLiege-getItemNumsForActe'] = {}
            cleanRamCacheFor('Products.MeetingLiege.adapters.getItemRefForActe')
    MeetingItem.setCategory = setCategory

    security.declarePublic('showAdvices')

    def showAdvices(self):
        """We show advices in every case on MeetingItemCollege and MeetingItemCouncil."""
        return True

    MeetingItem.__old_pm_show_budget_infos = MeetingItem.show_budget_infos

    security.declarePublic('show_budget_infos')

    def show_budget_infos(self):
        """Hide budget infos to the restrictedPowerObservers."""
        # call original code
        if self.__old_pm_show_budget_infos():
            tool = api.portal.get_tool('portal_plonemeeting')
            cfg = tool.getMeetingConfig(self)
            if not isPowerObserverForCfg(cfg, power_observer_types=['restrictedpowerobservers']):
                return True
    MeetingItem.show_budget_infos = show_budget_infos

    security.declarePublic('getExtraFieldsToCopyWhenCloning')

    def getExtraFieldsToCopyWhenCloning(self, cloned_to_same_mc, cloned_from_item_template):
        '''
          Keep some new fields when item is cloned (to another mc or from itemtemplate).
        '''
        res = ['financeAdvice', 'decisionEnd', 'toDiscuss']
        if cloned_to_same_mc:
            res = res + ['labelForCouncil', 'textCheckList',
                         'otherMeetingConfigsClonableToFieldLabelForCouncil']
        return res

    def getCustomAdviceMessageFor(self, advice):
        '''If we are on a finance advice that is still not giveable because
           the item is not 'complete', we display a clear message.'''
        item = self.getSelf()
        financial_group_uids = self.tool.finance_group_uids()
        if advice['id'] in financial_group_uids and \
           advice['delay'] and \
           not advice['delay_started_on']:
            # item in state giveable but item not complete
            item_state = item.query_state()
            if item_state in FINANCE_GIVEABLE_ADVICE_STATES:
                return {'displayDefaultComplementaryMessage': False,
                        'displayAdviceReviewState': True,
                        'customAdviceMessage':
                        translate('finance_advice_not_giveable_because_item_not_complete',
                                  domain="PloneMeeting",
                                  context=item.REQUEST)}
            elif getLastWFAction(item, 'wait_advices_from_proposed_to_director') and \
                item_state in ('itemcreated',
                               'itemcreated_waiting_advices',
                               'proposed_to_internal_reviewer',
                               'proposed_to_internal_reviewer_waiting_advices',
                               'proposed_to_director',):
                # advice was already given but item was returned back to the service
                return {'displayDefaultComplementaryMessage': False,
                        'displayAdviceReviewState': True,
                        'customAdviceMessage': translate(
                            'finance_advice_suspended_because_item_sent_back_to_proposing_group',
                            domain="PloneMeeting",
                            context=item.REQUEST)}
        res = self.context.getCustomAdviceMessageFor(advice)
        res['displayAdviceReviewState'] = True
        return res

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
            financial_group_uids = self.tool.finance_group_uids()
            for advice_uid, advice_info in item.adviceIndex.items():
                if advice_uid in financial_group_uids and not advice_info['optional']:
                    return advice_uid
        return None

    def _adviceIsEditable(self, org_uid):
        '''See doc in interfaces.py.'''
        item = self.getSelf()
        advice = item.getAdviceObj(org_uid)
        if advice.query_state() in ('financial_advice_signed', ):
            return False
        return True

    def _sendAdviceToGiveToGroup(self, org_uid):
        """Do not send an email to FINANCE_GROUP_IDS."""
        financial_group_uids = self.tool.finance_group_uids()
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
        # bypass for Managers
        if self.tool.isManager(realManagers=True):
            return True

        financeGroupId = item.adapted().getFinanceGroupUIDForItem()
        # a finance controller may evaluate if advice is actually asked
        # and may not change completeness if advice is currently given or has been given
        if not financeGroupId or \
           not '%s_financialcontrollers' % financeGroupId in get_plone_groups_for_user():
            return False

        # item must be still in a state where the advice can be given
        # and advice must still not have been given
        if not item.query_state() in FINANCE_GIVEABLE_ADVICE_STATES:
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
        # user must be able to edit the item and must have 'MeetingInternalReviewer'
        # or 'MeetingReviewer' role
        isReviewer, isInternalReviewer, isAdminReviewer = \
            self.context._roles_in_context()
        if not item.getCompleteness() == 'completeness_incomplete' or \
           not _checkPermission(ModifyPortalContent, item) or \
           not (isInternalReviewer or isReviewer or self.tool.isManager(self.cfg)):
            return False
        return True

    security.declarePublic('mayAskEmergency')

    def mayAskEmergency(self):
        '''Only directors may ask emergency.'''
        item = self.getSelf()
        isReviewer, isInternalReviewer, isAdminReviewer = \
            self.context._roles_in_context()
        if (item.query_state() == 'proposed_to_director' and isReviewer) or \
           self.tool.isManager(self.cfg):
            return True
        return False

    security.declarePublic('mayAcceptOrRefuseEmergency')

    def mayAcceptOrRefuseEmergency(self):
        '''Returns True if current user may accept or refuse emergency if asked for an item.
           Emergency can be accepted only by financial managers.'''
        # by default, only MeetingManagers can accept or refuse emergency
        if self.tool.isManager(realManagers=True) or \
           '%s_financialmanagers' % self.getFinanceGroupUIDForItem() in get_plone_groups_for_user():
            return True
        return False

    security.declarePublic('mayTakeOver')

    def mayTakeOver(self):
        '''Condition for editing 'takenOverBy' field.
           We still use default behaviour :
           A member may take an item over if he his able to change the review_state.
           But when the item is 'proposed_to_finance_waiting_advices', the item can be taken over by who can :
           - evaluate completeness;
           - add the advice;
           - change transition of already added advice.'''
        item = self.getSelf()
        if item.query_state() == 'proposed_to_finance_waiting_advices':
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
        '''TREASURY_GROUP_ID advice may be asked again by proposing group
           if it is accepted/accepted_but_modified.
           '''
        res = False
        # raise_on_error=False for tests
        if advice.advice_group == treasury_group_cec_uid() and \
           self.context.query_state() in ('accepted', 'accepted_but_modified'):
            org_uid = self.context.getProposingGroup()
            if org_uid in self.tool.get_orgs_for_user(
                    suffixes=['internalreviewers', 'reviewers'], the_objects=False):
                res = True
        else:
            res = self.context.mayAskAdviceAgain(advice)
        return res

    security.declarePrivate('listFinanceAdvices')

    def listFinanceAdvices(self):
        '''Vocabulary for the 'financeAdvice' field.'''
        res = []
        res.append(('_none_', translate('no_financial_impact',
                                        domain='PloneMeeting',
                                        context=self.REQUEST)))
        tool = api.portal.get_tool('portal_plonemeeting')
        financial_group_uids = tool.finance_group_uids()
        for finance_group_uid in financial_group_uids:
            res.append((finance_group_uid, get_organization(finance_group_uid).Title()))
        return DisplayList(tuple(res))
    MeetingItem.listFinanceAdvices = listFinanceAdvices

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
        res['comment'] = safe_encode(adviceData.get('comment') or '')
        advice_id = adviceData.get('advice_id')
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
            res = '%s' % item.getCategory(True).category_id
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
        return bool(self.tool.get_filtered_plone_groups_for_user(org_uids=[finance_group_id]))

    def mayGenerateFDAdvice(self):
        '''
          Returns True if the current user has the right to generate the
          Financial Director Advice template.
        '''
        adviceHolder = self.getItemWithFinanceAdvice()

        # do not generate if on an advice template
        if not adviceHolder.isDefinedInTool(item_type='itemtemplate') and \
           adviceHolder.getFinanceAdvice() != '_none_' and \
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
            predecessor = self.get_predecessor()
            while predecessor:
                if predecessor.query_state() == 'accepted_and_returned' and \
                   old_checkAlreadyClonedToOtherMC(predecessor, destMeetingConfigId):
                    # if item was sent to council, check that this item is not 'delayed' or 'returned'
                    councilClonedItem = predecessor.getItemClonedToOtherMC(destMeetingConfigId)
                    if councilClonedItem and not councilClonedItem.query_state() in ('delayed', 'returned'):
                        return True
                # break the loop if we encounter an item that was 'Duplicated and keep link'
                # and it is not an item that is 'accepted_and_returned'
                if getLastWFAction(predecessor, 'Duplicate and keep link'):
                    return res
                predecessor = predecessor.get_predecessor()
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
                    predecessor.query_state() in ('returned', )):
                return True
            # college item and predecessor college item in state ('accepted_returned', 'returned')
            if current.portal_type == 'MeetingItemCollege' and \
               (predecessor.portal_type == 'MeetingItemCollege' and
                    predecessor.query_state() in ('returned', 'accepted_and_returned')):
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
        predecessor = item.get_predecessor()
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
            predecessor = predecessor.get_predecessor()
        # either we found a valid predecessor, or we return self.context
        return item

    def getItemCollege(self):
        """Called on a Council item, will return the linked College item."""
        predecessor = self.context.get_predecessor()
        while predecessor and not predecessor.portal_type == 'MeetingItemCollege':
            predecessor = predecessor.get_predecessor()
        return predecessor

    def getLegalTextForFDAdvice(self, isMeeting=False):
        '''
        Helper method. Return legal text for each advice type.
        '''
        adviceHolder = self.getItemWithFinanceAdvice()
        adaptedAdviceHolder = adviceHolder.adapted()
        if not adaptedAdviceHolder.mayGenerateFDAdvice():
            return ''

        financialStuff = adaptedAdviceHolder.getFinancialAdviceStuff()
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
        rawDecisionEnd = item.getDecisionEnd(mimetype='text/plain').strip()
        if COUNCILITEM_DECISIONEND_SENTENCE_RAW not in rawDecisionEnd:
            return item.getDecisionEnd() + COUNCILITEM_DECISIONEND_SENTENCE
        else:
            return item.getDecisionEnd()

    def updateFinanceAdvisersAccess(self, old_local_roles={}):
        """ """
        item = self.getSelf()
        adapted = item.adapted()
        adapted._updateFinanceAdvisersAccessToAutoLinkedItems()
        adapted._updateFinanceAdvisersAccessToManuallyLinkedItems(old_local_roles)

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

        # avoid circular calls, avoid update_local_roles here under to enter further
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
        financial_group_uids = self.tool.finance_group_uids()
        potentialFinanceAccesses = set(["{0}_advisers".format(finance_advice_uid) for
                                        finance_advice_uid in financial_group_uids])
        financeInOldLocalRoles = potentialFinanceAccesses.intersection(set(old_local_roles.keys()))
        financeInNewLocalRoles = potentialFinanceAccesses.intersection(set(item.__ac_local_roles__.keys()))

        itemsToUpdate = []
        if financeInOldLocalRoles != financeInNewLocalRoles:
            # we need to update every linked items
            itemsToUpdate = linkedItems
        else:
            # just need to update newly linked items
            newUids = item.REQUEST.get('manuallyLinkedItems_newUids', [])
            if newUids:
                itemsToUpdate = [newItem for newItem in linkedItems
                                 if newItem.UID() in newUids]

        for itemToUpdate in itemsToUpdate:
            itemToUpdate.update_local_roles()
            for finance_access in finance_accesses:
                if finance_access not in itemToUpdate.__ac_local_roles__:
                    itemToUpdate.manage_addLocalRoles(finance_access, (READER_USECASES['advices'], ))
                    itemToUpdate.reindexObjectSecurity()

        # now we need removeUids to be updated too, we will call update_local_roles on removeUids
        removedUids = item.REQUEST.get('manuallyLinkedItems_removedUids', [])
        if removedUids:
            catalog = api.portal.get_tool('portal_catalog')
            for removeUid in removedUids:
                removedBrain = catalog.unrestrictedSearchResults(UID=removeUid)
                if removedBrain:
                    removedItem = removedBrain[0]._unrestrictedGetObject()
                    removedItem.update_local_roles()

        # cancel manuallyLinkedItems_... values
        # item.REQUEST.set('manuallyLinkedItems_newUids', [])
        # item.REQUEST.set('manuallyLinkedItems_removedUids', [])
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

    def _getAllGroupsManagingItem(self, review_state, theObjects=False):
        """For meeting-config-bourgmestre, include the proposingGroup,
           the general manager and the bourgmestre."""
        item = self.getSelf()
        res = [item.getProposingGroup(theObject=theObjects)]
        if item.portal_type == 'MeetingItemBourgmestre':
            if review_state not in self.BOURGMESTRE_PROPOSING_GROUP_STATES:
                org_uids = []
                org_uids.append(gm_group_uid())
                if review_state not in ['proposed_to_general_manager']:
                    org_uids.append(bg_group_uid())
                if theObjects:
                    res += uuidsToObjects(org_uids, unrestricted=True)
                else:
                    res += org_uids
        return res

    def _getGroupManagingItem(self, review_state, theObject=False):
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
                return theObject and \
                    uuidToObject(gm_group_uid(), unrestricted=True) or gm_group_uid()
            else:
                return theObject and \
                    uuidToObject(bg_group_uid(), unrestricted=True) or bg_group_uid()

    def _assign_roles_to_all_groups_managing_item_suffixes(self,
                                                           cfg,
                                                           item_state,
                                                           org_uids,
                                                           org_uid):
        """By default, every proposingGroup suffixes get the "Reader" role
           but we do not want the "observers" to get the "Reader" role."""
        item = self.getSelf()
        for managing_org_uid in org_uids:
            suffix_roles = {suffix: ['Reader'] for suffix in
                            get_all_suffixes(managing_org_uid)
                            if suffix != 'observers'}
            item._assign_roles_to_group_suffixes(managing_org_uid, suffix_roles)

    def getOfficeManager(self):
        '''
        Allows to get the office manager's name, even if the item is
        returned multiple times.
        '''
        # If we have the name of the office manager, we just return it.
        if getLastWFAction(self.context, 'proposeToDirector'):
            offMan = getLastWFAction(self.context, 'proposeToDirector')['actor']
        # Else we look for a predecessor which can have the intel.
        elif self.context.get_predecessor():
            offMan = ''
            predecessor = self.context.get_predecessor()
            # loops while the item has no office manager
            while predecessor and not offMan:
                if getLastWFAction(predecessor, 'proposeToDirector'):
                    offMan = getLastWFAction(predecessor, 'proposeToDirector')['actor']
                predecessor = predecessor.get_predecessor()
        else:
            return ''

        user = {}
        membershipTool = api.portal.get_tool('portal_membership')
        user['fullname'] = membershipTool.getMemberInfo(str(offMan))['fullname']
        memberInfos = membershipTool.getMemberById(offMan)
        user['phone'] = memberInfos.getProperty('description').split("     ")[0]
        user['email'] = memberInfos.getProperty('email')
        return user

    def treasuryCopyGroup(self):
        """Manage fact that group TREASURY_GROUP_ID _observers must be automatically
           set as copyGroup of items for which the finances advice was asked.
           It will have access from the 'validated' and 'sent_to_council_emergency'
           state and beyond.
           This is used in the MeetingGroup.asCopyGroupOn field."""
        item = self.getSelf()
        if item.getFinanceAdvice() != '_none_' and \
           item.getProposingGroup() not in not_copy_group_uids() and \
           (item.query_state() in ('validated', 'sent_to_council_emergency') or item.hasMeeting()):
            return ['incopy']
        else:
            return []

    def _roles_in_context_cachekey(method, self):
        '''cachekey method for self._roles_in_context.'''
        user_id = get_current_user_id(self.REQUEST)
        date = get_cachekey_volatile('_users_groups_value')
        return (self.getProposingGroup(), user_id, date)

    @ram.cache(_roles_in_context_cachekey)
    def _roles_in_context(self):
        ''' '''
        user_plone_groups = get_plone_groups_for_user()
        proposingGroupUID = self.getProposingGroup()
        isReviewer = get_plone_group_id(proposingGroupUID, 'reviewers') in user_plone_groups
        isInternalReviewer = get_plone_group_id(proposingGroupUID, 'internalreviewers') in user_plone_groups
        isAdminReviewer = get_plone_group_id(proposingGroupUID, 'administrativereviewers') in user_plone_groups
        return isReviewer, isInternalReviewer, isAdminReviewer
    MeetingItem._roles_in_context = _roles_in_context

    def _annex_decision_addable_states_after_validation(self, cfg, item_state):
        """Decision annex may be added in every states for every MeetingConfig."""
        return "*"


class CustomMeetingConfig(MeetingConfig):
    '''Adapter that adapts a meetingConfig implementing IMeetingConfig to the
       interface IMeetingConfigCustom.'''

    implements(IMeetingConfigCustom)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    def _extraSearchesInfo(self, infos):
        """Add some specific searches."""
        cfg = self.getSelf()
        extra_infos = OrderedDict(
            [
                # Items in state 'proposed_to_finance_waiting_advices' for which
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
        # add the 'searchitemswithfinanceadvice' for 'College'
        # use shortName because in test, id is generated to avoid multiple same id
        if cfg.getShortName() in ('College'):
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
                            'tal_condition': "python: tool.isFinancialUser() or tool.isManager(cfg)",
                            'roles_bypassing_talcondition': ['Manager', ]
                        }
                     ),
                ]
            )
            infos.update(finance_infos)
        return infos

    def _adviceConditionsInterfaceFor(self, advice_obj):
        '''See doc in interfaces.py.'''
        if advice_obj.portal_type == 'meetingadvicefinances':
            return IMeetingAdviceFinancesWorkflowConditions.__identifier__
        else:
            return super(CustomMeetingConfig, self)._adviceConditionsInterfaceFor(advice_obj)

    def _adviceActionsInterfaceFor(self, advice_obj):
        '''See doc in interfaces.py.'''
        if advice_obj.portal_type == 'meetingadvicefinances':
            return IMeetingAdviceFinancesWorkflowActions.__identifier__
        else:
            return super(CustomMeetingConfig, self)._adviceActionsInterfaceFor(advice_obj)

    def extra_item_decided_states(self):
        ''' '''
        return ['accepted_and_returned', 'returned']

    def _custom_reviewersFor(self):
        '''Manage reviewersFor Bourgmestre because as some 'creators' suffixes are
           used after reviewers levels, this break the _highestReviewerLevel and other
           related hierarchic level functionalities.
           This is done so order is correct for 'creators'.'''
        cfg = self.getSelf()
        if cfg.getId() == 'meeting-config-bourgmestre':
            return OrderedDict(
                [
                    ('reviewers',
                     ['proposed_to_director',
                      'proposed_to_general_manager',
                      'proposed_to_cabinet_reviewer']),
                    ('internalreviewers',
                     ['proposed_to_internal_reviewer']),
                    ('administrativereviewers',
                     ['proposed_to_administrative_reviewer']),
                    ('creators',
                     ['proposed_to_cabinet_manager'])
                ]
            )


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
        return tool.userIsAmong(FINANCE_GROUP_SUFFIXES)
    ToolPloneMeeting.isFinancialUser = isFinancialUser

    def finance_group_uids(self):
        """ """
        return finance_group_uids()
    ToolPloneMeeting.finance_group_uids = finance_group_uids

    security.declarePublic('isUrbanismUser')

    def isUrbanismUser(self):
        '''
        Is current user an urbanism user, so in groups 'urba-gestion-administrative',
        urba-affaires-ga-c-na-c-rales', 'urba-service-de-lurbanisme',
        'urbanisme-et-ama-c-nagement-du-territoire',
        'echevinat-de-la-culture-et-de-lurbanisme' or 'urba'
        '''
        userGroups = set(self.context.get_orgs_for_user(the_objects=False))
        allowedGroups = set(['urba-gestion-administrative',
                             'urba-affaires-ga-c-na-c-rales',
                             'urba-service-de-lurbanisme',
                             'urbanisme-et-ama-c-nagement-du-territoire',
                             'echevinat-de-la-culture-et-de-lurbanisme',
                             'urba'])
        if userGroups.intersection(allowedGroups):
            return True
        return False

    def performCustomWFAdaptations(
            self, meetingConfig, wfAdaptation, logger, itemWorkflow, meetingWorkflow):
        ''' '''
        if wfAdaptation == 'returned':
            _addDecidedState(new_state_id='returned',
                             transition_id='return',
                             itemWorkflow=itemWorkflow)
            return True
        elif wfAdaptation == 'accepted_and_returned':
            _addDecidedState(new_state_id='accepted_and_returned',
                             transition_id='accept_and_return',
                             itemWorkflow=itemWorkflow)
            return True
        elif wfAdaptation == 'sent_to_council_emergency':
            _addIsolatedState(
                new_state_id='sent_to_council_emergency',
                origin_state_id='validated',
                origin_transition_id='sendToCouncilEmergency',
                origin_transition_guard_expr_name='maySendToCouncilEmergency()',
                back_transition_guard_expr_name="mayCorrect('validated')",
                back_transition_id='backToValidatedFromSentToCouncilEmergency',
                itemWorkflow=itemWorkflow)
            return True
        return False

    def extraAdviceTypes(self):
        '''See doc in interfaces.py.'''
        return ("positive_finance", "positive_with_remarks_finance",
                "negative_finance", "not_required_finance")


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


class MeetingItemCollegeLiegeWorkflowActions(MeetingItemWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCollegeWorkflowActions'''

    implements(IMeetingItemCollegeLiegeWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doWait_advices_from')

    def doWait_advices_from(self, stateChange):
        '''When an item is proposed to finance again, make sure the item
           completeness si no more in ('completeness_complete', 'completeness_evaluation_not_required')
           so advice is not addable/editable when item come back again to the finance.'''
        if stateChange.new_state.id == 'proposed_to_finance_waiting_advices':
            # if we found an event 'wait_advices_from_proposed_to_director' in workflow_history,
            # it means that item is proposed again to the finances and we need to ask completeness
            # evaluation again current transition 'wait_advices_from_proposed_to_director'
            # is already in workflow_history...
            wfTool = api.portal.get_tool('portal_workflow')
            # take history but leave last event apart
            history = self.context.workflow_history[wfTool.getWorkflowsFor(self.context)[0].getId()][:-1]
            # if we find ' wait_advices_from_proposed_to_director' in previous actions,
            # then item is proposed to finance again
            for event in history:
                if event['action'] == 'wait_advices_from_proposed_to_director':
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

    def get_waiting_advices_icon_infos(self):
        """Use custom icon when waiting finances advice."""
        res = super(MeetingItemCollegeLiegeWorkflowConditions, self).get_waiting_advices_icon_infos()
        if self.review_state == 'proposed_to_finance_waiting_advices':
            res = ('wait_advices_from_proposed_to_director.png', res[1])
        return res

    security.declarePublic('mayWait_advices')

    def mayWait_advices(self, from_state, destination_state):
        """ """
        res = super(MeetingItemCollegeLiegeWorkflowConditions, self).mayWait_advices(
            from_state, destination_state)
        if res and \
           from_state == "itemcreated" and \
           destination_state == "proposed_to_internal_reviewer_waiting_advices":
            # only internal reviewers and reviewers may ask
            isReviewer, isInternalReviewer, isAdminReviewer = \
                self.context._roles_in_context()
            if not (isReviewer or isInternalReviewer or self.tool.isManager(self.cfg)):
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
            res = True
        elif _checkPermission(ReviewPortalContent, self.context):
            res = True
            finance_advice = self.context.adapted().getFinanceGroupUIDForItem()
            # if the current item state is 'itemcreated', only the MeetingManager can validate
            if self.review_state == 'itemcreated':
                if not self.tool.isManager(self.cfg):
                    res = False
            # special case for item having finance advice that was still under redaction when delay timed out
            # a MeetingManager mut be able to validate it
            elif self.review_state in ['proposed_to_finance_waiting_advices', 'proposed_to_director', ] and \
                    finance_advice and self.context._adviceDelayIsTimedOut(finance_advice):
                res = True
            # director may validate an item if no finance advice
            # or finance advice and emergency is asked
            elif self.review_state == 'proposed_to_director' and \
                    finance_advice and \
                    self.context.getEmergency() == 'no_emergency':
                res = False
            # special case for item being validable when emergency is asked on it
            elif self.review_state == 'proposed_to_finance_waiting_advices' and \
                    self.context.getEmergency() == 'no_emergency':
                res = False
            else:
                # common checks, including required data and last validation level
                res = super(MeetingItemCollegeLiegeWorkflowConditions, self).mayValidate()
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
           meeting and meeting.adapted().is_decided():
            res = True
        return res

    security.declarePublic('mayAcceptAndReturn')

    def mayAcceptAndReturn(self):
        ''' '''
        return self.mayDecide()

    def _currentUserIsAdviserAbleToSendItemBackExtraCondition(self, org_uid, destinationState):
        ''' '''
        # an adviser may not send back an item to the director, the transition
        # exists to be triggered automatically
        if destinationState == 'proposed_to_director':
            return False
        return True

    def _userIsPGMemberAbleToSendItemBackExtraCondition(self, org_uid, destinationState):
        ''' '''
        # avoid being able for directors to take back a complete item when sent to finances
        if self.review_state == 'proposed_to_finance_waiting_advices' and \
                self.context.adapted()._is_complete():
            return False
        return True

    security.declarePublic('mayCorrect')

    def mayCorrect(self, destinationState=None):
        '''See docstring in interfaces.py'''
        res = False
        if destinationState == 'itemcreated':
            res = self._mayBackToItemCreated(destinationState)
        elif destinationState == 'proposed_to_internal_reviewer':
            res = self._mayBackToProposedToInternalReviewer(destinationState)
        elif destinationState == 'proposed_to_director':
            res = self._mayBackToProposedToDirector(destinationState)
        else:
            res = super(MeetingItemCollegeLiegeWorkflowConditions, self).mayCorrect(
                destinationState)
        return res

    def _mayBackToItemCreated(self, destinationState):
        '''
            A proposedToDirector item may be directly sent back to the
            'itemCreated' state if the user is reviewer and there are no
            administrative or internal reviewers.
        '''
        res = False
        # special case when automatically sending back an item to 'itemcreated' or
        # 'proposed_to_internal_reviewer' when every advices are given (coming from waiting_advices)
        if self.context.REQUEST.get('everyAdvicesAreGiven', False) and \
                self.review_state == 'itemcreated_waiting_advices':
            res = True
        else:
            res = super(MeetingItemCollegeLiegeWorkflowConditions, self).mayCorrect(
                destinationState)
        return res

    def _mayBackToProposedToInternalReviewer(self, destinationState):
        '''
            An item can be sent back to internal reviewer if it is
            proposed to director. The transition is only available
            if there is an internal reviewer.
        '''
        res = False
        # special case for financial controller that can send an item back to
        # the internal reviewer if it is in state 'proposed_to_finance_waiting_advices' and
        # item is incomplete
        item_state = self.context.query_state()
        if item_state == 'proposed_to_finance_waiting_advices' and not self.tool.isManager(self.cfg):
            # user must be a member of the finance group the advice is asked to
            financeGroupId = self.context.adapted().getFinanceGroupUIDForItem()
            memberGroups = get_plone_groups_for_user()
            for suffix in FINANCE_GROUP_SUFFIXES:
                financeSubGroupId = get_plone_group_id(financeGroupId, suffix)
                if financeSubGroupId in memberGroups:
                    res = True
                    break
        # special case when automatically sending back an item to 'proposed_to_internal_reviewer'
        # when every advices are given (coming from waiting_advices)
        elif self.context.REQUEST.get('everyAdvicesAreGiven', False) and \
                item_state == 'proposed_to_internal_reviewer_waiting_advices':
            return True
        else:
            res = super(MeetingItemCollegeLiegeWorkflowConditions, self).mayCorrect(
                destinationState)
        return res

    def _mayBackToProposedToDirector(self, destinationState):
        '''
          Item may back to proposedToDirector if a value 'mayBackToProposedToDirector' is
          found and True in the REQUEST.  It means that the item is 'proposed_to_finance_waiting_advices'
          and that the freshly signed advice was negative.
          It is also the case for MeetingItemBourgmestre if 'everyAdvicesAreGiven' found
          and True in the REQUEST.
          If the item is 'validated', a MeetingManager can send it back to the director.
        '''
        res = False
        item_state = self.context.query_state()
        if self.context.REQUEST.get('mayBackToProposedToDirector', False):
            res = True
        # special case when automatically sending back an item to 'proposed_to_director'
        # when every advices are given (coming from waiting_advices)
        elif (self.context.REQUEST.get('everyAdvicesAreGiven', False) and
              item_state == 'proposed_to_director_waiting_advices'):
            res = True
        # bypass for (Meeting)Managers
        elif self.tool.isManager(self.cfg):
            res = True
        else:
            res = super(MeetingItemCollegeLiegeWorkflowConditions, self).mayCorrect(
                destinationState)
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


class MeetingItemCouncilLiegeWorkflowActions(MeetingItemWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCouncilWorkflowActions'''

    implements(IMeetingItemCouncilLiegeWorkflowActions)
    security = ClassSecurityInfo()

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


class MeetingItemCouncilLiegeWorkflowConditions(MeetingItemWorkflowConditions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCouncilWorkflowConditions'''

    implements(IMeetingItemCouncilLiegeWorkflowConditions)
    security = ClassSecurityInfo()

    security.declarePublic('mayDecide')

    def mayDecide(self):
        '''We may decide an item if the linked meeting is in relevant state.'''
        res = False
        meeting = self.context.getMeeting()
        if _checkPermission(ReviewPortalContent, self.context) and \
           meeting and (meeting.query_state() in ['decided', 'closed', ]):
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
            # if item is itemcreated, only Cabinet Manager
            # may propose to cabinet reviewer directly
            if self.context.query_state() == 'itemcreated' and \
               not self.context.adapted().is_cabinet_manager():
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


class MeetingAdviceFinancesWorkflowActions(MeetingAdviceWorkflowActions):
    ''' '''

    implements(IMeetingAdviceFinancesWorkflowActions)
    security = ClassSecurityInfo()

    security.declarePrivate('doProposeToFinancialReviewer')

    def doProposeToFinancialReviewer(self, stateChange):
        ''' '''
        pass

    security.declarePrivate('doProposeToFinancialManager')

    def doProposeToFinancialManager(self, stateChange):
        ''' '''
        pass

    security.declarePrivate('doSignFinancialAdvice')

    def doSignFinancialAdvice(self, stateChange):
        ''' '''
        pass


class MeetingAdviceFinancesWorkflowConditions(MeetingAdviceWorkflowConditions):
    ''' '''

    implements(IMeetingAdviceFinancesWorkflowConditions)
    security = ClassSecurityInfo()

    security.declarePublic('mayProposeToFinancialReviewer')

    def mayProposeToFinancialReviewer(self):
        '''
        '''
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayProposeToFinancialManager')

    def mayProposeToFinancialManager(self):
        ''' '''
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('maySignFinancialAdvice')

    def maySignFinancialAdvice(self):
        '''A financial reviewer may sign the advice if it is 'positive_finance'
           or 'not_required_finance', if not this will be the financial manager
           that will be able to sign it.'''
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
            # if 'negative_finance', only finance manager can sign,
            # aka advice must be in state 'proposed_to_finance_waiting_advices_manager'
            if self.context.advice_type == 'negative_finance' and not \
               self.context.query_state() == 'proposed_to_financial_manager':
                res = False
        return res


old_get_advice_given_on = MeetingAdvice.get_advice_given_on


def get_advice_given_on(self):
    '''Monkeypatch the meetingadvice.get_advice_given_on method, if it is
       a finance advice, we will return date of last transition 'sign_advice'.'''
    tool = api.portal.get_tool('portal_plonemeeting')
    financial_group_uids = tool.finance_group_uids()
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
InitializeClass(CustomMeetingConfig)
InitializeClass(CustomMeetingItem)
InitializeClass(CustomToolPloneMeeting)
InitializeClass(MeetingAdviceFinancesWorkflowActions)
InitializeClass(MeetingAdviceFinancesWorkflowConditions)
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
    @ram.cache(query_user_groups_cachekey)
    def query_itemstocontrollcompletenessof(self):
        '''Queries all items for which there is completeness to evaluate, so where completeness
           is not 'completeness_complete'.'''
        if not self.cfg:
            return {}
        groupIds = []
        userGroups = get_plone_groups_for_user()
        financial_group_uids = self.tool.finance_group_uids()
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
                'review_state': {'query': 'proposed_to_finance_waiting_advices'}}

    # we may not ram.cache methods in same file with same name...
    query = query_itemstocontrollcompletenessof


class ItemsWithAdviceProposedToFinancialControllerAdapter(CompoundCriterionBaseAdapter):

    @property
    @ram.cache(query_user_groups_cachekey)
    def query_itemswithadviceproposedtofinancialcontroller(self):
        '''Queries all items for which there is an advice in state 'proposed_to_financial_controller'.
           We only return items for which completeness has been evaluated to 'complete'.'''
        if not self.cfg:
            return {}
        groupIds = []
        userGroups = get_plone_groups_for_user()
        financial_group_uids = self.tool.finance_group_uids()
        for financeGroup in financial_group_uids:
            # only keep finance groupIds the current user is controller for
            if '%s_financialcontrollers' % financeGroup in userGroups:
                groupIds.append('delay__%s_proposed_to_financial_controller' % financeGroup)
        # Create query parameters
        return {'portal_type': {'query': self.cfg.getItemTypeName()},
                'getCompleteness': {'query': 'completeness_complete'},
                'indexAdvisers': {'query': groupIds}}

    # we may not ram.cache methods in same file with same name...
    query = query_itemswithadviceproposedtofinancialcontroller


class ItemsWithAdviceProposedToFinancialReviewerAdapter(CompoundCriterionBaseAdapter):

    @property
    @ram.cache(query_user_groups_cachekey)
    def query_itemswithadviceproposedtofinancialreviewer(self):
        '''Queries all items for which there is an advice in state 'proposed_to_financial_reviewer'.'''
        if not self.cfg:
            return {}
        groupIds = []
        userGroups = get_plone_groups_for_user()
        financial_group_uids = self.tool.finance_group_uids()
        for financeGroup in financial_group_uids:
            # only keep finance groupIds the current user is reviewer for
            if '%s_financialreviewers' % financeGroup in userGroups:
                groupIds.append('delay__%s_proposed_to_financial_reviewer' % financeGroup)
        return {'portal_type': {'query': self.cfg.getItemTypeName()},
                'indexAdvisers': {'query': groupIds}}

    # we may not ram.cache methods in same file with same name...
    query = query_itemswithadviceproposedtofinancialreviewer


class ItemsWithAdviceProposedToFinancialManagerAdapter(CompoundCriterionBaseAdapter):

    @property
    @ram.cache(query_user_groups_cachekey)
    def query_itemswithadviceproposedtofinancialmanager(self):
        '''Queries all items for which there is an advice in state 'proposed_to_financial_manager'.'''
        if not self.cfg:
            return {}
        groupIds = []
        userGroups = get_plone_groups_for_user()
        financial_group_uids = self.tool.finance_group_uids()
        for financeGroup in financial_group_uids:
            # only keep finance groupIds the current user is manager for
            if '%s_financialmanagers' % financeGroup in userGroups:
                groupIds.append('delay__%s_proposed_to_financial_manager' % financeGroup)
        return {'portal_type': {'query': self.cfg.getItemTypeName()},
                'indexAdvisers': {'query': groupIds}}

    # we may not ram.cache methods in same file with same name...
    query = query_itemswithadviceproposedtofinancialmanager


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

        # Add our icons for some review states
        if self.itemState == 'accepted_and_returned':
            icons.append(('accepted_and_returned.png',
                          translate('icon_help_accepted_and_returned',
                                    domain="PloneMeeting",
                                    context=self.request)))
        elif self.itemState == 'returned':
            icons.append(('returned.png',
                          translate('icon_help_returned',
                                    domain="PloneMeeting",
                                    context=self.request)))

        # add an icon if College item is down the workflow from the finances
        # if item was ever gone the finances and now it is down to the
        # proposingGroup, then it is considered as down the wf from the finances
        # take into account every states before 'validated/proposed_to_finance_waiting_advices'
        if self.context.portal_type == 'MeetingItemCollege' and \
           self.itemState in self.cfg.getItemWFValidationLevels(data='state', only_enabled=True) and \
           getLastWFAction(self.context, 'wait_advices_from_proposed_to_director'):
            icons.append(('wf_down_finances.png',
                         translate('icon_help_wf_down_finances',
                                   domain="PloneMeeting",
                                   context=self.request)))
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
