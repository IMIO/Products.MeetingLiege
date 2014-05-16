from plone.memoize.view import memoize_contextless
from Products.PloneMeeting.browser.overrides import BaseActionsPanelView


class MeetingLiegeAdviceActionsPanelView(BaseActionsPanelView):
    """
      Specific actions displayed on a meetingadvice.
    """
    def __init__(self, context, request):
        super(MeetingLiegeAdviceActionsPanelView, self).__init__(context, request)
        self.SECTIONS_TO_RENDER = ['renderTransitions',
                                   'renderDelete',
                                   'renderEdit',
                                   'renderActions', ]

    def mayDelete(self):
        """
          Override, check if we have the relevant permission on the advice.
        """
        return self.member.has_permission('Delete objects', self.context)

    @memoize_contextless
    def _transitionsToConfirm(self):
        """
          Override, every transitions of the finance workflow will have to be confirmed (commentable).
        """
        toConfirm = ['meetingadvice.proposeToFinancialController',
                     'meetingadvice.proposeToFinancialReviewer',
                     'meetingadvice.proposeToFinancialManager', ]
        return toConfirm
