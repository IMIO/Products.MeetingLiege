# -*- coding: utf-8 -*-

from imio.helpers.cache import get_plone_groups_for_user
from imio.history.interfaces import IImioHistory
from imio.history.utils import getLastWFAction
from plone import api
from plone.memoize.view import memoize_contextless
from Products.MeetingLiege import logger
from Products.PloneMeeting.browser.advicechangedelay import AdviceDelaysView
from Products.PloneMeeting.browser.overrides import AdviceActionsPanelView
from Products.PloneMeeting.browser.overrides import PMContentHistoryView
from Products.PloneMeeting.browser.views import FolderDocumentGenerationHelperView
from Products.PloneMeeting.browser.views import ItemDocumentGenerationHelperView
from Products.PloneMeeting.utils import get_event_field_data
from zope.component import getAdapter

import time


class MLAdviceActionsPanelView(AdviceActionsPanelView):
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
            financeGroupId = self.context.adapted().getFinanceGroupUIDForItem()
            if not financeGroupId:
                return False

            if not self.context.adviceIndex[financeGroupId]['advice_addable'] and \
               not self.context.adviceIndex[financeGroupId]['advice_editable']:
                return False

            # current advice is still addable/editable, a finance manager may change delay for it
            financialManagerGroupId = '%s_financialmanagers' % financeGroupId
            if financialManagerGroupId not in get_plone_groups_for_user():
                return False

        return True


class MLItemDocumentGenerationHelperView(ItemDocumentGenerationHelperView):
    """Specific printing methods used for item."""

    def _collegeAdministrativeReviewer(self):
        """Used on a council item : get the administrative reviewer of the College item."""
        collegeItem = self.context.adapted().getItemCollege()
        if collegeItem:
            event = getLastWFAction(collegeItem, 'proposeToDirector')
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
            date = tool.format_date(collegeItem.getMeeting().date)
            sentence = u"<p>Sur proposition du Collège communal, en sa séance du %s, et " \
                u"après examen du dossier par la Commission compétente ;</p>" % date
        else:
            sentence = u"<p>Sur proposition du Collège communal, " \
                u"et après examen du dossier par la Commission compétente ;</p>"
        return sentence

    def printActeContentForCollege(self):
        """Printed on a College item, get the whole body of the acte in one shot."""
        body = self.context.getMotivation()
        legalTextForFDAdvice = self.context.adapted().getLegalTextForFDAdvice().strip()
        if legalTextForFDAdvice:
            body += legalTextForFDAdvice
        category = self.context.getCategory(theObject=True)
        representative = category and category.Description().split('|')[1] or "Monsieur / Madame X"
        body += "<p>Sur proposition de %s,<br></p>" % representative
        body += self.context.getDecision()
        body += self.context.getDecisionSuite()
        body += self.context.getDecisionEnd()
        if self.context.getSendToAuthority():
            body += "<p>Conformément aux prescrits des articles L3111-1 et suivants " \
                    "du Code de la démocratie locale et de la décentralisation relatifs "\
                    "à la Tutelle, la présente décision et ses pièces justificatives sont "\
                    "transmises aux Autorités de Tutelle.</p>"
        return body

    def printActeContentForCouncil(self, include_decisionEnd=True, include_observations=True):
        """Printed on a Council item, get the whole body of the acte in one shot."""
        body = self.context.getMotivation() or ''
        legalTextForFDAdvice = self.context.adapted().getLegalTextForFDAdvice().strip()
        if legalTextForFDAdvice:
            body += legalTextForFDAdvice
        body += self.printCollegeProposalInfos().encode("utf-8")
        body += self.context.getDecision()
        body += self.context.getDecisionSuite()
        # include decisionEnd and votesResult
        if include_decisionEnd:
            body += self.context.getVotesResult().strip()
            body += self.context.getDecisionEnd() and self.context.getDecisionEnd() or ''
        if self.context.getSendToAuthority():
            body += "<p>Conformément aux prescrits des articles L3111-1 et suivants " \
                    "du Code de la démocratie locale et de la décentralisation relatifs "\
                    "à la Tutelle, la présente décision et ses pièces justificatives sont "\
                    "transmises aux Autorités de Tutelle.</p>"
        if include_observations:
            body += self.context.getObservations() and self.context.getObservations() or ''
        return body

    def print_deliberation(self, xhtmlContents=[], **kwargs):
        """ """
        content = self.printActeContentForCouncil()
        return super(MLItemDocumentGenerationHelperView, self).print_deliberation(
            xhtmlContents=[content], **kwargs)

    def print_public_deliberation(self, xhtmlContents=[], **kwargs):
        """ """
        content = self.printActeContentForCouncil(
            include_decisionEnd=False, include_observations=False)
        return super(MLItemDocumentGenerationHelperView, self).print_deliberation(
            xhtmlContents=[content], **kwargs)

    def print_public_deliberation_decided(self, xhtmlContents=[], **kwargs):
        """ """
        content = self.printActeContentForCouncil(
            include_decisionEnd=True, include_observations=False)
        return super(MLItemDocumentGenerationHelperView, self).print_deliberation(
            xhtmlContents=[content], **kwargs)


