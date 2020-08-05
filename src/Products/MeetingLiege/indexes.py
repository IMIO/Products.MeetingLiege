# -*- coding: utf-8 -*-

from plone.indexer import indexer
from Products.PloneMeeting.interfaces import IMeetingItem


@indexer(IMeetingItem)
def category_id(obj):
    """
      Indexes the getCategoryId defined on the selected MeetingItem.category
    """
    category = obj.getCategory(theObject=True)
    if not category.portal_type == 'meetingcategory':
        return []
    else:
        return category.category_id
