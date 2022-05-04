# -*- coding: utf-8 -*-

from imio.history.adapters import ImioWfHistoryAdapter
from plone import api
from plone.memoize.instance import memoize
from Products.PloneMeeting.adapters import PMCategorizedObjectAdapter
from Products.PloneMeeting.adapters import PMWfHistoryAdapter


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
        tool = api.portal.get_tool('portal_plonemeeting')
        if tool.isManager(realManagers=True):
            return True

        # if not a finance advice comment is viewable...
        financial_group_uids = tool.finance_group_uids()
        if self.context.advice_group not in financial_group_uids:
            return True

        # finance advice event, check if user is member of finance group
        if self.context.advice_group in tool.get_orgs_for_user(the_objects=False):
            return True
        return False


class ItemWfHistoryAdapter(PMWfHistoryAdapter):
    """
      Manage the the fact that a given user may see or not a comment in an item history.
    """

    @memoize
    def get_history_data(self):
        """We need previous_review_state for MeetingItemBourgmestre and MeetingItemCollege."""
        if self.context.portal_type in ('MeetingItemBourgmestre', 'MeetingItemCollege'):
            self.include_previous_review_state = True
        history_data = super(ItemWfHistoryAdapter, self).get_history_data()
        return history_data

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
            # so comments in the 'wait_advices_from_proposed_to_director' and comments made by finance in
            # the 'backToProposedToInternalReviewer' must be viewable.  Take care that for this
            # last event 'backToProposedToInternalReviewer' it could be done by the director and
            # we want only to show comment to the finance group when it is the finance group
            # that triggered the transition...
            if (event['action'] in ('backTo_proposed_to_internal_reviewer_from_waiting_advices',
                          'wait_advices_from_proposed_to_director') or
                event['previous_review_state'] == 'proposed_to_finance_waiting_advices') and \
               self.context.adapted().isCurrentUserInFDGroup(financeAdvice):
                userMayAccessComment = True
        return userMayAccessComment

    @memoize
    def _userIsInProposingGroup(self):
        """ """
        tool = api.portal.get_tool('portal_plonemeeting')
        return self.context.getProposingGroup() in tool.get_orgs_for_user(the_objects=False)

    @memoize
    def _is_general_manager(self):
        """ """
        return self.context.adapted().is_general_manager()

    @memoize
    def _is_cabinet_member(self):
        """ """
        return self.context.adapted().is_cabinet_manager() or self.context.adapted().is_cabinet_reviewer()

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
            'backToProposedToDirector': ['proposed_to_general_manager',
                                         'proposed_to_director_waiting_advices'],
            'askAdvicesByDirector': None, }

        if event['action'] and self.context.portal_type == 'MeetingItemBourgmestre':
            tool = api.portal.get_tool('portal_plonemeeting')
            # MeetingManager bypass

            if tool.isManager(self.cfg) or self._is_general_manager():
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
            if event['action'] not in not_viewable_transitions:
                return True

            previous_review_state = event['previous_review_state']
            forbidden_previous_review_state = not_viewable_transitions[event['action']]
            # if transition in not_viewable_transitions, it is viewable if previous_review_state
            # is not in forbidden_previous_review_state.  This manage fact that backTo transitions
            # may lead to a former state from various review_states
            if not forbidden_previous_review_state or previous_review_state in forbidden_previous_review_state:
                return False
        return True


class MLItemCategorizedObjectAdapter(PMCategorizedObjectAdapter):
    """ """

    def can_view(self):
        res = super(MLItemCategorizedObjectAdapter, self).can_view()
        if not res:
            return res

        # annexDecision marked as 'to_sign' are only viewable to (Meeting)Managers
        infos = self.context.categorized_elements[self.categorized_obj.UID()]
        if infos['portal_type'] == 'annexDecision':
            if infos['signed_activated'] and \
               infos['to_sign'] and \
               not infos['signed'] and \
               not self.tool.isManager(self.cfg):
                return False
        return res
