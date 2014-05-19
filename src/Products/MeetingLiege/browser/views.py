from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.Five import BrowserView
from Products.CMFCore.permissions import ReviewPortalContent
from Products.PloneMeeting.utils import checkPermission
from Products.MeetingLiege.config import FINANCE_GROUP_IDS


class AdviceWFConditionsView(BrowserView):
    """
      This is a view that manage workflow guards for the advice.
      It is called by the guard_expr of meetingadvice workflow transitions.
    """
    security = ClassSecurityInfo()

    security.declarePublic('mayProposeToFinancialController')

    def mayProposeToFinancialController(self):
        '''Only relevant for finance groups.'''
        res = False
        if self.request.get('mayProposeToFinancialController', False) or \
           (checkPermission(ReviewPortalContent, self.context) and self.context.advice_group in FINANCE_GROUP_IDS):
                res = True
        return res

    security.declarePublic('mayBackToProposedToFinancialController')

    def mayBackToProposedToFinancialController(self):
        '''
        '''
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True  # At least at present
        return res

    security.declarePublic('mayProposeToFinancialReviewer')

    def mayProposeToFinancialReviewer(self):
        '''
        '''
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True  # At least at present
        return res

    security.declarePublic('mayBackToProposedToFinancialReviewer')

    def mayBackToProposedToFinancialReviewer(self):
        '''
        '''
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True  # At least at present
        return res

    security.declarePublic('mayProposeToFinancialManager')

    def mayProposeToFinancialManager(self):
        '''Only relevant if current advice_type is 'negative_finance'.'''
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True  # At least at present
            if not self.context.advice_type == 'negative_finance':
                res = False
        return res

    security.declarePublic('maySignFinancialAdvice')

    def maySignFinancialAdvice(self):
        '''A financial reviewer may sign the advice if it is 'positive_finance', if not
           this will be the financial manager that will be able to sign it.'''
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True  # At least at present
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
        if checkPermission(ReviewPortalContent, self.context):
            res = True  # At least at present
        return res

InitializeClass(AdviceWFConditionsView)
