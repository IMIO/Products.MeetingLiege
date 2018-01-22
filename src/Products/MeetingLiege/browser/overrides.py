# -*- coding: utf-8 -*-
#
# File: overrides.py
#
# Copyright (c) 2015 by Imio.be
#
# GNU General Public License (GPL)
#

import time
from DateTime import DateTime
from zope.component import getAdapter

from plone.memoize.view import memoize_contextless
from plone import api

from collective.iconifiedcategory.browser.actionview import SignedChangeView
from imio.history.interfaces import IImioHistory
from Products.PloneMeeting.browser.advicechangedelay import AdviceDelaysView
from Products.PloneMeeting.browser.overrides import BaseActionsPanelView
from Products.PloneMeeting.browser.views import ItemDocumentGenerationHelperView
from Products.PloneMeeting.browser.views import FolderDocumentGenerationHelperView
from Products.PloneMeeting.browser.overrides import PMContentHistoryView
from Products.MeetingLiege import logger


class MLAdviceActionsPanelView(BaseActionsPanelView):
    """
      Specific actions displayed on a meetingadvice.
    """
    def __init__(self, context, request):
        super(MLAdviceActionsPanelView, self).__init__(context, request)

    @memoize_contextless
    def _transitionsToConfirm(self):
        """
          Override, every transitions of the finance workflow will have to be confirmed (commentable).
        """
        toConfirm = ['meetingadvicefinances.proposeToFinancialReviewer',
                     'meetingadvicefinances.proposeToFinancialManager',
                     'meetingadvicefinances.signFinancialAdvice',
                     'meetingadvicefinances.backToProposedToFinancialController',
                     'meetingadvicefinances.backToProposedToFinancialReviewer',
                     'meetingadvicefinances.backToProposedToFinancialManager', ]
        return toConfirm


class MLAdviceDelaysView(AdviceDelaysView):
    '''Render the advice available delays HTML on the advices list.'''

    def _mayEditDelays(self, isAutomatic):
        '''Rules of original method applies but here, the _financialmanagers,
           may also change an advice delay in some cases.'''

        if not super(MLAdviceDelaysView, self)._mayEditDelays(isAutomatic):
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
            if financialManagerGroupId not in member.getGroups():
                return False

        return True


