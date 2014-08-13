from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import TextField
from Products.Archetypes.atapi import SelectionWidget
from Products.Archetypes.atapi import TextAreaWidget
from Products.Archetypes.atapi import RichWidget

from Products.DataGridField import DataGridField
from Products.DataGridField import Column
from Products.DataGridField import SelectColumn

from collective.datagridcolumns.MultiSelectColumn import MultiSelectColumn

from Products.PloneMeeting.MeetingItem import MeetingItem
from Products.PloneMeeting.MeetingConfig import MeetingConfig


def update_item_schema(baseSchema):

    specificSchema = Schema((
        # field for defining label that will be used when the item is in the Council
        # in College, this is a proposal that will be copied to the item sent to Council
        TextField(
            name='labelForCouncil',
            widget=RichWidget(
                rows=15,
                condition="python: here.attributeIsUsed('labelForCouncil')",
                label='LabelForCouncil',
                label_msgid='MeetingLiege_label_labelForCouncil',
                description="Label of decision that will be used when the will be in the Council",
                description_msgid="MeetingLiege_descr_labelForCouncil",
                i18n_domain='PloneMeeting',
            ),
            default_content_type="text/html",
            searchable=True,
            allowable_content_types=('text/html',),
            default_output_type="text/x-html-safe",
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
            name='financeAdvice',
            widget=SelectionWidget(
                condition="python: here.attributeIsUsed('financeAdvice')",
                label='FinanceAdvice',
                label_msgid='MeetingLiege_label_financeAdvice',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
            vocabulary='listFinanceAdvices',
            default='_none_',
        ),
        StringField(
            name='archivingRef',
            widget=SelectionWidget(
                condition="python: here.attributeIsUsed('archivingRef')",
                label='ArchivingRef',
                label_msgid='MeetingLiege_label_archivingRef',
                description=" ",
                description_msgid="MeetingLiege_descr_archivingRef",
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
    # define some description_msgid not existing by default in PloneMeeting
    completeItemSchema['title'].widget.description_msgid = 'item_title_descr'
    completeItemSchema['description'].widget.description_msgid = 'item_description_descr'
    completeItemSchema['detailedDescription'].widget.description_msgid = 'item_detailed_description_descr'
    completeItemSchema['proposingGroup'].widget.description_msgid = 'item_proposing_group_descr'
    completeItemSchema['motivation'].widget.description_msgid = 'item_motivation_descr'
    completeItemSchema['decision'].widget.description_msgid = 'item_decision_descr'
    completeItemSchema['observations'].widget.description_msgid = 'item_observations_descr'

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
            # do not use 'finance_advice' column for now, replaced (definitively?) by field 'financeAdvice'
            columns=('row_id', 'code', 'label', 'restrict_to_groups', 'active'),
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
