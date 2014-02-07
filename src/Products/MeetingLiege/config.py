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

__author__ = """Gauthier Bastien <g.bastien@imio.be>, Stephan Geulette <s.geulette@imio.be>"""
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
import os
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
LALOUVIEREROLES['budgetimpactreviewers'] = 'MeetingBudgetImpactReviewer'
LALOUVIEREROLES['serviceheads'] = 'MeetingServiceHead'
LALOUVIEREROLES['officemanagers'] = 'MeetingOfficeManager'
LALOUVIEREROLES['divisionheads'] = 'MeetingDivisionHead'
LALOUVIEREROLES['directors'] = 'MeetingDirector'
LALOUVIEREROLES['followupwriters'] = 'MeetingFollowUpWriter'
PMconfig.MEETINGROLES.update(LALOUVIEREROLES)
PMconfig.MEETING_GROUP_SUFFIXES = PMconfig.MEETINGROLES.keys()

# see doc in Products.PloneMeeting.config.py
RETURN_TO_PROPOSING_GROUP_MAPPINGS = {'backTo_item_in_committee_from_returned_to_proposing_group': ['in_committee', ],
                                      'backTo_item_in_council_from_returned_to_proposing_group': ['in_council', ],
                                      }
PMconfig.RETURN_TO_PROPOSING_GROUP_MAPPINGS.update(RETURN_TO_PROPOSING_GROUP_MAPPINGS)


# url of the DEF application
DEFURL = os.environ.get('DEFURL', 'http://192.168.1.106/def')

# ids of commissions used as categories for MeetingItemCouncil
# before 2013, commission ids were :
COUNCIL_COMMISSION_IDS = ('commission-travaux', 'commission-enseignement',
                          'commission-cadre-de-vie-et-logement', 'commission-ag',
                          'commission-finances-et-patrimoine', 'commission-police',
                          'commission-speciale',)
# until 2013, commission ids are :
# changes are about 'commission-enseignement', 'commission-cadre-de-vie-et-logement' and
# 'commission-finances-et-patrimoine' that are splitted in smaller commissions
COUNCIL_COMMISSION_IDS_2013 = ('commission-ag', 'commission-finances', 'commission-enseignement',
                               'commission-culture', 'commission-sport', 'commission-sante',
                               'commission-police', 'commission-cadre-de-vie', 'commission-patrimoine',
                               'commission-travaux', 'commission-speciale',)
# commissions taken into account on the Meeting
# since 2013, some commissions are made of several categories...
COUNCIL_MEETING_COMMISSION_IDS_2013 = ('commission-travaux',
                                       ('commission-ag', 'commission-finances', 'commission-enseignement',
                                        'commission-culture', 'commission-sport', 'commission-sante',),
                                       ('commission-cadre-de-vie', 'commission-patrimoine',),
                                       'commission-police',
                                       'commission-speciale',)


# suffix of specific groups containing commission transcript editors
COMMISSION_EDITORS_SUFFIX = '_commissioneditors'
##/code-section config-bottom


# Load custom configuration not managed by archgenxml
try:
    from Products.MeetingLalouviere.AppConfig import *
except ImportError:
    pass
