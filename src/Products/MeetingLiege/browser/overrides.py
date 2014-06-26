from zope.component import queryUtility
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from plone.memoize.view import memoize_contextless
from Products.PloneMeeting.browser.overrides import BaseActionsPanelView
from Products.PloneMeeting.browser.advicechangedelay import AdviceDelaysView
from Products.MeetingLiege.config import FINANCE_GROUP_IDS


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


class AdviceTypeVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        terms = []
        cfg = context.portal_plonemeeting.getMeetingConfig(context)
        if not cfg:
            return SimpleVocabulary(terms)
        usedAdviceTypes = cfg.getUsedAdviceTypes()
        # make sure if an adviceType was used for context and it is no more available, it
        # appears in the vocabulary and is so useable...
        if context.portal_type == 'meetingadvice' and not context.advice_type in usedAdviceTypes:
            usedAdviceTypes = usedAdviceTypes + (context.advice_type, )
        # if finance group in group vocabulary, we use special _finance advice types
        factory = queryUtility(IVocabularyFactory, u'Products.PloneMeeting.content.advice.advice_group_vocabulary')
        # self.context is portal
        groupVocab = factory(context)
        groupIds = set([group.value for group in groupVocab._terms])
        if set(FINANCE_GROUP_IDS).intersection(groupIds):
            # we are on a finance group, only keep _finance advice types
            res = list(usedAdviceTypes)
            for adviceType in usedAdviceTypes:
                if not adviceType in ('positive_finance', 'negative_finance', 'not_required_finance', ):
                    res.remove(adviceType)
            usedAdviceTypes = tuple(res)
        else:
            # not a finance group, remove specific _finance types
            res = list(usedAdviceTypes)
            for adviceType in usedAdviceTypes:
                if adviceType in ('positive_finance', 'negative_finance', 'not_required_finance', ):
                    res.remove(adviceType)
            usedAdviceTypes = tuple(res)

        for advice_id, advice_title in cfg.listAdviceTypes().items():
            if advice_id in usedAdviceTypes:
                terms.append(SimpleTerm(advice_id, advice_id, advice_title))
        return SimpleVocabulary(terms)
