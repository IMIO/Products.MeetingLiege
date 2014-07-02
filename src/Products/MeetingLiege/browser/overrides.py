from plone.memoize.view import memoize_contextless
from Products.PloneMeeting.browser.overrides import BaseActionsPanelView
from Products.PloneMeeting.browser.advicechangedelay import AdviceDelaysView


class MeetingLiegeAdviceActionsPanelView(BaseActionsPanelView):
    """
      Specific actions displayed on a meetingadvice.
    """
    def __init__(self, context, request):
        super(MeetingLiegeAdviceActionsPanelView, self).__init__(context, request)

    @memoize_contextless
    def _transitionsToConfirm(self):
        """
          Override, every transitions of the finance workflow will have to be confirmed (commentable).
        """
        toConfirm = ['meetingadvice.proposeToFinancialController',
                     'meetingadvice.proposeToFinancialReviewer',
                     'meetingadvice.proposeToFinancialManager',
                     'meetingadvice.signAdvice',
                     'meetingadvice.backToProposedToFinancialController',
                     'meetingadvice.backToProposedToFinancialReviewer',
                     'meetingadvice.backToProposedToFinancialManager', ]
        return toConfirm


class MeetingLiegeAdviceDelaysView(AdviceDelaysView):
    '''Render the advice available delays HTML on the advices list.'''

    def _mayEditDelays(self, isAutomatic):
        '''Rules of original method applies but here, the _financialmanagers,
           may also change an advice delay in some cases.'''
        res = super(MeetingLiegeAdviceDelaysView, self)._mayEditDelays(isAutomatic)

        if not res:
            # maybe a financialmanager may change delay
            # that member may change delay if advice still addable/editable
            financeGroupId = self.context.adapted().getFinanceGroupIdsForItem()
            if not financeGroupId:
                return False
            toAdd, toEdit = self.context.getAdvicesGroupsInfosForUser()
            if not financeGroupId in [group[0] for group in toAdd] and \
               not financeGroupId in [group[0] for group in toEdit]:
                return False
            # current member may still add/edit finance advice, but is it a financialmanager?
            member = self.context.restrictedTraverse('@@plone_portal_state').member()
            financialManagerGroupId = '%s_financialmanagers' % financeGroupId
            if not financialManagerGroupId in member.getGroups():
                return False

        return True
