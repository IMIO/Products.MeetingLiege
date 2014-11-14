# -*- coding: utf-8 -*-
#
# File: MeetingLiege.py
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
from collections import OrderedDict
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
LIEGEROLES['administrativereviewers'] = 'MeetingAdminReviewer'
LIEGEROLES['internalreviewers'] = 'MeetingInternalReviewer'
LIEGEROLES['reviewers'] = 'MeetingReviewer'
PMconfig.MEETINGROLES.update(LIEGEROLES)
PMconfig.MEETING_GROUP_SUFFIXES = PMconfig.MEETINGROLES.keys()

LIEGEMEETINGREVIEWERS = OrderedDict([('reviewers', 'proposed_to_director'),
                                     ('internalreviewers', 'proposed_to_internal_reviewer'),
                                     ('administrativereviewers', 'proposed_to_administrative_reviewer'), ])
PMconfig.MEETINGREVIEWERS = LIEGEMEETINGREVIEWERS

LIEGE_ADVICE_STATES_STILL_EDITABLE = ('advice_under_edit',
                                      'proposed_to_financial_controller',
                                      'proposed_to_financial_reviewer',
                                      'proposed_to_financial_manager', )
LIEGE_ADVICE_STATES_NO_MORE_EDITABLE = ('financial_advice_signed',
                                        'advice_given', )
PMconfig.ADVICE_STATES_STILL_EDITABLE = LIEGE_ADVICE_STATES_STILL_EDITABLE
PMconfig.ADVICE_STATES_NO_MORE_EDITABLE = LIEGE_ADVICE_STATES_NO_MORE_EDITABLE

# add field 'textCheckList' to field to keep while using itemtemplate
from Products.PloneMeeting import config
ML_EXTRA_COPIED_FIELDS_SAME_MC = config.EXTRA_COPIED_FIELDS_SAME_MC + ['textCheckList', ]
config.EXTRA_COPIED_FIELDS_SAME_MC = ML_EXTRA_COPIED_FIELDS_SAME_MC

# finance groups ids
FINANCE_GROUP_IDS = ['df-contrale', 'df-comptabilita-c-et-audit-financier', ]

FINANCE_GROUP_SUFFIXES = ('financialcontrollers',
                          'financialreviewers',
                          'financialmanagers')
# in those states, finance advice can still be given
FINANCE_GIVEABLE_ADVICE_STATES = ('proposed_to_finance', 'validated', 'presented', 'itemfrozen')
##/code-section config-bottom


# Load custom configuration not managed by archgenxml
try:
    from Products.MeetingLiege.AppConfig import *
except ImportError:
    pass
