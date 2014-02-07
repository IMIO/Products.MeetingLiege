## Script (Python) "getLinkAndTitle"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=Return an escaped version of link and title to use in templates
##

import cgi

return "<a href='%s'>%s</a>" % (context.absolute_url(), cgi.escape(context.Title()))
