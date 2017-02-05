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


class MLItemCategorizedObjectAdapter(PMCategorizedObjectAdapter):
    """ """

    def __init__(self, context, request, brain):
        super(PMCategorizedObjectAdapter, self).__init__(context, request, brain)

    def can_view(self):
        res = super(MLItemCategorizedObjectAdapter, self).can_view()
        if not res:
            return res

        # if user may see and isPowerObserver, double check for normal annexes (not decision annexes
        # that are all viewable when isPowerObserver
        # power observer may only access annexes of items using the categories
        # they are in charge of and annexes using type 'annexeCahier' or 'courrier-a-valider-par-le-college'
        if self.brain.portal_type == 'annex':
            infos = self.context.categorized_elements[self.brain.UID]
            tool = api.portal.get_tool('portal_plonemeeting')
            cfg = tool.getMeetingConfig(self.context)
            isPowerObserver = tool.isPowerObserverForCfg(cfg, isRestricted=False)
            extraViewableAnnexTypeIds = ('annexeCahier', 'courrier-a-valider-par-le-college')
            if isPowerObserver and infos['category_id'] not in extraViewableAnnexTypeIds:
                cat = self.context.getCategory(True)
                if not cat or not cat.meta_type == 'MeetingCategory':
                    return False
                for groupOfMatter in cat.getGroupsOfMatter():
                    groupId = '%s_observers' % groupOfMatter
                    if groupId in self._user_groups():
                        return True
                return False
        return True
