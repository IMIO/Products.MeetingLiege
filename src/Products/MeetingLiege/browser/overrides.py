from zope.component import queryUtility
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from plone.memoize.view import memoize_contextless
from Products.PloneMeeting.browser.overrides import BaseActionsPanelView
from Products.MeetingLiege.config import FINANCE_GROUP_IDS


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
                     'meetingadvice.proposeToFinancialManager',
                     'meetingadvice.signAdvice',
                     'meetingadvice.backToProposedToFinancialController',
                     'meetingadvice.backToProposedToFinancialReviewer',
                     'meetingadvice.backToProposedToFinancialManager', ]
        return toConfirm


class AdviceTypeVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        terms = []
        cfg = context.portal_plonemeeting.getMeetingConfig(context)
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
                if not adviceType in ('positive_finance', 'negative_finance'):
                    res.remove(adviceType)
            usedAdviceTypes = tuple(res)
        else:
            # not a finance group, remove specific _finance types
            res = list(usedAdviceTypes)
            for adviceType in usedAdviceTypes:
                if adviceType in ('positive_finance', 'negative_finance'):
                    res.remove(adviceType)
            usedAdviceTypes = tuple(res)

        for advice_id, advice_title in cfg.listAdviceTypes().items():
            if advice_id in usedAdviceTypes:
                terms.append(SimpleTerm(advice_id, advice_id, advice_title))
        return SimpleVocabulary(terms)
