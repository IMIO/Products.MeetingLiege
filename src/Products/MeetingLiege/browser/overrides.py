from Products.CMFCore.utils import getToolByName
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

        if not super(MeetingLiegeAdviceDelaysView, self)._mayEditDelays(isAutomatic):
            # maybe a financialmanager may change delay
            # that member may change delay if advice still addable/editable
            financeGroupId = self.context.adapted().getFinanceGroupIdsForItem()
            if not financeGroupId:
                return False

            if not self.context.adviceIndex[financeGroupId]['advice_addable'] and \
               not self.context.adviceIndex[financeGroupId]['advice_editable']:
                return False

            # current advice is still addable/editable, a finance manager may change delay for it
            member = getToolByName(self.context, 'portal_membership').getAuthenticatedMember()
            financialManagerGroupId = '%s_financialmanagers' % financeGroupId
            if not financialManagerGroupId in member.getGroups():
                return False

        return True
