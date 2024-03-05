# -*- coding: utf-8 -*-

from Products.CMFCore.permissions import setDefaultRoles
from Products.PloneMeeting import config as PMconfig
from Products.PloneMeeting.config import ADVICE_STATES_MAPPING


__author__ = """Gauthier Bastien <g.bastien@imio.be>"""
__docformat__ = 'plaintext'

product_globals = globals()

PROJECTNAME = "MeetingLiege"

# Permissions
DEFAULT_ADD_CONTENT_PERMISSION = "Add portal content"
setDefaultRoles(DEFAULT_ADD_CONTENT_PERMISSION, ('Manager', 'Owner', 'Contributor'))

# group suffixes
PMconfig.EXTRA_GROUP_SUFFIXES = [
    {'fct_title': u'administrativereviewers',
     'fct_id': u'administrativereviewers',
     'fct_orgs': [],
     'fct_management': False,
     'enabled': True},
    {'fct_title': u'internalreviewers',
     'fct_id': u'internalreviewers',
     'fct_orgs': [],
     'fct_management': False,
     'enabled': True},
    {'fct_title': u'incopy',
     'fct_id': u'incopy',
     'fct_orgs': [],
     'fct_management': False,
     'enabled': True},
    {'fct_title': u'financialcontrollers',
     'fct_id': u'financialcontrollers',
     'fct_orgs': ['df-contrale', 'df-comptabilita-c-et-audit-financier'],
     'fct_management': False,
     'enabled': True},
    {'fct_title': u'financialreviewers',
     'fct_id': u'financialreviewers',
     'fct_orgs': ['df-contrale', 'df-comptabilita-c-et-audit-financier'],
     'fct_management': False,
     'enabled': True},
    {'fct_title': u'financialmanagers',
     'fct_id': u'financialmanagers',
     'fct_orgs': ['df-contrale', 'df-comptabilita-c-et-audit-financier'],
     'fct_management': False,
     'enabled': True},
]

FINANCE_GROUP_SUFFIXES = ('financialcontrollers',
                          'financialreviewers',
                          'financialmanagers')

ADVICE_STATES_MAPPING.update(
    {'proposed_to_financial_controller': 'financialcontrollers',
     'proposed_to_financial_reviewer': 'financialreviewers',
     'proposed_to_financial_manager': 'financialmanagers',
     'financial_advice_signed': 'financialmanagers',
     })

ITEM_MAIN_INFOS_HISTORY = 'main_infos_history'

FINANCE_GROUP_IDS = ['df-contrale', 'df-comptabilita-c-et-audit-financier', ]

TREASURY_GROUP_ID = 'df-controle-tresorerie'

NOT_COPY_GROUP_IDS = ['rh-recrutement', 'rh-gestion-administrative']

GENERAL_MANAGER_GROUP_ID = 'sc'

BOURGMESTRE_GROUP_ID = 'bourgmestre'

# in those states, finance advice can still be given
FINANCE_GIVEABLE_ADVICE_STATES = ('proposed_to_finance_waiting_advices',
                                  'validated',
                                  'presented',
                                  'itemfrozen')

# comment used when a finance advice has been signed and so historized
FINANCE_ADVICE_HISTORIZE_COMMENTS = 'financial_advice_signed_historized_comments'

# text about FD advice used in templates
FINANCE_ADVICE_LEGAL_TEXT_PRE = "<p>Attendu la demande d'avis adressée sur "\
    "base d'un dossier complet au Directeur financier en date du {0}.</p>"

FINANCE_ADVICE_LEGAL_TEXT = "<p>Attendu l'avis {0} du Directeur financier "\
    "rendu en date du {1} conformément à l'article L1124-40 du Code de la "\
    "démocratie locale et de la décentralisation,</p>"

FINANCE_ADVICE_LEGAL_TEXT_NOT_GIVEN = "<p>Attendu l'absence d'avis du "\
    "Directeur financier rendu dans le délai prescrit à l'article L1124-40 "\
    "du Code de la démocratie locale et de la décentralisation,</p>"

COUNCILITEM_DECISIONEND_SENTENCE = "<p>La présente décision a recueilli l'unanimité des suffrages.</p>"
COUNCILITEM_DECISIONEND_SENTENCE_RAW = "La présente décision a recueilli l'unanimité des suffrages."
