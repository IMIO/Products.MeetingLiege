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
from plone.memoize.instance import memoize
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
        if self.context.advice_group not in FINANCE_GROUP_IDS:
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
                    previousEvent = getPreviousEvent(
                        self.context, event, checkMayViewEvent=False, checkMayViewComment=False)
                    if previousEvent and previousEvent['review_state'] == 'proposed_to_finance':
                        return True
        return userMayAccessComment

    @memoize
    def _userIsInProposingGroup(self):
        """ """
        tool = api.portal.get_tool('portal_plonemeeting')
        return self.context.getProposingGroup(theObject=True) in tool.getGroupsForUser()

    @memoize
    def _is_general_manager(self):
        """ """
        return self.context.adapted().is_general_manager()

    @memoize
    def _is_cabinet_member(self):
        """ """
        return self.context.adapted().is_cabinet_manager() or self.context.adapted().is_cabinet_reviewer()

    @memoize
    def _build_history_with_previous_review_state(self):
        """ """
        history = self.get_history_data()
        res = []
        previous_event = None
        for event in history:
            new_event = event.copy()
            new_event['previous_review_state'] = previous_event and previous_event['review_state'] or None
            previous_event = new_event.copy()
            res.append(new_event)
        return res

    def mayViewEvent(self, event):
        """ """
        # key is the transition, value is the previous review_state it can not come from
        ADMINISTRATIVE_NOT_VIEWABLE_TRANSITIONS = {
            'proposeToCabinetManager': None,
            'backToProposedToGeneralManager': None,
            'proposeToCabinetReviewer': None,
            'backToProposedToCabinetManager': None,
            'validate': None,
            'backToProposedToCabinetReviewer': None}

        # key is the transition, value is the previous review_state it can not come from
        CABINET_NOT_VIEWABLE_TRANSITIONS = {
            'proposeToAdministrativeReviewer': None,
            'backToItemCreated': None,
            'proposeToInternalReviewer': None,
            'backToProposedToAdministrativeReviewer': None,
            'proposeToDirector': None,
            'backToProposedToInternalReviewer': None,
            'proposeToGeneralManager': None,
            'backToProposedToDirector': ['proposed_to_general_manager']}

        if event['action'] and self.context.portal_type == 'MeetingItemBourgmestre':
            tool = api.portal.get_tool('portal_plonemeeting')
            # MeetingManager bypass

            if tool.isManager(self.context) or self._is_general_manager():
                return True

            # is member of the proposingGroup?
            userIsInProposingGroup = self._userIsInProposingGroup()
            # is cabinet member?
            is_cabinet_member = self._is_cabinet_member()

            # in case user is in proposing group + cabinet member, he may see everything
            if userIsInProposingGroup and is_cabinet_member:
                return True

            # only in proposing group
            if userIsInProposingGroup:
                not_viewable_transitions = ADMINISTRATIVE_NOT_VIEWABLE_TRANSITIONS
            # only cabinet member
            elif is_cabinet_member:
                not_viewable_transitions = CABINET_NOT_VIEWABLE_TRANSITIONS
            else:
                return False

            # check for not_viewable_transitions transition
            history = self._build_history_with_previous_review_state()
            # find event in history
            event_with_previous_review_state = [
                elt for elt in history if event['time'] == elt['time']][0]
            action = event_with_previous_review_state['action']
            if action not in not_viewable_transitions:
                return True

            previous_review_state = event_with_previous_review_state['previous_review_state']
            forbidden_previous_review_state = not_viewable_transitions[action]
            # if transition in not_viewable_transitions, it is viewable if previous_review_state
            # is not in forbidden_previous_review_state.  This manage fact that backTo transitions
            # may lead to a former state from various review_states
            if not forbidden_previous_review_state or previous_review_state in forbidden_previous_review_state:
                return False
        return True


class MLItemCategorizedObjectAdapter(PMCategorizedObjectAdapter):
    """ """

    def __init__(self, context, request, brain):
        super(PMCategorizedObjectAdapter, self).__init__(context, request, brain)

    def can_view(self):
        res = super(MLItemCategorizedObjectAdapter, self).can_view()
        if not res:
            return res

        # bypass for MeetingManagers
        tool = api.portal.get_tool('portal_plonemeeting')
        if tool.isManager(self.context):
            return True

        # if user may see and isPowerObserver, double check for normal annexes (not decision annexes)
        # that are all viewable when isPowerObserver
        # power observer may only access annexes of items using the categories
        # they are in charge of and annexes using type 'annexeCahier' or 'courrier-a-valider-par-le-college'
        if self.brain.portal_type == 'annex':
            infos = self.context.categorized_elements[self.brain.UID]
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
        # annexDecision marked as 'to_sign' are only viewable to (Meeting)Managers
        elif self.brain.portal_type == 'annexDecision':
            infos = self.context.categorized_elements[self.brain.UID]
            if infos['signed_activated'] and infos['to_sign'] and not infos['signed']:
                return False
        return True
