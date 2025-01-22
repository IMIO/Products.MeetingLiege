# -*- coding: utf-8 -*-

from Products.Archetypes.atapi import RichWidget
from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import SelectionWidget
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import TextField
from Products.PloneMeeting.config import registerClasses
from Products.PloneMeeting.MeetingItem import MeetingItem


def update_item_schema(baseSchema):

    specificSchema = Schema((
        # field for defining label that will be used when the item is in the Council
        # in College, this is a proposal that will be copied to the item sent to Council
        TextField(
            name='otherMeetingConfigsClonableToFieldLabelForCouncil',
            widget=RichWidget(
                condition="python: here.attribute_is_used('otherMeetingConfigsClonableToFieldLabelForCouncil')",
                label_msgid="MeetingLiege_label_labelForCouncil",
                label='Description',
                description="",
                description_msgid="MeetingLiege_descr_labelForCouncil",
                i18n_domain='PloneMeeting',
            ),
            default_content_type="text/html",
            searchable=True,
            allowable_content_types=('text/html',),
            default_output_type="text/x-html-safe",
            optional=True,
        ),
        TextField(
            name='labelForCouncil',
            widget=RichWidget(
                condition="python: here.attribute_is_used('labelForCouncil')",
                label='LabelForCouncil',
                label_msgid='MeetingLiege_label_labelForCouncil',
                description="",
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
                condition="python: here.attribute_is_used('financeAdvice')",
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

    ),)

    completeItemSchema = baseSchema + specificSchema.copy()
    # define some description_msgid not existing by default in PloneMeeting
    completeItemSchema['title'].widget.description_msgid = 'item_title_descr'
    completeItemSchema['description'].widget.description_msgid = 'item_description_descr'
    completeItemSchema['detailedDescription'].widget.description_msgid = 'item_detailed_description_descr'
    completeItemSchema['proposingGroup'].widget.description_msgid = 'item_proposing_group_descr'
    completeItemSchema['motivation'].widget.description_msgid = 'item_motivation_descr'
    completeItemSchema['decision'].widget.description_msgid = 'item_decision_descr'
    completeItemSchema['decisionSuite'].widget.description_msgid = 'item_decision_suite_descr'
    completeItemSchema['decisionEnd'].widget.description_msgid = 'item_decision_end_descr'
    completeItemSchema['observations'].widget.description_msgid = 'item_observations_descr'
    # use a specific condition to show field 'otherMeetingConfigsClonableToEmergency'
    completeItemSchema['otherMeetingConfigsClonableToEmergency'].widget.condition = \
        'python: here.adapted().showOtherMeetingConfigsClonableToEmergency()'

    return completeItemSchema


MeetingItem.schema = update_item_schema(MeetingItem.schema)

registerClasses()
