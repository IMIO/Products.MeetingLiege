# -*- coding: utf-8 -*-
#
# File: indexes.py
#
# Copyright (c) 2015 by Imio.be
#
# GNU General Public License (GPL)
#

from plone.indexer import indexer
from Products.PloneMeeting.interfaces import IMeetingItem


@indexer(IMeetingItem)
def category_id(obj):
    """
      Indexes the getCategoryId defined on the selected MeetingItem.category
    """
    category = obj.getCategory(theObject=True)
    if not category.meta_type == 'MeetingCategory':
        return []
    else:
        return category.getCategoryId()
