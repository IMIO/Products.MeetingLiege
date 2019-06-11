# -*- coding: utf-8 -*-

from Products.Five import BrowserView
from Products.MeetingLiege.config import ITEM_MAIN_INFOS_HISTORY


class MainInfosHistoryView(BrowserView):
    """ """

    def __call__(self, event_time):
        """ """
        for event in getattr(self.context, ITEM_MAIN_INFOS_HISTORY, []):
            if int(event['time']) == event_time:
                self.historized_data = event['historized_data']
                break
        return super(MainInfosHistoryView, self).__call__()
