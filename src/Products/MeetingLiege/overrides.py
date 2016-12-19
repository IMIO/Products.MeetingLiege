# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
# File: overrides.py
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

from Products.CMFCore.utils import getToolByName
from plone import api
from imio.history.adapters import ImioWfHistoryAdapter
from imio.history.utils import getPreviousEvent
from Products.PloneMeeting.adapters import AnnexableAdapter
from Products.PloneMeeting.adapters import PMCategorizedObjectAdapter
from Products.PloneMeeting.adapters import PMWfHistoryAdapter
from Products.MeetingLiege.config import FINANCE_GROUP_IDS


class AdviceWfHistoryAdapter(ImioWfHistoryAdapter):
    """
      Manage the the fact that a given user may see or not a comment in an advice history.
    """

    def mayViewComment(self, event):
        '''
          If advice was given by a financial group, members of the financial group
          may access every comments but other member will be able to access a special event
          'historize_signed_advice_content' where we store the historized content of an advice
          that was signed.
        '''
        # bypass for real Managers
        tool = getToolByName(self.context, 'portal_plonemeeting')
        if tool.isManager(self.context, True):
            return True

        # if not a finance advice comment is viewable...
        if not self.context.advice_group in FINANCE_GROUP_IDS:
            return True

        # finance advice event, check if user is member of finance group
        userMeetingGroupIds = [mGroup.getId() for mGroup in tool.getGroupsForUser()]
        if self.context.advice_group in userMeetingGroupIds:
            return True
        return False


class ItemWfHistoryAdapter(PMWfHistoryAdapter):
    """
      Manage the the fact that a given user may see or not a comment in an item history.
    """
    def mayViewComment(self, event):
        """
          By default, comments are hidden to everybody outside the proposing group
          but here, we let comments between internal_reviewer, reviewer and
          finance adviser viewable by relevant users.
        """
        # call super mayViewComment, if it returns False, maybe
        # nevertheless user may see the comment
        userMayAccessComment = super(ItemWfHistoryAdapter, self).mayViewComment(event)
        financeAdvice = self.context.getFinanceAdvice()
        if not userMayAccessComment and financeAdvice != '_none_':
            # in case there is a finance advice asked comments of finance to internal_reviewer
            # and from director to finance must be viewable by the finance group
            # so comments in the 'proposeToFinance' and comments made by finance in
            # the 'backToProposedToInternalReviewer' must be viewable.  Take care that for this
            # last event 'backToProposedToInternalReviewer' it could be done by the director and
            # we want only to show comment to the finance group when it is the finance group
            # that triggered the transition...
            action = event['action']
            if action in ['backToProposedToInternalReviewer', 'proposeToFinance']:
                isCurrentUserInFDGroup = self.context.adapted().isCurrentUserInFDGroup(financeAdvice)
                if isCurrentUserInFDGroup and action == 'proposeToFinance':
                    return True
                else:
                    # check that it is the finance group that made the transition 'backToProposedToInternalReviewer'
                    previousEvent = getPreviousEvent(self.context, event, checkMayView=False)
                    if previousEvent and previousEvent['review_state'] == 'proposed_to_finance':
                        return True
        return userMayAccessComment


class MLCategorizedObjectAdapter(PMCategorizedObjectAdapter):
    """ """

    def __init__(self, context, request, brain):
        super(PMCategorizedObjectAdapter, self).__init__(context, request, brain)

    def can_view(self):
        res = super(MLCategorizedObjectAdapter).can_view()
        infos = self.context.categorized_elements[self.brain.UID]

        # not confidential, viewable
        # restricted power observers respect classic behavior
        tool = api.portal.get_tool('portal_plonemeeting')
        cfg = tool.getMeetingConfig(self.context)
        isRestrictedPowerObserver = tool.isPowerObserverForCfg(cfg, isRestricted=True)
        if not infos['confidential'] or isRestrictedPowerObserver:
            return res

        # every decision annexes are viewable by power observers
        isPowerObserver = tool.isPowerObserverForCfg(cfg, isRestricted=False)
        if infos['portal_type'] == 'annexDecision' and isPowerObserver:
            return res

        # not (restricted) power observers may access annexes
        if not isPowerObserver and not isRestrictedPowerObserver:
            return res

        # if user may see and isPowerObserver, double check
        # power observer may only access annexes of items using the categories
        # they are in charge of and annexes using type 'annexeCahier' or 'courrier-a-valider-par-le-college'
        extraViewableAnnexTypeIds = ('annexeCahier', 'courrier-a-valider-par-le-college')
        if res and isPowerObserver and not infos['category_id'] in extraViewableAnnexTypeIds:
            member = api.user.get_current()
            cat = self.context.getCategory(True)
            if not cat or not cat.meta_type == 'MeetingCategory':
                return res

            memberGroups = member.getGroups()
            res = False
            for groupOfMatter in cat.getGroupsOfMatter():
                groupId = '%s_observers' % groupOfMatter
                if groupId in memberGroups:
                    res = True
                    break
        return res


class MatterAwareAnnexableAdapter(AnnexableAdapter):
    """
      This overrides the AnnexableAdapter so power advisers have only access to annexes of items
      of their own categories.  So if default _isViewableForCurrentUser returns True,
      double check if we should not hide it anyway because current user is a power observer
      not in charge of the item matter (category).
    """

    def _isViewableForCurrentUser(self, cfg, isPowerObserver, isRestrictedPowerObserver, annexInfo):
        '''
          Power observers may only access annexes of items they are in charge of.
        '''
        res = super(MatterAwareAnnexableAdapter, self)._isViewableForCurrentUser(cfg,
                                                                                 isPowerObserver,
                                                                                 isRestrictedPowerObserver,
                                                                                 annexInfo)
        # not confidential, viewable
        # restricted power observers respect classic behavior
        if not annexInfo['isConfidential'] or isRestrictedPowerObserver:
            return res

        # every decision annexes are viewable by power observers
        if annexInfo['relatedTo'] == 'item_decision' and isPowerObserver:
            return res

        # not (restricted) power observers may access annexes
        if not isPowerObserver and not isRestrictedPowerObserver:
            return res

        # if user may see and isPowerObserver, double check
        # power observer may only access annexes of items using the categories
        # they are in charge of and annexes using type 'annexeCahier' or 'courrier-a-valider-par-le-college'
        extraViewableFileTypeIds = ('annexeCahier', 'courrier-a-valider-par-le-college')
        extraViewableFileTypeUids = []
        for extraViewableFileTypeId in extraViewableFileTypeIds:
            fileType = getattr(cfg.meetingfiletypes, extraViewableFileTypeId, None)
            if fileType:
                extraViewableFileTypeUids.append(fileType.UID())
        if res and isPowerObserver and not annexInfo['meetingFileTypeObjectUID'] in extraViewableFileTypeUids:
            # powerObservers may see annex using type
            membershipTool = getToolByName(self.context, 'portal_membership')
            member = membershipTool.getAuthenticatedMember()
            cat = self.context.getCategory(True)
            if not cat or not cat.meta_type == 'MeetingCategory':
                return res

            memberGroups = member.getGroups()
            res = False
            for groupOfMatter in cat.getGroupsOfMatter():
                groupId = '%s_observers' % groupOfMatter
                if groupId in memberGroups:
                    res = True
                    break
        return res
