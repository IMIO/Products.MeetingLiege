from Products.PloneMeeting.content.advice import IMeetingAdvice
from zope.component import queryUtility
from zope.schema.interfaces import IVocabularyFactory
from Products.MeetingLiege.config import FINANCE_GROUP_IDS
from zope.component.hooks import getSite


# override the IMeetingAdvice.advice_hide_during_redaction defaultFactory
def patched_default_advice_hide_during_redaction():
    '''Default value for field 'advice_hide_during_redaction'.
       This is made for now to be overrided...'''
    # XXX change commented 'return False', return True for finance advice, False for others
    # return False
    # if finance group in group vocabulary, we use special _finance advice types
    factory = queryUtility(IVocabularyFactory, u'Products.PloneMeeting.content.advice.advice_group_vocabulary')
    site = getSite()
    context = site.REQUEST['PUBLISHED'].context
    groupVocab = factory(context)
    groupIds = set([group.value for group in groupVocab._terms])
    if set(FINANCE_GROUP_IDS).intersection(groupIds):
        return True
    return False

IMeetingAdvice['advice_hide_during_redaction'].defaultFactory = patched_default_advice_hide_during_redaction
