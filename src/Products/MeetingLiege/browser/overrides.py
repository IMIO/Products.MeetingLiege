# -*- coding: utf-8 -*-
#
# File: overrides.py
#
# Copyright (c) 2015 by Imio.be
#
# GNU General Public License (GPL)
#

from plone.memoize.view import memoize_contextless
from plone import api

from Products.PloneMeeting.browser.advicechangedelay import AdviceDelaysView
from Products.PloneMeeting.browser.overrides import BaseActionsPanelView
from Products.PloneMeeting.browser.views import ItemDocumentGenerationHelperView


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
            member = api.user.get_current()
            financialManagerGroupId = '%s_financialmanagers' % financeGroupId
            if not financialManagerGroupId in member.getGroups():
                return False

        return True


class MLItemDocumentGenerationHelperView(ItemDocumentGenerationHelperView):
    """Specific printing methods used for item."""

    def _collegeAdministrativeReviewer(self):
        """Used on a council item : get the administrative reviewer of the College item."""
        collegeItem = self.context.adapted().getItemCollege()
        if collegeItem:
            event = collegeItem.getLastEvent('proposeToDirector')
            if event:
                return api.user.get(event['actor'])

    def printAdministrativeReviewerFullname(self):
        """Printed on a Council item : print fullname of administrative reviewer of College item."""
        reviewer = self._collegeAdministrativeReviewer()
        fullname = '-'
        if reviewer:
            fullname = reviewer.getProperty('fullname')
        return fullname

    def printAdministrativeReviewerTel(self):
        """Printed on a Council item : print tel of administrative reviewer of College item."""
        reviewer = self._collegeAdministrativeReviewer()
        tel = ''
        if reviewer:
            tel = reviewer.getProperty('description').split('     ')[0]
        return tel

    def printAdministrativeReviewerEmail(self):
        """Printed on a Council item : print email of administrative reviewer of College item."""
        reviewer = self._collegeAdministrativeReviewer()
        email = '-'
        if reviewer:
            email = reviewer.getProperty('email')
        return email

    def printCollegeProposalInfos(self):
        """Printed on a Council item, get the linked College meeting and print the date it was proposed in."""
        collegeItem = self.context.adapted().getItemCollege()
        if collegeItem and collegeItem.hasMeeting():
            tool = api.portal.get_tool('portal_plonemeeting')
            date = tool.formatMeetingDate(collegeItem.getMeeting(), markAdoptsNextCouncilAgenda=False)
            sentence = u"Sur proposition du Collège Communal, en sa séance du %s, et " \
                u"après examen du dossier par la Commission compétente ;" % date
        else:
            sentence = u"Sur proposition du Collège Communal, et après examen du dossier par la Commission compétente ;"
        return sentence

    def printActeContentForCollege(self):
        """Printed on a College item, get the whole body of the acte in one shot."""
        body = self.context.getMotivation() and self.context.getMotivation() + '<p></p>' or ''
        if self.context.adapted().getItemWithFinanceAdvice().getFinanceAdvice()!= '_none_' and \
           self.context.adapted().mayGenerateFDAdvice():
            body += self.context.adapted().getLegalTextForFDAdvice() + '<p></p>'
        representative = self.context.getCategory(theObject=True).Description().split('|')[1]
        body += "<p>Sur proposition de %s <br/></p>" % representative
        body += self.context.getDecision() + '<p></p>'
        body += self.context.getDecisionSuite() and self.context.getDecisionSuite()  + '<p></p>' or ''
        body += self.context.getDecisionEnd() and self.context.getDecisionEnd() or ''
        if self.context.getSendToAuthority():
            body += "<p>Conformément aux prescrits des articles L3111-1 et suivants " \
                    "du Code de la démocratie locale et de la décentralisation relatifs "\
                    "à la Tutelle, la présente décision et ses pièces justificatives sont "\
                    "transmises aux Autorités de Tutelle.</p>"
        return body

    def printActeContentForCouncil(self):
        """Printed on a Council item, get the whole body of the acte in one shot."""
        body = self.context.getMotivation() and self.context.getMotivation() + '<p></p>' or ''
        if self.context.adapted().getItemWithFinanceAdvice().getFinanceAdvice()!= '_none_' and \
           self.context.adapted().mayGenerateFDAdvice():
            body += self.context.adapted().getLegalTextForFDAdvice() + '<p></p>'
        body += self.printCollegeProposalInfos().encode("utf-8")
        body += self.context.getDecision() + '<p></p>'
        body += self.context.getDecisionSuite() and self.context.getDecisionSuite()  + '<p></p>' or ''
        body += self.context.getDecisionEnd() and self.context.getDecisionEnd() or ''
        if self.context.getSendToAuthority():
            body += "<p>Conformément aux prescrits des articles L3111-1 et suivants " \
                    "du Code de la démocratie locale et de la décentralisation relatifs "\
                    "à la Tutelle, la présente décision et ses pièces justificatives sont "\
                    "transmises aux Autorités de Tutelle.<br/></p>"
        body += self.context.getObservations() and self.context.getObservations() or ''
        return body