class MLFolderDocumentGenerationHelperView(FolderDocumentGenerationHelperView):
    """Specific printing methods used for item."""

    def printFDStats(self, brains):
        """
        Printed on a list of all the items with a finance advice asked on it.
        Join informations from completeness, workflow and revision histories and
        return them in a list generated in a xls file.
        """
        results = []
        startTime1 = time.time()
        for brain in brains:
            item = brain.getObject()
            advice_id = item.adapted().getFinanceGroupUIDForItem(checkAdviceIndex=True)
            full_history = []
            advice_infos = item.getAdviceDataFor(item)[advice_id]
            advice = advice_infos['given_advice']
            advice_histories = []
            if advice:
                advice_histories = [history for history in
                                    getAdapter(advice, IImioHistory, 'advice_given').getHistory()]
                wf_history = getAdapter(advice, IImioHistory, 'workflow').getHistory()
                full_history.extend(wf_history)
            # older histories first
            advice_histories.reverse()
            # Keep the completeness history
            full_history.extend(item.completeness_changes_history)
            # Keep the item workflow history.
            wf_history = getAdapter(item, IImioHistory, 'workflow').getHistory()
            full_history.extend(wf_history)
            # sort from older to newer. Needed to catch the
            # completeness_incomplete before backToInternalReviewer.
            full_history.sort(key=lambda x: x["time"], reverse=False)
            last_action = ''
            last_comment = ''
            kept_states = []
            finance_proposals = []
            first_time_complete = True
            for state in full_history:
                # keep the history when advice is positive, negative or timed out.
                # formerly item with negative advice was auto sent back to director, now it is to internal reviewer
                if (state['action'] in
                        ('backTo_proposed_to_director_from_waiting_advices', 'backTo_proposed_to_internal_reviewer_from_waiting_advices') and
                    state['comments'] == 'item_wf_changed_finance_advice_negative') or \
                   (state['action'] == 'validate' and
                    (state['comments'] == 'item_wf_changed_finance_advice_positive' or
                     state['comments'] == 'item_wf_changed_finance_advice_timed_out')):
                    kept_states.append(state)
                # When item is send back to internal reviewer because of incompleteness,
                # keep the history and add the comment eventually given when set to
                # incomplete to the back to reviewer comment.
                elif (last_action == 'completeness_incomplete' and
                        state['action'] == 'backTo_proposed_to_internal_reviewer_from_waiting_advices'):
                    state['comments'] += last_comment
                    kept_states.append(state)
                # Keep the history when item is complete, but only the first
                # time.
                elif (state['action'] == 'completeness_complete' and
                      first_time_complete is True):
                    kept_states.append(state)
                    first_time_complete = False
                # Keep also the proposed_to_finance_waiting_advices state.
                elif (state['action']) == 'wait_advices_from_proposed_to_director':
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
                                              advice_histories)
            # Because we don't want a list of list of dict, we append each
            # element of res in results.
            for re in res:
                results.append(re)

        seconds = time.time() - startTime1
        logger.info('PrintFDStats: First part done in %.2f seconds(s).' % (seconds))

        return results

    def _preparePrintableDatas(self, item, kept_states, finance_proposals, advice_infos, advice_histories):
        """ Prepare datas needed by the FD synthesis. """
        pt = api.portal.get_tool('portal_transforms')
        results = []
        res = {}
        res['title'] = item.Title()
        res['group'] = item.getProposingGroup(theObject=True).Title()
        if item.getMeeting():
            res['meeting_date'] = item.getMeeting().date.strftime('%d/%m/%Y')
        else:
            res['meeting_date'] = ''
        advice = advice_infos['given_advice']
        res['adviser'] = advice_infos['name']
        # If the advice has been created.
        if advice:
            end_advice = 'OUI'
            for state in kept_states:
                res['comments'] = ''
                for advice_history in advice_histories:
                    if advice_history['time'] < state['time']:
                        advice_comment = get_event_field_data(
                            advice_history["advice_data"], "advice_comment")
                        advice_type = get_event_field_data(
                            advice_history["advice_data"], "advice_type")
                        # Must check if a comment was added. If not, there
                        # is no advice_comment object.
                        if advice_comment:
                            str_comment = pt.convert('html_to_text', advice_comment).getData().strip()
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
                elif state['comments'] == 'item_wf_changed_finance_advice_negative':
                    res['end_advice'] = end_advice
                    res['advice_type'] = 'Avis finance défavorable'
                    if end_advice == 'OUI':
                        end_advice = 'NON'
                elif state['action'] == 'completeness_complete':
                    res['end_advice'] = ''
                    res['advice_type'] = 'Complétude'
                    res['comments'] = ''
                elif state['action'] == 'backTo_proposed_to_internal_reviewer_from_waiting_advices':
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
                elif state['action'] == 'backTo_proposed_to_internal_reviewer_from_waiting_advices':
                    res['end_advice'] = ''
                    res['advice_type'] = 'Renvoyé au validateur interne pour incomplétude'
                    res['comments'] = state['comments']
                elif state['comments'] == 'item_wf_changed_finance_advice_timed_out':
                    res['end_advice'] = ''
                    res['advice_type'] = 'Avis finance expiré'
                # Some items had their advice deleted. So they still have
                # the item_wf_changed_finance_advice_negative comments in history, even if
                # there is no more advice given.
                elif state['comments'] == 'item_wf_changed_finance_advice_negative':
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
