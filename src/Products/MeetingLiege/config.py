# -*- coding: utf-8 -*-
#
# File: config.py
#
# Copyright (c) 2015 by Imio.be
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

LIEGE_ADVICE_STATES_ALIVE = ('advice_under_edit',
                             'proposed_to_financial_controller',
                             'proposed_to_financial_reviewer',
                             'proposed_to_financial_manager',
                             'financial_advice_signed', )
LIEGE_ADVICE_STATES_ENDED = ('advice_given', )
PMconfig.ADVICE_STATES_ALIVE = LIEGE_ADVICE_STATES_ALIVE
PMconfig.ADVICE_STATES_ENDED = LIEGE_ADVICE_STATES_ENDED

# add our custom inserting method
PMconfig.ITEM_INSERT_METHODS = PMconfig.ITEM_INSERT_METHODS + ('on_decision_first_word', )

# finance groups ids
FINANCE_GROUP_IDS = ['df-contrale', 'df-comptabilita-c-et-audit-financier', ]

FINANCE_GROUP_SUFFIXES = ('financialcontrollers',
                          'financialreviewers',
                          'financialmanagers')
# in those states, finance advice can still be given
FINANCE_GIVEABLE_ADVICE_STATES = ('proposed_to_finance', 'validated', 'presented', 'itemfrozen')

# comment used when a finance advice has been signed and so historized
FINANCE_ADVICE_HISTORIZE_COMMENTS = 'financial_advice_signed_historized_comments'

# text about FD advice used in templates
FINANCE_ADVICE_LEGAL_TEXT_PRE = "<p>Attendu la demande d'avis adressée sur "\
    "base d'un dossier complet au Directeur financier en date du {0}.<br/></p>"

FINANCE_ADVICE_LEGAL_TEXT = "<p>Attendu l'avis {0} du Directeur financier "\
    "annexé à la présente décision et rendu en date du {1} conformément à "\
    "l'article L1124-40 du Code de la démocratie locale et de la "\
    "décentralisation,</p>"

FINANCE_ADVICE_LEGAL_TEXT_NOT_GIVEN = "<p>Attendu l'absence d'avis du "\
    "Directeur financier rendu dans le délai prescrit à l'article L1124-40 "\
    "du Code de la démocratie locale et de la décentralisation,</p>"

COUNCILITEM_DECISIONEND_SENTENCE = u"<p>La présente décision a recueilli l'unanimité des suffrages.</p>".encode('utf-8')

##/code-section config-bottom


# Load custom configuration not managed by archgenxml
try:
    from Products.MeetingLiege.AppConfig import *
except ImportError:
    pass
