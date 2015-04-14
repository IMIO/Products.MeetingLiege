## Script (Python) "generateCDLD"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=
##

context.REQUEST.set('templateId', 'generate-cdld')
# this is a dummy item we use because generateDocument here above need an item object...
brains=context.portal_catalog.searchResults(portal_type='MeetingItemCollege', sort_limit=1)
context.REQUEST.set('objectUid', brains[0].UID)

return context.portal_plonemeeting.generateDocument()
