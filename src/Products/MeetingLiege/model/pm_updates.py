from Products.Archetypes.atapi import *
from Products.PloneMeeting.Meeting import Meeting
from Products.PloneMeeting.MeetingItem import MeetingItem
from Products.PloneMeeting.MeetingGroup import MeetingGroup
from Products.PloneMeeting.MeetingConfig import MeetingConfig


def update_config_schema(baseSchema):
    specificSchema = Schema((
        TextField(
            name='preMeetingAssembly_default',
            widget=TextAreaWidget(
                condition="python: 'preMeetingAssembly' in here.getUsedMeetingAttributes()",
                description="PreMeetingAssembly",
                description_msgid="premeeting_assembly_descr",
                label='Premeetingassembly',
                label_msgid='MeetingLalouviere_label_preMeetingAssembly_default',
                i18n_domain='PloneMeeting',
                label_method='getLabelPreMeetingAssembly_default'
            ),
        ),
        TextField(
            name='preMeetingAssembly_2_default',
            widget=TextAreaWidget(
                condition="python: 'preMeetingAssembly_2' in here.getUsedMeetingAttributes()",
                description="PreMeetingAssembly_2",
                description_msgid="premeeting_assembly_2_descr",
                label='Premeetingassembly_2',
                label_msgid='MeetingLalouviere_label_preMeetingAssembly_2_default',
                i18n_domain='PloneMeeting',
            ),
        ),
        TextField(
            name='preMeetingAssembly_3_default',
            widget=TextAreaWidget(
                condition="python: 'preMeetingAssembly_3' in here.getUsedMeetingAttributes()",
                description="PreMeetingAssembly_3",
                description_msgid="premeeting_assembly_3_descr",
                label='Premeetingassembly_3',
                label_msgid='MeetingLalouviere_label_preMeetingAssembly_3_default',
                i18n_domain='PloneMeeting',
            ),
        ),
        TextField(
            name='preMeetingAssembly_4_default',
            widget=TextAreaWidget(
                condition="python: 'preMeetingAssembly_4' in here.getUsedMeetingAttributes()",
                description="PreMeetingAssembly_4",
                description_msgid="premeeting_assembly_4_descr",
                label='Premeetingassembly_4',
                label_msgid='MeetingLalouviere_label_preMeetingAssembly_4_default',
                i18n_domain='PloneMeeting',
            ),
        ),
        TextField(
            name='preMeetingAssembly_5_default',
            widget=TextAreaWidget(
                condition="python: 'preMeetingAssembly_5' in here.getUsedMeetingAttributes()",
                description="PreMeetingAssembly_5",
                description_msgid="premeeting_assembly_5_descr",
                label='Premeetingassembly_5',
                label_msgid='MeetingLalouviere_label_preMeetingAssembly_5_default',
                i18n_domain='PloneMeeting',
            ),
        ),
        TextField(
            name='preMeetingAssembly_6_default',
            widget=TextAreaWidget(
                condition="python: 'preMeetingAssembly_6' in here.getUsedMeetingAttributes()",
                description="PreMeetingAssembly_6",
                description_msgid="premeeting_assembly_6_descr",
                label='Premeetingassembly_6',
                label_msgid='MeetingLalouviere_label_preMeetingAssembly_6_default',
                i18n_domain='PloneMeeting',
            ),
        ),
        TextField(
            name='preMeetingAssembly_7_default',
            widget=TextAreaWidget(
                condition="python: 'preMeetingAssembly_7' in here.getUsedMeetingAttributes()",
                description="PreMeetingAssembly_7",
                description_msgid="premeeting_assembly_7_descr",
                label='Premeetingassembly_7',
                label_msgid='MeetingLalouviere_label_preMeetingAssembly_7_default',
                i18n_domain='PloneMeeting',
            ),
        ),

    ),)

    completeConfigSchema = baseSchema + specificSchema.copy()
    return completeConfigSchema
MeetingConfig.schema = update_config_schema(MeetingConfig.schema)


def update_group_schema(baseSchema):
    specificSchema = Schema((

        # field used to define specific signatures for a MeetingGroup
        TextField(
            name='signatures',
            widget=TextAreaWidget(
                label='Signatures',
                label_msgid='MeetingLalouviere_label_signatures',
                description='Leave empty to use the signatures defined on the meeting',
                description_msgid='MeetingLalouviere_descr_signatures',
                i18n_domain='PloneMeeting',
            ),
        ),
    ),)

    completeGroupSchema = baseSchema + specificSchema.copy()

    return completeGroupSchema
