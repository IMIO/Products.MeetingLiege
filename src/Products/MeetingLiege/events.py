# -*- coding: utf-8 -*-
#
# File: events.py
#
# Copyright (c) 2013 by Imio.be
# Generator: ArchGenXML Version 2.7
#            http://plone.org/products/archgenxml
#
# GNU General Public License (GPL)
#

__author__ = """Gauthier Bastien <g.bastien@imio.be>, Stephan Geulette <s.geulette@imio.be>"""
__docformat__ = 'plaintext'


def onMeetingItemTransition(obj, event):
    '''Called whenever a transition has been fired on a meetingItem.
       Reindex the previous_review_state index.'''
    if not event.transition or (obj != event.object):
        return
    obj.reindexObject(idxs=['previous_review_state', ])
