from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import SelectionWidget
from Products.PloneMeeting.MeetingItem import MeetingItem


def update_item_schema(baseSchema):

    specificSchema = Schema((
        # field for defining title that will be used for item created in the Council
        StringField(
            name='titleForCouncil',
            widget=StringField._properties['widget'](
                condition="python: here.attributeIsUsed('titleForCouncil')",
                description="Title that will be used for the item created in the Council",
                description_msgid="MeetingLiege_descr_titleForCouncil",
                label='TitleForCouncil',
                label_msgid='MeetingLiege_label_titleForCouncil',
                i18n_domain='PloneMeeting',
                maxlength='500',
            ),
            optional=True,
        ),

        StringField(
            name='privacyForCouncil',
            default='public',
            widget=SelectionWidget(
                condition="python: here.attributeIsUsed('privacyForCouncil')",
                label='PrivacyForCouncil',
                label_msgid='PloneMeeting_label_privacyForCouncil',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
            vocabulary='listPrivacyValues',
        ),

    ),)

    completeItemSchema = baseSchema + specificSchema.copy()
    return completeItemSchema
MeetingItem.schema = update_item_schema(MeetingItem.schema)


# Classes have already been registered, but we register them again here
# because we have potentially applied some schema adaptations (see above).
# Class registering includes generation of accessors and mutators, for
# example, so this is why we need to do it again now.
from Products.PloneMeeting.config import registerClasses
registerClasses()
