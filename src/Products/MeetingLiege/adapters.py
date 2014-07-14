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
from appy.gen import No
from AccessControl import getSecurityManager, ClassSecurityInfo
from Globals import InitializeClass
from zope.component import queryUtility
from zope.interface import implements
from zope.i18n import translate
from zope.schema.interfaces import IVocabularyFactory
from Products.CMFCore.permissions import ReviewPortalContent, ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.Archetypes import DisplayList
from Products.PloneMeeting.MeetingItem import MeetingItem, MeetingItemWorkflowConditions, MeetingItemWorkflowActions
from Products.PloneMeeting.config import NOT_GIVEN_ADVICE_VALUE
from Products.PloneMeeting.config import MEETING_GROUP_SUFFIXES
from Products.PloneMeeting.utils import checkPermission, prepareSearchValue
from Products.PloneMeeting.Meeting import MeetingWorkflowActions, MeetingWorkflowConditions, Meeting
from Products.PloneMeeting.MeetingConfig import MeetingConfig
from Products.PloneMeeting.MeetingGroup import MeetingGroup
from Products.PloneMeeting.interfaces import IMeetingCustom, IMeetingItemCustom, \
    IMeetingConfigCustom, IMeetingGroupCustom
from Products.MeetingLiege.interfaces import \
    IMeetingItemCollegeLiegeWorkflowConditions, IMeetingItemCollegeLiegeWorkflowActions,\
    IMeetingCollegeLiegeWorkflowConditions, IMeetingCollegeLiegeWorkflowActions, \
    IMeetingItemCouncilLiegeWorkflowConditions, IMeetingItemCouncilLiegeWorkflowActions,\
    IMeetingCouncilLiegeWorkflowConditions, IMeetingCouncilLiegeWorkflowActions
from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from Products.MeetingLiege.config import FINANCE_GROUP_SUFFIXES

# disable every wfAdaptations
customWfAdaptations = ()
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
                                    excludedCategories=[], firstNumber=1, renumber=False,
                                    includeEmptyCategories=False, includeEmptyGroups=False):
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
        res = []
        items = []
        previousCatId = None
        tool = getToolByName(self.context, 'portal_plonemeeting')
        # Retrieve the list of items
        for elt in itemUids:
            if elt == '':
                itemUids.remove(elt)
        items = self.context.getItemsInOrder(late=late, uids=itemUids)
        if by_proposing_group:
            groups = tool.getMeetingGroups()
        else:
            groups = None
        if items:
            for item in items:
                # Check if the review_state has to be taken into account
                if item.queryState() in ignore_review_states:
                    continue
                elif not (privacy == '*' or item.getPrivacy() == privacy):
                    continue
                elif not (oralQuestion == 'both' or item.getOralQuestion() == oralQuestion):
                    continue
                elif not (toDiscuss == 'both' or item.getToDiscuss() == toDiscuss):
                    continue
                elif categories and not item.getCategory() in categories:
                    continue
                elif excludedCategories and item.getCategory() in excludedCategories:
                    continue
                currentCat = item.getCategory(theObject=True)
                currentCatId = currentCat.getId()
                if currentCatId != previousCatId:
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
                    previousCatId = currentCatId
                else:
                    # Append the item to the same category
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
            #return a list of tuple with first element the number and second
            #element the item itself
            i = firstNumber
            res = []
            for item in items:
                res.append((i, item))
                i = i + 1
            items = res
        return res

    security.declarePublic('showAllItemsAtOnce')
    def showAllItemsAtOnce(self):
        '''Monkeypatch for hiding the allItemsAtOnce field.'''
        return False
    Meeting.showAllItemsAtOnce = showAllItemsAtOnce


