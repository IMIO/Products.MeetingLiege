from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import TextField
from Products.Archetypes.atapi import SelectionWidget
from Products.Archetypes.atapi import TextAreaWidget

from Products.DataGridField import DataGridField
from Products.DataGridField import Column
from Products.DataGridField import SelectColumn

from collective.datagridcolumns.MultiSelectColumn import MultiSelectColumn

from Products.PloneMeeting.MeetingItem import MeetingItem
from Products.PloneMeeting.MeetingConfig import MeetingConfig


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
        # field for defining privacy that will be used for item created in the Council
        StringField(
            name='privacyForCouncil',
            default='public',
            widget=SelectionWidget(
                condition="python: here.attributeIsUsed('privacyForCouncil')",
                label='PrivacyForCouncil',
                label_msgid='MeetingLiege_label_privacyForCouncil',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
            vocabulary='listPrivacyValues',
        ),
        StringField(
            name='archivingRef',
            widget=SelectionWidget(
                condition="python: here.attributeIsUsed('archivingRef')",
                label='ArchivingRef',
                label_msgid='MeetingLiege_label_archivingRef',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
            vocabulary='listArchivingRefs',
            default='_none_',
        ),
        TextField(
            name='textCheckList',
            allowable_content_types=('text/plain',),
            optional=True,
            widget=TextAreaWidget(
                condition="python: here.attributeIsUsed('textCheckList')",
                description="Enter elements that are necessary for this kind of item",
                description_msgid="MeetingLiege_descr_textCheckList",
                label='TextCheckList',
                label_msgid='MeetingLiege_label_textCheckList',
                i18n_domain='PloneMeeting',
            ),
            write_permission="Manage portal",
            default_output_type="text/x-html-safe",
            default_content_type="text/plain",
        ),
    ),)

    completeItemSchema = baseSchema + specificSchema.copy()
    return completeItemSchema
MeetingItem.schema = update_item_schema(MeetingItem.schema)


def update_config_schema(baseSchema):

    specificSchema = Schema((
        # field for defining title that will be used for item created in the Council
        DataGridField(
            # very strange bug when using a field name ending with 'References'...
            name='archivingRefs',
            widget=DataGridField._properties['widget'](
                description="ArchivingRefs",
                description_msgid="archiving_refs_descr",
                columns={'row_id': Column("Archiving reference row id", visible=False),
                         'code': Column("Archiving reference code"),
                         'label': Column("Archiving reference label"),
                         'finance_advice': SelectColumn("Archiving reference finance advice",
                                                        vocabulary="listArchivingReferenceFinanceAdvices"),
                         'restrict_to_groups': MultiSelectColumn("Archiving reference restrict to selected groups",
                                                                 vocabulary="listActiveMeetingGroupsForArchivingRefs"),
                         'active': SelectColumn("Archiving reference active?",
                                                vocabulary="listBooleanVocabulary",
                                                default='1'),
                         },
                label='ArchivingRefs',
                label_msgid='MeetingLiege_label_archivingRefs',
                i18n_domain='PloneMeeting',
            ),
            allow_oddeven=True,
            default=(),
            columns=('row_id', 'code', 'label', 'finance_advice', 'restrict_to_groups', 'active'),
            allow_empty_rows=False,
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
