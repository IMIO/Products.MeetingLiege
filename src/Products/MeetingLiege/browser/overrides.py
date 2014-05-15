from Products.PloneMeeting.browser.overrides import PloneMeetingDocumentBylineViewlet


class MeetingLiegeDocumentBylineViewlet(PloneMeetingDocumentBylineViewlet):
    '''
      Overrides the PloneMeetingDocumentBylineViewlet to display the  to hide it for some layouts.
    '''

    def show_history(self):
        """
          Show the history in every cases...
        """
        return True