MeetingGroup.schema = update_group_schema(MeetingGroup.schema)


def update_meeting_schema(baseSchema):
    specificSchema = Schema((

        TextField(
            name='preMeetingAssembly',
            allowable_content_types="text/plain",
            optional=True,
            widget=TextAreaWidget(
                condition="python: here.attributeIsUsed('preMeetingAssembly')",
                description="PreMeetingAssembly",
                description_msgid="premeeting_assembly_descr",
                label='Premeetingassembly',
                label_msgid='MeetingLalouviere_label_preMeetingAssembly',
                i18n_domain='PloneMeeting',
            ),
            default_output_type="text/html",
            default_method="getDefaultPreMeetingAssembly",
            default_content_type="text/plain",
        ),
        DateTimeField(
            name='preMeetingDate_2',
            widget=DateTimeField._properties['widget'](
                condition="python: here.attributeIsUsed('preMeetingDate_2')",
                label='Premeetingdate_2',
                label_msgid='PloneMeeting_label_preMeetingDate_2',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
        ),
        StringField(
            name='preMeetingPlace_2',
            widget=StringField._properties['widget'](
                condition="python: here.attributeIsUsed('preMeetingPlace_2')",
                label='Premeetingplace_2',
                label_msgid='PloneMeeting_label_preMeetingPlace_2',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
        ),
        TextField(
            name='preMeetingAssembly_2',
            allowable_content_types="text/plain",
            optional=True,
            widget=TextAreaWidget(
                condition="python: here.attributeIsUsed('preMeetingAssembly_2')",
                description="PreMeetingAssembly_2",
                description_msgid="premeeting_assembly_2_descr",
                label='Premeetingassembly_2',
                label_msgid='MeetingLalouviere_label_preMeetingAssembly_2',
                i18n_domain='PloneMeeting',
            ),
            default_output_type="text/html",
            default_method="getDefaultPreMeetingAssembly_2",
            default_content_type="text/plain",
        ),
        DateTimeField(
            name='preMeetingDate_3',
            widget=DateTimeField._properties['widget'](
                condition="python: here.attributeIsUsed('preMeetingDate_3')",
                label='Premeetingdate_3',
                label_msgid='PloneMeeting_label_preMeetingDate_3',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
        ),
        StringField(
            name='preMeetingPlace_3',
            widget=StringField._properties['widget'](
                condition="python: here.attributeIsUsed('preMeetingPlace_3')",
                label='Premeetingplace_3',
                label_msgid='PloneMeeting_label_preMeetingPlace_3',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
        ),
        TextField(
            name='preMeetingAssembly_3',
            allowable_content_types="text/plain",
            optional=True,
            widget=TextAreaWidget(
                condition="python: here.attributeIsUsed('preMeetingAssembly_3')",
                description="PreMeetingAssembly_3",
                description_msgid="premeeting_assembly_3_descr",
                label='Premeetingassembly_3',
                label_msgid='MeetingLalouviere_label_preMeetingAssembly_3',
                i18n_domain='PloneMeeting',
            ),
            default_output_type="text/html",
            default_method="getDefaultPreMeetingAssembly_3",
            default_content_type="text/plain",
        ),
        DateTimeField(
            name='preMeetingDate_4',
            widget=DateTimeField._properties['widget'](
                condition="python: here.attributeIsUsed('preMeetingDate_4')",
                label='Premeetingdate_4',
                label_msgid='PloneMeeting_label_preMeetingDate_4',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
        ),
        StringField(
            name='preMeetingPlace_4',
            widget=StringField._properties['widget'](
                condition="python: here.attributeIsUsed('preMeetingPlace_4')",
                label='Premeetingplace_4',
                label_msgid='PloneMeeting_label_preMeetingPlace_4',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
        ),
        TextField(
            name='preMeetingAssembly_4',
            allowable_content_types="text/plain",
            optional=True,
            widget=TextAreaWidget(
                condition="python: here.attributeIsUsed('preMeetingAssembly_4')",
                description="PreMeetingAssembly_4",
                description_msgid="premeeting_assembly_4_descr",
                label='Premeetingassembly_4',
                label_msgid='MeetingLalouviere_label_preMeetingAssembly_4',
                i18n_domain='PloneMeeting',
            ),
            default_output_type="text/html",
            default_method="getDefaultPreMeetingAssembly_4",
            default_content_type="text/plain",
        ),
        DateTimeField(
            name='preMeetingDate_5',
            widget=DateTimeField._properties['widget'](
                condition="python: here.attributeIsUsed('preMeetingDate_5')",
                label='Premeetingdate_5',
                label_msgid='PloneMeeting_label_preMeetingDate_5',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
        ),
        StringField(
            name='preMeetingPlace_5',
            widget=StringField._properties['widget'](
                condition="python: here.attributeIsUsed('preMeetingPlace_5')",
                label='Premeetingplace_5',
                label_msgid='PloneMeeting_label_preMeetingPlace_5',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
        ),
        TextField(
            name='preMeetingAssembly_5',
            allowable_content_types="text/plain",
            optional=True,
            widget=TextAreaWidget(
                condition="python: here.attributeIsUsed('preMeetingAssembly_5')",
                description="PreMeetingAssembly_5",
                description_msgid="premeeting_assembly_5_descr",
                label='Premeetingassembly_5',
                label_msgid='MeetingLalouviere_label_preMeetingAssembly_5',
                i18n_domain='PloneMeeting',
            ),
            default_output_type="text/html",
            default_method="getDefaultPreMeetingAssembly_5",
            default_content_type="text/plain",
        ),
        DateTimeField(
            name='preMeetingDate_6',
            widget=DateTimeField._properties['widget'](
                condition="python: here.attributeIsUsed('preMeetingDate_6')",
                label='Premeetingdate_6',
                label_msgid='PloneMeeting_label_preMeetingDate_6',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
        ),
        StringField(
            name='preMeetingPlace_6',
            widget=StringField._properties['widget'](
                condition="python: here.attributeIsUsed('preMeetingPlace_6')",
                label='Premeetingplace_6',
                label_msgid='PloneMeeting_label_preMeetingPlace_6',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
        ),
        TextField(
            name='preMeetingAssembly_6',
            allowable_content_types="text/plain",
            optional=True,
            widget=TextAreaWidget(
                condition="python: here.attributeIsUsed('preMeetingAssembly_6')",
                description="PreMeetingAssembly_6",
                description_msgid="premeeting_assembly_6_descr",
                label='Premeetingassembly_6',
                label_msgid='MeetingLalouviere_label_preMeetingAssembly_6',
                i18n_domain='PloneMeeting',
            ),
            default_output_type="text/html",
            default_method="getDefaultPreMeetingAssembly_6",
            default_content_type="text/plain",
        ),
        DateTimeField(
            name='preMeetingDate_7',
            widget=DateTimeField._properties['widget'](
                condition="python: here.attributeIsUsed('preMeetingDate_7')",
                label='Premeetingdate_7',
                label_msgid='PloneMeeting_label_preMeetingDate_7',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
        ),
        StringField(
            name='preMeetingPlace_7',
            widget=StringField._properties['widget'](
                condition="python: here.attributeIsUsed('preMeetingPlace_7')",
                label='Premeetingplace_7',
                label_msgid='PloneMeeting_label_preMeetingPlace_7',
                i18n_domain='PloneMeeting',
            ),
            optional=True,
        ),
        TextField(
            name='preMeetingAssembly_7',
            allowable_content_types="text/plain",
            optional=True,
            widget=TextAreaWidget(
                condition="python: here.attributeIsUsed('preMeetingAssembly_7')",
                description="PreMeetingAssembly_7",
                description_msgid="premeeting_assembly_7_descr",
                label='Premeetingassembly_7',
                label_msgid='MeetingLalouviere_label_preMeetingAssembly_7',
                i18n_domain='PloneMeeting',
            ),
            default_output_type="text/html",
            default_method="getDefaultPreMeetingAssembly_7",
            default_content_type="text/plain",
        ),

    ),)

    baseSchema['observations'].widget.label_method = "getLabelObservations"

    completeMeetingSchema = baseSchema + specificSchema.copy()
    return completeMeetingSchema
Meeting.schema = update_meeting_schema(Meeting.schema)


def update_item_schema(baseSchema):

    specificSchema = Schema((
        #specific field for council added for MeetingManagers to transcribe interventions
        TextField(
            name='interventions',
            widget=RichWidget(
                rows=15,
                condition="python: here.portal_type == 'MeetingItemCouncil' and here.portal_plonemeeting.isManager()",
                label='Interventions',
                label_msgid='MeetingLalouviere_label_interventions',
                description='Transcription of interventions',
                description_msgid='MeetingLalouviere_descr_interventions',
                i18n_domain='PloneMeeting',
            ),
            default_content_type="text/html",
            searchable=True,
            allowable_content_types=('text/html',),
            default_output_type="text/html",
        ),
        #specific field for council added for MeetingManagers to transcribe interventions
        TextField(
            name='commissionTranscript',
            widget=RichWidget(
                rows=15,
                condition="python: here.portal_type == 'MeetingItemCouncil'",
                label='CommissionTranscript',
                label_msgid='MeetingLalouviere_label_commissionTranscript',
                description='Transcription of commission',
                description_msgid='MeetingLalouviere_descr_commissionTranscript',
                i18n_domain='PloneMeeting',
            ),
            default_content_type="text/html",
            default="<p>N&eacute;ant</p>",
            searchable=True,
            allowable_content_types=('text/html',),
            default_output_type="text/html",
            write_permission = "MeetingLalouviere: Write commission transcript",
            read_permission = "MeetingLalouviere: Read commission transcript",
        ),
        #here above are 3 specific fields for managing item follow-up
        StringField(
            name='followUp',
            default="follow_up_no",
            widget=SelectionWidget(
                condition="python: here.attributeIsUsed('neededFollowUp') and "
                          "here.queryState() in here.itemDecidedStates",
                description="A follow up is needed : no, yes, provided?",
                description_msgid="MeetingLalouviere_descr_followUp",
                label='FollowUp',
                label_msgid='MeetingLalouviere_label_followUp',
                i18n_domain='PloneMeeting',
            ),
            vocabulary='listFollowUps',
            write_permission = "MeetingLalouviere: Write followUp",
            read_permission = "MeetingLalouviere: Read followUp",
        ),
        TextField(
            name='neededFollowUp',
            optional=True,
            widget=RichWidget(
                rows=15,
                condition="python: here.attributeIsUsed('neededFollowUp') and "
                          "here.queryState() in here.itemDecidedStates",
                label='NeededFollowUp',
                label_msgid='MeetingLalouviere_label_neededFollowUp',
                description='Follow-up needed for this item',
                description_msgid='MeetingLalouviere_descr_neededFollowUp',
                i18n_domain='PloneMeeting',
            ),
            default_content_type="text/html",
            searchable=True,
            allowable_content_types=('text/html',),
            default_output_type="text/html",
            write_permission = "MeetingLalouviere: Write neededFollowUp",
            read_permission = "MeetingLalouviere: Read neededFollowUp",
        ),
        TextField(
            name='providedFollowUp',
            optional=True,
            widget=RichWidget(
                rows=15,
                condition="python: here.attributeIsUsed('providedFollowUp') and "
                          "here.queryState() in here.itemDecidedStates",
                label='ProvidedFollowUp',
                label_msgid='MeetingLalouviere_label_providedFollowUp',
                description='Follow-up provided for this item',
                description_msgid='MeetingLalouviere_descr_providedFollowUp',
                i18n_domain='PloneMeeting',
            ),
            default_content_type="text/html",
            default="<p>N&eacute;ant</p>",
            searchable=True,
            allowable_content_types=('text/html',),
            default_output_type="text/html",
            write_permission = "MeetingLalouviere: Write providedFollowUp",
            read_permission = "MeetingLalouviere: Read providedFollowUp",
        ),

    ),)

    baseSchema['budgetInfos'].write_permission = "MeetingLalouviere: Write budget infos"
    baseSchema['budgetInfos'].read_permission = "MeetingLalouviere: Read budget infos"
    baseSchema['description'].widget.label_method = "getLabelDescription"
    baseSchema['category'].widget.label_method = "getLabelCategory"
    baseSchema['privacy'].widget.condition = "python: here.attributeIsUsed('privacy') and " \
                                             "portal.portal_plonemeeting.isManager()"
    baseSchema['decision'].default = '<p>DECIDE :</p>'

    completeItemSchema = baseSchema + specificSchema.copy()
    return completeItemSchema
MeetingItem.schema = update_item_schema(MeetingItem.schema)


# Classes have already been registered, but we register them again here
# because we have potentially applied some schema adaptations (see above).
# Class registering includes generation of accessors and mutators, for
# example, so this is why we need to do it again now.
from Products.PloneMeeting.config import registerClasses
registerClasses()
