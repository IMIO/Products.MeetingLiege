# -*- coding: utf-8 -*-
#
# File: overrides.py
#
# Copyright (c) 2015 by Imio.be
#
# GNU General Public License (GPL)
#
from zope.component import getAdapter

from plone.memoize.view import memoize_contextless
from plone import api

from imio.history.interfaces import IImioHistory
from DateTime import DateTime
from Products.PloneMeeting.browser.advicechangedelay import AdviceDelaysView
from Products.PloneMeeting.browser.overrides import BaseActionsPanelView
from Products.PloneMeeting.browser.views import ItemDocumentGenerationHelperView
from Products.PloneMeeting.browser.views import FolderDocumentGenerationHelperView


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
        if self.context.adapted().getLegalTextForFDAdvice():
            body += self.context.adapted().getLegalTextForFDAdvice() + '<p></p>'
        representative = self.context.getCategory(theObject=True).Description().split('|')[1]
        body += "<p>Sur proposition de %s <br/></p>" % representative
        body += self.context.getDecision() + '<p></p>'
        body += self.context.getDecisionSuite() and self.context.getDecisionSuite() + '<p></p>' or ''
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
        if self.context.adapted().getLegalTextForFDAdvice():
            body += self.context.adapted().getLegalTextForFDAdvice() + '<p></p>'
        body += self.printCollegeProposalInfos().encode("utf-8")
        body += self.context.getDecision() + '<p></p>'
        body += self.context.getDecisionSuite() and self.context.getDecisionSuite() + '<p></p>' or ''
        body += self.context.getDecisionEnd() and self.context.getDecisionEnd() or ''
        if self.context.getSendToAuthority():
            body += "<p>Conformément aux prescrits des articles L3111-1 et suivants " \
                    "du Code de la démocratie locale et de la décentralisation relatifs "\
                    "à la Tutelle, la présente décision et ses pièces justificatives sont "\
                    "transmises aux Autorités de Tutelle.<br/></p>"
        body += self.context.getObservations() and self.context.getObservations() or ''
        return body