class MLSignedChangeView(SignedChangeView):
    """ """

    def _may_set_values(self, values):
        """ """
        res = super(MLSignedChangeView, self)._may_set_values(values)
        if res:
            tool = api.portal.get_tool('portal_plonemeeting')
            res = bool(tool.isManager(self.context))
        return res


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
            date = tool.formatMeetingDate(collegeItem.getMeeting())
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
        body += "<p>Sur proposition de %s,<br/></p>" % representative
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
        body += self.printCollegeProposalInfos().encode("utf-8") + '<p></p>'
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
        Printed on a list of all the items with a finance advice asked on it.
        Join informations from completeness, workflow and revision histories and
        return them in a list generated in a xls file.
        """
        pr = api.portal.get_tool('portal_repository')
        pw = api.portal.get_tool('portal_workflow')
        results = []
        startTime1 = time.time()
        for brain in brains:
            item = brain.getObject()
            advice_id = item.adapted().getFinanceGroupIdsForItem(checkAdviceIndex=True)
            full_history = []
            advice_infos = item.getAdviceDataFor(item)[advice_id]
            advice = advice_infos['given_advice']
            advice_revisions = []
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
                # keep the history when advice is positive, negative or timed
                # out.
                if (state['action'] == 'backToProposedToDirector' and
                    state['comments'] == 'item_wf_changed_finance_advice_negative') or\
                   (state['action'] == 'validate' and
                    (state['comments'] == 'item_wf_changed_finance_advice_positive' or
                     state['comments'] == 'item_wf_changed_finance_advice_timed_out')):
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
            res = self._preparePrintableDatas(item,
                                              kept_states,
                                              finance_proposals,
                                              advice_infos,
                                              advice_revisions)
            # Because we don't want a list of list of dict, we append each
            # element of res in results.
            for re in res:
                results.append(re)

        seconds = time.time() - startTime1
        logger.info('PrintFDStats: First part done in %.2f seconds(s).' % (seconds))

        return results

    def _preparePrintableDatas(self, item, kept_states, finance_proposals, advice_infos, advice_revisions):
        """ Prepare datas needed by the FD synthesis. """
        pr = api.portal.get_tool('portal_repository')
        pt = api.portal.get_tool('portal_transforms')
        results = []
        res = {}
        res['title'] = item.Title()
        res['group'] = item.getProposingGroup(theObject=True).Title()
        if item.getMeeting():
            res['meeting_date'] = item.getMeeting().getDate().strftime('%d/%m/%Y')
        else:
            res['meeting_date'] = ''
        advice = advice_infos['given_advice']
        res['adviser'] = advice_infos['name']
        # If the advice has been created.
        if advice:
            end_advice = 'OUI'
            for state in kept_states:
                res['comments'] = ''
                for revision in advice_revisions:
                    if DateTime(revision['time']) < state['time']:
                        advice_object = pr.retrieve(advice, revision['version_id']).object
                        advice_comment = advice_object.advice_comment
                        advice_type = advice_object.advice_type
                        # Must check if a comment was added. If not, there
                        # is no advice_comment object.
                        if advice_comment:
                            html_comment = advice_comment.output
                            str_comment = pt.convert('html_to_text', html_comment).getData().strip()
                            res['comments'] = str_comment
                            break
                        else:
                            break
                res['advice_date'] = state['time'].strftime('%d/%m/%Y')
                if state['comments'] == 'item_wf_changed_finance_advice_timed_out':
                    res['end_advice'] = end_advice
                    res['advice_type'] = 'Avis finance expiré'
                    if end_advice == 'OUI':
                        end_advice = 'NON'
                elif state['comments'] == 'item_wf_changed_finance_advice_positive':
                    if advice_type == 'positive_with_remarks_finance':
                        res['advice_type'] = 'Avis finance favorable avec remarques'
                    else:
                        res['advice_type'] = 'Avis finance favorable'
                    res['end_advice'] = end_advice
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
                res['comments'] = ''
                res['advice_date'] = state['time'].strftime('%d/%m/%Y')
                if state['action'] == 'completeness_complete':
                    res['end_advice'] = ''
                    res['advice_type'] = 'Complétude'
                elif state['action'] == 'backToProposedToInternalReviewer':
                    res['end_advice'] = ''
                    res['advice_type'] = 'Renvoyé au validateur interne pour incomplétude'
                    res['comments'] = state['comments']
                elif state['comments'] == 'item_wf_changed_finance_advice_timed_out':
                    res['end_advice'] = ''
                    res['advice_type'] = 'Avis finance expiré'
                # Some items had their advice deleted. So they still have
                # the backtoproposedtodirector state in history, even if
                # there is no more advice given.
                elif state['action'] == 'backToProposedToDirector':
                    res['end_advice'] = ''
                    res['advice_type'] = 'Avis finance défavorable'
                # Yeah, you would not expect to find a positive advice in
                # the history if no advice is given. An admin should however, in
                # some unusual cases, have deleted an advice that has been
                # given.
                elif state['comments'] == 'item_wf_changed_finance_advice_positive':
                    res['end_advice'] = ''
                    res['advice_type'] = 'Avis finance expiré'
                for fp in finance_proposals:
                    if fp['time'] < state['time']:
                        res['reception_date'] = fp['time'].strftime('%d/%m/%y à %H:%M')
                        break
                results.append(res.copy())
        return results


class MLMeetingDocumentGenerationHelperView(FolderDocumentGenerationHelperView):
    """Specific printing methods used for meeting."""

    def printItemActeContentForCollege(self, item):
        """
        Printed on a College Item in a College Meeting, get the whole body
        of the acte in one shot.
        """
        view = item.restrictedTraverse("@@document-generation")
        helper = view.get_generation_context_helper()
        return helper.printActeContentForCollege()

    def printItemActeContentForCouncil(self, item):
        """
        Printed on a Council Item in a Council Meeting, get the whole body
        of the acte in one shot.
        """
        view = item.restrictedTraverse("@@document-generation")
        helper = view.get_generation_context_helper()
        return helper.printActeContentForCouncil()


class MLContentHistoryView(PMContentHistoryView):
    """ """
    histories_to_handle = (u'revision', u'workflow', u'data_changes', u'main_infos')

    def renderCustomJS(self):
        """ """
        return '<script>overOverlays();</script>'
