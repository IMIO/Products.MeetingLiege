# -*- coding: utf-8 -*-

from Products.PloneMeeting.interfaces import IMeetingItemWorkflowActions
from Products.PloneMeeting.interfaces import IMeetingItemWorkflowConditions
from Products.PloneMeeting.interfaces import IMeetingWorkflowActions
from Products.PloneMeeting.interfaces import IMeetingWorkflowConditions
from Products.PloneMeeting.workflows.advice import IMeetingAdviceWorkflowActions
from Products.PloneMeeting.workflows.advice import IMeetingAdviceWorkflowConditions


__author__ = """Gauthier Bastien <g.bastien@imio.be>"""
__docformat__ = 'plaintext'


class IMeetingItemBourgmestreWorkflowActions(IMeetingItemWorkflowActions):
    ''' '''


class IMeetingItemBourgmestreWorkflowConditions(IMeetingItemWorkflowConditions):
    ''' '''


class IMeetingBourgmestreWorkflowActions(IMeetingWorkflowActions):
    ''' '''


class IMeetingBourgmestreWorkflowConditions(IMeetingWorkflowConditions):
    ''' '''


class IMeetingAdviceFinancesWorkflowActions(IMeetingAdviceWorkflowActions):
    ''' '''


class IMeetingAdviceFinancesWorkflowConditions(IMeetingAdviceWorkflowConditions):
    ''' '''


class IMeetingItemCollegeLiegeWorkflowActions(IMeetingItemWorkflowActions):
    '''This interface represents a meeting item as viewed by the specific
       item workflow that is defined in this MeetingLiege product.'''
    def doPresent():
        """
          Triggered while doing the 'present' transition
        """
    def doAcceptButModify():
        """
          Triggered while doing the 'accept_but_modify' transition
        """
    def doPreAccept():
        """
          Triggered while doing the 'pre_accept' transition
        """


class IMeetingItemCollegeLiegeWorkflowConditions(IMeetingItemWorkflowConditions):
    '''This interface represents a meeting item as viewed by the specific
       item workflow that is defined in this MeetingLiege product.'''
    def mayDecide():
        """
          Guard for the 'decide' transition
        """
    def mayFreeze():
        """
          Guard for the 'freeze' transition
        """
    def mayCorrect(destinationState=None):
        """
          Guard for the 'backToXXX' transitions
        """


class IMeetingCollegeLiegeWorkflowActions(IMeetingWorkflowActions):
    '''This interface represents a meeting as viewed by the specific meeting
       workflow that is defined in this MeetingLiege product.'''
    def doClose():
        """
          Triggered while doing the 'close' transition
        """
    def doDecide():
        """
          Triggered while doing the 'decide' transition
        """
    def doFreeze():
        """
          Triggered while doing the 'freeze' transition
        """
    def doBackToCreated():
        """
          Triggered while doing the 'doBackToCreated' transition
        """


class IMeetingCollegeLiegeWorkflowConditions(IMeetingWorkflowConditions):
    '''This interface represents a meeting as viewed by the specific meeting
       workflow that is defined in this MeetingLiege product.'''
    def mayFreeze():
        """
          Guard for the 'freeze' transition
        """
    def mayClose():
        """
          Guard for the 'close' transitions
        """
    def mayDecide():
        """
          Guard for the 'decide' transition
        """
    def mayChangeItemsOrder():
        """
          Check if the user may or not changes the order of the items on the meeting
        """
    def mayCorrect(destinationState=None):
        """
          Guard for the 'backToXXX' transitions
        """


# ------------------------------------------------------------------------------
class IMeetingCouncilLiegeWorkflowActions(IMeetingWorkflowActions):
    '''This interface represents a meeting as viewed by the specific meeting
       workflow that is defined in this MeetingLiege product.'''
    def doClose():
        """
          Triggered while doing the 'close' transition
        """
    def doDecide():
        """
          Triggered while doing the 'decide' transition
        """
    def doFreeze():
        """
          Triggered while doing the 'freeze' transition
        """
    def doBackToCreated():
        """
          Triggered while doing the 'doBackToCreated' transition
        """


class IMeetingCouncilLiegeWorkflowConditions(IMeetingWorkflowConditions):
    '''This interface represents a meeting as viewed by the specific meeting
       workflow that is defined in this MeetingLiege product.'''
    def mayFreeze():
        """
          Guard for the 'freeze' transition
        """
    def mayClose():
        """
          Guard for the 'close' transitions
        """
    def mayDecide():
        """
          Guard for the 'decide' transition
        """
    def mayChangeItemsOrder():
        """
          Check if the user may or not changes the order of the items on the meeting
        """
    def mayCorrect(destinationState=None):
        """
          Guard for the 'backToXXX' transitions
        """


class IMeetingItemCouncilLiegeWorkflowActions(IMeetingItemWorkflowActions):
    '''This interface represents a meeting item as viewed by the specific
       item workflow that is defined in this MeetingLiege product.'''
    def doPresent():
        """
          Triggered while doing the 'present' transition
        """


class IMeetingItemCouncilLiegeWorkflowConditions(IMeetingItemWorkflowConditions):
    '''This interface represents a meeting item as viewed by the specific
       item workflow that is defined in this MeetingLiege product.'''
    def mayDecide():
        """
          Guard for the 'decide' transition
        """
    def mayFreeze():
        """
          Guard for the 'freeze' transition
        """
    def mayRemove():
        """
          Guard for the 'remove' transition (removing an item from the meeting)
        """

# ------------------------------------------------------------------------------