class MLFolderDocumentGenerationHelperView(FolderDocumentGenerationHelperView):
    """Specific printing methods used for item."""

    def printFDStats(self, brains):
        """
        Printed on a list of all the items where a finance advice has been asked.
        Join informations from completeness, workflow and revision histories and
        return them in a list generated in a xls file.
        """
        items_and_advices = self.selected_indexAdvisers_data(brains)
        pr = api.portal.get_tool('portal_repository')
        pt = api.portal.get_tool('portal_transforms')
        pw = api.portal.get_tool('portal_workflow')
        kept_history = []
        for item_and_advice in items_and_advices:
            item = item_and_advice['item']
            advice_id = item_and_advice['advices'][0]['id']
            full_history = []
            advice = item.getAdviceDataFor(item)[advice_id]['given_advice']
            if advice:
                advice_revisions = [revision for revision in getAdapter(advice, IImioHistory, 'revision').getHistory()]
                # Browse the advice versions and keep their history.
                for revision in advice_revisions:
                    rev_history = pr.retrieve(advice, revision['version_id']).object.getHistory()
                    full_history.extend(rev_history)
            # Keep the completeness history
            full_history.extend(item.completeness_changes_history)
            # Keep the workflow history.
            itemWFId = pw.getWorkflowsFor(item)[0].getId()
            full_history.extend(item.workflow_history[itemWFId])
            # sort from older to newer. Needed to catch the
            # completeness_incomplete before backToInternalReviewer.
            full_history.sort(key=lambda x: x["time"], reverse=False)
            last_action = ''
            last_comment = ''
            kept_states = []
            finance_proposals = []
            first_time_complete = True
            for state in full_history:
                # keep the history when  advice is positive or negative.
                if (state['action'] == 'backToProposedToDirector' and
                    state['comments'] == 'item_wf_changed_finance_advice_negative') or\
                   (state['action'] == 'validate' and
                    state['comments'] == 'item_wf_changed_finance_advice_positive'):
                    kept_states.append(state)
                # When item is send back to internal reviewer because of incompleteness,
                # keep the history and add the comment eventually given when set to
                # incomplete to the back to reviewer comment.
                elif (last_action == 'completeness_incomplete' and
                        state['action'] == 'backToProposedToInternalReviewer'):
                    state['comments'] += last_comment
                    kept_states.append(state)
                # Keep the history when item is complete, but only the first
                # time.
                elif (state['action'] == 'completeness_complete' and
                      first_time_complete is True):
                    kept_states.append(state)
                    first_time_complete = False
                # Keep also the proposeToFinance state.
                elif (state['action']) == 'proposeToFinance':
                    finance_proposals.append(state.copy())
                last_action = state['action']
                last_comment = state['comments']
            # Reverse the sort on time to have the most recent state first.
            kept_states.sort(key=lambda x: x["time"], reverse=True)
            # Do the same on the list containing the proposals to finances.
            finance_proposals.sort(key=lambda x: x["time"], reverse=True)
            kept_history.append([item, kept_states, finance_proposals, advice_id])

        results = []
        for item, kept_states, finance_proposals, advice_id in kept_history:
            res = {}
            res['title'] = item.Title()
            res['group'] = item.getProposingGroup()
            if item.getMeeting():
                res['meeting_date'] = item.getMeeting().getDate().strftime('%d/%m/%Y')
            else:
                res['meeting_date'] = ''
            adviceInfos = item.getAdviceDataFor(item)[advice_id]
            advice = adviceInfos['given_advice']
            res['adviser'] = adviceInfos['name']
            # If the advice has been created.
            if advice:
                advice_revisions = [revision for revision in getAdapter(advice, IImioHistory, 'revision').getHistory()]
                end_advice = 'OUI'
                for state in kept_states:
                    for revision in advice_revisions:
                        res['comments'] = ''
                        if DateTime(revision['time']) < state['time']:
                            advice_comment = pr.retrieve(advice, revision['version_id']).object.advice_comment
                            # Must check if a comment was added. If not, there
                            # is no advice_comment object.
                            if advice_comment:
                                html_comment = advice_comment.output
                                str_comment = pt.convert('html_to_text', html_comment).getData().strip()
                                res['comments'] = str_comment
                                break

                    res['advice_date'] = state['time'].strftime('%d/%m/%Y')
                    if state['action'] == 'validate':
                        res['end_advice'] = end_advice
                        res['advice_type'] = 'Avis finance favorable'
                        if end_advice == 'OUI':
                            end_advice = 'NON'

                    elif state['action'] == 'backToProposedToDirector':
                        res['end_advice'] = end_advice
                        res['advice_type'] = 'Avis finance défavorable'
                        if end_advice == 'OUI':
                            end_advice = 'NON'
                    elif state['action'] == 'completeness_complete':
                        res['end_advice'] = ''
                        res['advice_type'] = 'Complétude'
                        res['comments'] = ''
                    elif state['action'] == 'backToProposedToInternalReviewer':
                        res['end_advice'] = ''
                        res['advice_type'] = 'Renvoyé au validateur interne pour incomplétude'
                        res['comments'] = state['comments']
                    for fp in finance_proposals:
                        if fp['time'] < state['time']:
                            res['reception_date'] = fp['time'].strftime('%d/%m/%y à %H:%M')
                            break
                    results.append(res.copy())
            # else if the advice is just asked but no advice has been created
            # yet.
            else:
                for state in kept_states:
                    res['advice_date'] = state['time'].strftime('%d/%m/%Y')
                    if state['action'] == 'completeness_complete':
                        res['end_advice'] = ''
                        res['advice_type'] = 'Complétude'
                        res['comments'] = ''
                    elif state['action'] == 'backToProposedToInternalReviewer':
                        res['end_advice'] = ''
                        res['advice_type'] = 'Renvoyé au validateur interne pour incomplétude'
                        res['comments'] = state['comments']
                    for fp in finance_proposals:
                        if fp['time'] < state['time']:
                            res['reception_date'] = fp['time'].strftime('%d/%m/%y à %H:%M')
                            break
                    results.append(res.copy())

        return results