class CustomMeetingItem(MeetingItem):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingItemCustom.'''
    implements(IMeetingItemCustom)
    security = ClassSecurityInfo()

    customItemPositiveDecidedStates = ('accepted', 'accepted_but_modified', )
    MeetingItem.itemPositiveDecidedStates = customItemPositiveDecidedStates
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

    def getExtraFieldsToCopyWhenCloning(self):
        '''
          Keep field 'labelForCouncil' when item is sent from college to council.
        '''
        return ['labelForCouncil', ]

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
        # Default PM item icons
        res = res + MeetingItem.getIcons(item, inMeeting, meeting)
        # Add our icons for some review states
        if itemState == 'accepted_but_modified':
            res.append(('accepted_but_modified.png', 'icon_help_accepted_but_modified'))
        elif itemState == 'pre_accepted':
            res.append(('pre_accepted.png', 'icon_help_pre_accepted'))
        elif itemState == 'itemcreated_waiting_advices':
            res.append(('askAdvicesByItemCreator.png', 'icon_help_itemcreated_waiting_advices'))
        elif itemState == 'proposed_to_administrative_reviewer':
            res.append(('proposeToAdministrativeReviewer.png', 'icon_help_proposed_to_administrative_reviewer'))
        elif itemState == 'proposed_to_internal_reviewer':
            res.append(('proposeToInternalReviewer.png', 'icon_help_proposed_to_internal_reviewer'))
        elif itemState == 'proposed_to_internal_reviewer_waiting_advices':
            res.append(('askAdvicesByInternalReviewer.png', 'icon_help_proposed_to_internal_reviewer_waiting_advices'))
        elif itemState == 'proposed_to_director':
            res.append(('proposeToDirector.png', 'icon_help_proposed_to_director'))
        elif itemState == 'proposed_to_finance':
            res.append(('proposeToFinance.png', 'icon_help_proposed_to_finance'))
        elif itemState == 'marked_not_applicable':
            res.append(('marked_not_applicable.png', 'icon_help_marked_not_applicable'))
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
        financeGroupId = item.adapted().getFinanceGroupIdsForItem()
        if not financeGroupId or not '%s_financialcontrollers' % financeGroupId in member.getGroups():
            return False
        # advice must not have been added, but must be addable
        toAdd, toEdit = item.getAdvicesGroupsInfosForUser()
        if not financeGroupId in [group[0] for group in toAdd]:
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
                member.has_role('MeetingReviewer', item) or tool.isManager()):
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
        if tool.isManager(realManagers=True) or \
           '%s_financialmanagers' % self.getFinanceGroupIdsForItem() in member.getGroups():
            return True
        return False

    security.declareProtected('Modify portal content', 'onDuplicated')
    def onDuplicated(self, original):
        '''When an item is sent to the Council, we need to initialize
           title and privacy from what was defined on the college item.'''
        item = self.getSelf()
        if original.portal_type == 'MeetingItemCollege' and item.portal_type == 'MeetingItemCouncil':
            # we just sent an item from college to council
            item.setPrivacy(original.getPrivacyForCouncil())

    security.declarePrivate('listArchivingRefs')
    def listArchivingRefs(self):
        '''Vocabulary for the 'archivingRef' field.'''
        res = []
        tool = getToolByName(self, 'portal_plonemeeting')
        cfg = tool.getMeetingConfig(self)
        userGroups = set(tool.getGroupsForUser())
        for ref in cfg.getArchivingRefs():
            # if ref is not active, continue
            if ref['active'] == '0':
                continue
            # if ref is restricted to some groups and current member is not member of, continue
            if ref['restrict_to_groups'] and not set(ref['restrict_to_groups']).intersection(userGroups):
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
          Method that returns True if current item need advice of
          given p_financeGroupId.  We will check if archiving reference
          selected on the item needs a finance advice regarding it's definition
          on the revant MeetingConfig.archivingRefs.
        '''
        item = self.getSelf()
        if item.getArchivingRef() == '_none_':
            return False
        tool = getToolByName(item, 'portal_plonemeeting')
        cfg = tool.getMeetingConfig(item)
        archRefData = cfg.adapted()._dataForArchivingRefRowId(item.getArchivingRef())
        if financeGroupId in archRefData['finance_advice']:
            return True
        return False


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

    security.declarePublic('searchItemsToValidate')
    def searchItemsToValidate(self, sortKey, sortOrder, filterKey, filterValue, **kwargs):
        '''See docstring in Products.PloneMeeting.MeetingConfig.
           We override it here because relevant groupIds and wf state are no the same...'''
        member = self.portal_membership.getAuthenticatedMember()
        groupIds = self.portal_groups.getGroupsForPrincipal(member)
        res = []
        for groupId in groupIds:
            if groupId.endswith('_reviewers'):
                # append group name without suffix
                res.append(groupId[:-10])
        # if we use pre_validation, the state in which are items to validate is 'prevalidated'
        # if not using the WFAdaptation 'pre_validation', the items are in state 'proposed'
        usePreValidationWFAdaptation = 'pre_validation' in self.getWorkflowAdaptations()
        params = {'portal_type': self.getItemTypeName(),
                  'getProposingGroup': res,
                  # XXX change by MeetingLiege
                  # 'review_state': usePreValidationWFAdaptation and ('prevalidated', ) or ('proposed', ),
                  'review_state': usePreValidationWFAdaptation and ('prevalidated', ) or ('proposed_to_director', ),
                  'sort_on': sortKey,
                  'sort_order': sortOrder
                  }
        # Manage filter
        if filterKey:
            params[filterKey] = prepareSearchValue(filterValue)
        # update params with kwargs
        params.update(kwargs)
        # Perform the query in portal_catalog
        return self.portal_catalog(**params)
    MeetingConfig.searchItemsToValidate = searchItemsToValidate

    security.declarePublic('searchItemsWithAdviceProposedToFinancialController')
    def searchItemsWithAdviceProposedToFinancialController(self, sortKey, sortOrder, filterKey, filterValue, **kwargs):
        '''Queries all items for which there is an advice in state 'proposed_to_financial_controller'.'''
        groupIds = []
        for financeGroup in FINANCE_GROUP_IDS:
            groupIds.append('delay__%s_proposed_to_financial_controller' % financeGroup)
        # Create query parameters
        params = {'Type': unicode(self.getItemTypeName(), 'utf-8'),
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
    MeetingConfig.searchItemsWithAdviceProposedToFinancialController = searchItemsWithAdviceProposedToFinancialController

    security.declarePublic('searchItemsWithAdviceProposedToFinancialReviewer')
    def searchItemsWithAdviceProposedToFinancialReviewer(self, sortKey, sortOrder, filterKey, filterValue, **kwargs):
        '''Queries all items for which there is an advice in state 'proposed_to_financial_reviewer'.'''
        groupIds = []
        for financeGroup in FINANCE_GROUP_IDS:
            groupIds.append('delay__%s_proposed_to_financial_reviewer' % financeGroup)
        # Create query parameters
        params = {'Type': unicode(self.getItemTypeName(), 'utf-8'),
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
        for financeGroup in FINANCE_GROUP_IDS:
            groupIds.append('delay__%s_proposed_to_financial_manager' % financeGroup)
        # Create query parameters
        params = {'Type': unicode(self.getItemTypeName(), 'utf-8'),
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
            group._createPloneGroup(groupSuffix)

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

class MeetingCollegeLiegeWorkflowActions(MeetingWorkflowActions):
    '''Adapter that adapts a meeting item implementing IMeetingItem to the
       interface IMeetingCollegeWorkflowActions'''

    implements(IMeetingCollegeLiegeWorkflowActions)
    security = ClassSecurityInfo()

    def _adaptEveryItemsOnMeetingClosure(self):
        """Helper method for accepting every items."""
        # Every item that is not decided will be automatically set to "accepted"
        for item in self.context.getAllItems():
            if item.queryState() == 'presented':
                self.context.portal_workflow.doActionFor(item, 'itemfreeze')
            if item.queryState() in ['itemfrozen', 'pre_accepted', ]:
                self.context.portal_workflow.doActionFor(item, 'accept')

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
        ''' '''
        pass

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
        if checkPermission(ReviewPortalContent, self.context) and self.context.hasAdvices(toGive=True):
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
        if checkPermission(ReviewPortalContent, self.context) and self.context.hasAdvices(toGive=True):
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
            the advice will be 'signed' by the finance group if the advice type is 'positive_finance' or 'not_required_finance'
            or it can be manually validated by the director if item emergency has been asked
            and motivated on the item.
        """
        res = False
        # very special case, we can bypass the guard if a 'mayValidate'
        # value is found to True in the REQUEST
        if self.context.REQUEST.get('mayValidate', False):
            return True
        tool = getToolByName(self.context, 'portal_plonemeeting')
        isManager = tool.isManager()
        item_state = self.context.queryState()
        # first of all, the use must have the 'Review portal content permission'
        if checkPermission(ReviewPortalContent, self.context):
            res = True
            # if the current item state is 'itemcreated', only the MeetingManager can validate
            if item_state == 'itemcreated' and not isManager:
                res = False
            # special case for item being validable when emergency is asked on it
            elif item_state == 'proposed_to_finance' and self.context.getEmergency() == 'no_emergency':
                res = False
            elif item_state == 'proposed_to_director':
                # check if item needs finance advice, if it is the case, the item
                # must be proposed to finance before being validated
                # except if finance already gave his advice and it was a negative advice
                # in this case, the item was sent back to the director that can 'validate' himself
                # the item with this negative finance advice
                finance_advice = self.context.adapted().getFinanceGroupIdsForItem()
                if finance_advice and not self.context.adviceIndex[finance_advice]['type'] == 'negative_finance':
                    res = False
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
            elif self.context.queryState() == 'proposed_to_finance' and \
                    self.context.getCompleteness() == 'completeness_incomplete':
                # user must be a controller of finance group the advice is asked to
                financeControllerGroupId = '%s_financialcontrollers' % self.context.adapted().getFinanceGroupIdsForItem()
                member = self.context.restrictedTraverse('@@plone_portal_state').member()
                if financeControllerGroupId in member.getGroups():
                    res = True
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

    def _adaptEveryItemsOnMeetingClosure(self):
        """Helper method for accepting every items."""
        # Every item that is not decided will be automatically set to "accepted"
        for item in self.context.getAllItems():
            if item.queryState() == 'presented':
                self.context.portal_workflow.doActionFor(item, 'itemfreeze')
            if item.queryState() in ['itemfrozen', 'pre_accepted', ]:
                self.context.portal_workflow.doActionFor(item, 'accept')

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


# ------------------------------------------------------------------------------
InitializeClass(CustomMeetingItem)
InitializeClass(CustomMeeting)
InitializeClass(CustomMeetingConfig)
InitializeClass(CustomMeetingGroup)
InitializeClass(MeetingCollegeLiegeWorkflowActions)
InitializeClass(MeetingCollegeLiegeWorkflowConditions)
InitializeClass(MeetingItemCollegeLiegeWorkflowActions)
InitializeClass(MeetingItemCollegeLiegeWorkflowConditions)
InitializeClass(MeetingCouncilLiegeWorkflowActions)
InitializeClass(MeetingCouncilLiegeWorkflowConditions)
InitializeClass(MeetingItemCouncilLiegeWorkflowActions)
InitializeClass(MeetingItemCouncilLiegeWorkflowConditions)
# ------------------------------------------------------------------------------
