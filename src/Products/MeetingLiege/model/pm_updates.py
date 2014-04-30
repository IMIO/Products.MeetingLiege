from Products.Archetypes.atapi import LinesField
from Products.Archetypes.atapi import MultiSelectionWidget
from Products.Archetypes.atapi import Schema

from Products.PloneMeeting.MeetingConfig import MeetingConfig


def update_config_schema(baseSchema):
    specificSchema = Schema((
        LinesField(
            name='financialGroups',
            widget=MultiSelectionWidget(
                size=10,
                description="FinancialGroups",
                description_msgid="financial_groups_descr",
                label='Financialgroups',
                label_msgid='PloneMeeting_label_financialGroups',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
            multiValued=1,
            vocabulary='listActiveMeetingGroups',
        ),

    ),)

    completeConfigSchema = baseSchema + specificSchema.copy()
    return completeConfigSchema
MeetingConfig.schema = update_config_schema(MeetingConfig.schema)


# Classes have already been registered, but we register them again here
# because we have potentially applied some schema adaptations (see above).
# Class registering includes generation of accessors and mutators, for
# example, so this is why we need to do it again now.
from Products.PloneMeeting.config import registerClasses
registerClasses()
