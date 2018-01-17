from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.Five import BrowserView
from Products.CMFCore.permissions import ReviewPortalContent
from Products.CMFCore.utils import _checkPermission
from Products.MeetingLiege.config import ITEM_MAIN_INFOS_HISTORY


class MainInfosHistoryView(BrowserView):
    """ """

    def __call__(self, event_time):
        """ """
        for event in getattr(self.context, ITEM_MAIN_INFOS_HISTORY, []):
            if int(event['time']) == event_time:
                self.historized_data = event['historized_data']
                break
        return super(MainInfosHistoryView, self).__call__()


class AdviceWFConditionsView(BrowserView):
    """
      This is a view that manage workflow guards for the advice.
      It is called by the guard_expr of meetingadvice workflow transitions.
    """
    security = ClassSecurityInfo()

    security.declarePublic('mayBackToProposedToFinancialController')

    def mayBackToProposedToFinancialController(self):
        '''
        '''
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayProposeToFinancialReviewer')

    def mayProposeToFinancialReviewer(self):
        '''
        '''
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayBackToProposedToFinancialReviewer')

    def mayBackToProposedToFinancialReviewer(self):
        '''
        '''
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayProposeToFinancialManager')

    def mayProposeToFinancialManager(self):
        '''A financial manager may send the advice to the financial manager
           in any case (advice positive or negative).'''
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
            # aka advice must be in state 'proposed_to_finance_manager'
            if self.context.advice_type == 'negative_finance' and not \
               self.context.queryState() == 'proposed_to_financial_manager':
                res = False
        return res

    security.declarePublic('mayBackToProposedToFinancialManager')

    def mayBackToProposedToFinancialManager(self):
        '''
        '''
        res = False
        if _checkPermission(ReviewPortalContent, self.context):
            res = True
        return res


InitializeClass(AdviceWFConditionsView)
