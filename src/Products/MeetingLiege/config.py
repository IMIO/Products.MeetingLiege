# -*- coding: utf-8 -*-
#
# File: config.py
#
# Copyright (c) 2014 by Imio.be
# Generator: ArchGenXML Version 2.7
#            http://plone.org/products/archgenxml
#
# GNU General Public License (GPL)
#

__author__ = """Gauthier Bastien <g.bastien@imio.be>"""
__docformat__ = 'plaintext'


# Product configuration.
#
# The contents of this module will be imported into __init__.py, the
# workflow configuration and every content type module.
#
# If you wish to perform custom configuration, you may put a file
# AppConfig.py in your product's root directory. The items in there
# will be included (by importing) in this file if found.

from Products.CMFCore.permissions import setDefaultRoles
##code-section config-head #fill in your manual code here
##/code-section config-head


PROJECTNAME = "MeetingLiege"

# Permissions
DEFAULT_ADD_CONTENT_PERMISSION = "Add portal content"
setDefaultRoles(DEFAULT_ADD_CONTENT_PERMISSION, ('Manager', 'Owner', 'Contributor'))

product_globals = globals()

# Dependencies of Products to be installed by quick-installer
# override in custom configuration
DEPENDENCIES = []

# Dependend products - not quick-installed - used in testcase
# override in custom configuration
PRODUCT_DEPENDENCIES = []

##code-section config-bottom #fill in your manual code here
from Products.PloneMeeting import config as PMconfig
LIEGEROLES = {}
LIEGEROLES['budgetimpactreviewers'] = 'MeetingBudgetImpactReviewer'
LIEGEROLES['serviceheads'] = 'MeetingServiceHead'
LIEGEROLES['officemanagers'] = 'MeetingOfficeManager'
LIEGEROLES['divisionheads'] = 'MeetingDivisionHead'
LIEGEROLES['directors'] = 'MeetingDirector'
LIEGEROLES['followupwriters'] = 'MeetingFollowUpWriter'
PMconfig.MEETINGROLES.update(LIEGEROLES)
PMconfig.MEETING_GROUP_SUFFIXES = PMconfig.MEETINGROLES.keys()


# Load custom configuration not managed by archgenxml
try:
    from Products.MeetingLiege.AppConfig import *
except ImportError:
    pass
