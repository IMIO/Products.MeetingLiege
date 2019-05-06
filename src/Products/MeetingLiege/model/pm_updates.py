from collective.datagridcolumns.MultiSelectColumn import MultiSelectColumn
from Products.Archetypes.atapi import BooleanField
from Products.Archetypes.atapi import LinesField
from Products.Archetypes.atapi import MultiSelectionWidget
from Products.Archetypes.atapi import RichWidget
from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import SelectionWidget
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import TextField
from Products.DataGridField import Column
from Products.DataGridField import DataGridField
from Products.DataGridField import SelectColumn
from Products.PloneMeeting.config import registerClasses
from Products.PloneMeeting.config import WriteRiskyConfig
from Products.PloneMeeting.Meeting import Meeting
from Products.PloneMeeting.MeetingCategory import MeetingCategory
from Products.PloneMeeting.MeetingConfig import MeetingConfig
from Products.PloneMeeting.MeetingItem import MeetingItem


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
        StringField(
            name='financeAdvice',
            widget=SelectionWidget(
                condition="python: here.attributeIsUsed('financeAdvice')",
                description="If necessary, select the financial service that will have to "
                            "give the legal financial advice on this item",
                description_msgid="MeetingLiege_descr_financeAdvice",
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
            name='decisionSuite',
            widget=RichWidget(
                rows=15,
                condition="python: here.attributeIsUsed('decisionSuite')",
                label='DecisionSuite',
                label_msgid='MeetingLiege_label_decisionSuite',
                description="Decision suite descr",
                description_msgid="item_decision_suite_descr",
                i18n_domain='PloneMeeting',
            ),
            read_permission="PloneMeeting: Read decision",
            searchable=True,
            allowable_content_types=('text/html',),
            default_content_type="text/html",
            default_output_type="text/x-html-safe",
            write_permission="PloneMeeting: Write decision",
            optional=True,
        ),
        TextField(
            name='decisionEnd',
            widget=RichWidget(
                rows=15,
                condition="python: here.attributeIsUsed('decisionEnd')",
                label='DecisionEnd',
                label_msgid='MeetingLiege_label_decisionEnd',
                description="Decision end descr",
                description_msgid="item_decision_end_descr",
                i18n_domain='PloneMeeting',
            ),
            read_permission="PloneMeeting: Read decision",
            searchable=True,
            allowable_content_types=('text/html',),
            default_content_type="text/html",
            default_output_type="text/x-html-safe",
            write_permission="PloneMeeting: Write decision",
            optional=True,
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
    # use a specific condition to show field 'otherMeetingConfigsClonableToEmergency'
    completeItemSchema['otherMeetingConfigsClonableToEmergency'].widget.condition = \
        'python: here.adapted().showOtherMeetingConfigsClonableToEmergency()'

    return completeItemSchema
MeetingItem.schema = update_item_schema(MeetingItem.schema)


def update_meeting_schema(baseSchema):

    specificSchema = Schema((
        # field for defining if a college meeting adopts next council meeting agenda
        BooleanField(
            name='adoptsNextCouncilAgenda',
            default=False,
            widget=BooleanField._properties['widget'](
                condition="python: here.attributeIsUsed('adoptsNextCouncilAgenda')",
                description="AdoptsNextCouncilAgenda",
                description_msgid="adopts_next_council_agenda_descr",
                label='Adoptsnextcouncilagenda',
                label_msgid='MeetingLiege_label_adoptsNextCouncilAgenda',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
        ),
    ),)

    completeConfigSchema = baseSchema + specificSchema.copy()
    return completeConfigSchema
Meeting.schema = update_meeting_schema(Meeting.schema)


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
                         'restrict_to_groups': MultiSelectColumn("Archiving reference restrict to selected groups",
                                                                 vocabulary="listActiveOrgsForArchivingRefs"),
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
            write_permission=WriteRiskyConfig,
        ),
    ),)

    completeConfigSchema = baseSchema + specificSchema.copy()
    return completeConfigSchema
MeetingConfig.schema = update_config_schema(MeetingConfig.schema)


def update_category_schema(baseSchema):

    specificSchema = Schema((
        # field for defining a group that is responsible for this category and
        # that will be able to see every items using this category once this item is validated
        LinesField(
            name='groupsOfMatter',
            widget=MultiSelectionWidget(
                size=10,
                description="GroupsOfMatter",
                description_msgid="groups_of_matter_descr",
                label='Groupsofmatter',
                label_msgid='MeetingLiege_label_GroupsOfMatter',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
            multiValued=1,
            vocabulary='listGroupsOfMatter',
        ),
    ),)

    completeCategorySchema = baseSchema + specificSchema.copy()
    return completeCategorySchema
MeetingCategory.schema = update_category_schema(MeetingCategory.schema)


registerClasses()
