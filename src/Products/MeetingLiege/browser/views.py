from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.Five import BrowserView


class AdviceWFConditionsView(BrowserView):
    """
      This is a view that manage workflow guards for the advice.
      It is called by the guard_expr of meetingadvice workflow transitions.
    """
    security = ClassSecurityInfo()

    def getFinanceGroups(self):
        '''
        '''
        return ['comptabilite', ]

    security.declarePublic('mayProposeToFinancialController')
    def mayProposeToFinancialController(self):
        '''
        '''
        if self.advice_group in self.getFinanceGroups():
            return True


InitializeClass(AdviceWFConditionsView)
