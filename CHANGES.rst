Products.MeetingLiege Changelog
===============================

4.1b10 (unreleased)
-------------------

- Products.PloneMeeting.utils.getLastEvent was removed, use imio.history.utils.getLastWFAction.
- Adapted profile regarding changes about integration of collective.contact.* in Products.PloneMeeting.

4.1b9 (2018-07-13)
------------------

- In onItemAfterTransition, use event.new_state.id instead item.queryState().
- Added test test_ItemTakenOverByFinancesAdviser.
- For WFA return to proposing group in Council, use 'itemcreated' state from
  'meetingitemcollegeliege_workflow' as it does not exist in the 'meetingitemcouncilliege_workflow'.
- Smaller logo.png.

4.1b8 (2018-05-09)
------------------

- Do not use member.getGroups, use ToolPloneMeeting.getPloneGroupsForUser that use caching.
- Adapted tests to use _addPrincipalToGroup and _removePrincipalFromGroup from PloneMeetingTestCase.

4.1b7 (2018-05-04)
------------------

- Decision annexes are no more kept in any duplication
- Simplify confidential annex management by giving access to non confidential annexes
  and using the default 'group in charge' parameter.  We adapt the MeetingItem.getGroupInCharge
  method to use the groupOfMatter to handle this

4.1b6 (2018-03-19)
------------------

- Fixed MeetingManager read access to items in review_state validated and following states
- Restricted access of MeetingObserverLocal to positive decided states in every item WF

4.1b5 (2018-03-07)
------------------

- Added state 'accepted_but_modified' in BG WF
- MeetingObserverLocal role is only given on items when it is at least 'validated'
- Give the 'PloneMeeting: Read budget infos' permission to Reader in every item review_states
- Added 'back' shortcuts in item administrative process WF of BG
- Removed 'itemcreated_waiting_advices' review_state leading icon as it is already added
  by PloneMeeting.  Just override the icon title to fit the review_state translation

4.1b4 (2018-02-23)
------------------

- Simplified 'mayCorrect' for meeting and item WF condition adapters
- BG WF : added  'backToProposedToDirector' from 'validated' state
- BG WF : changed validate transition/validated state title so it can be translated
  differently than in College/Council
- BG WF : do BG reviewer able to validate item in state 'proposed_to_cabinet_manager'
- BG WF : defined item validation WF shortcuts like it is made for College item

4.1b3 (2018-01-31)
------------------

- 'Accept and return' transition also works when item not to send to Council, in this case,
  item is just duplicated and not sent to Council
- Adapted config.MEETINGREVIEWERS format
- Define RETURN_TO_PROPOSING_GROUP_STATE_TO_CLONE for 'meetingitembourgmestre_workflow' so
  'return_to_proposing_group' wfAdaptation is selectable
- Do not bind default workflow for Meeting/MeetingItem types so reapplying the workflows.xml
  portal_setup step do not change workflow selected on these types as it is different when
  managed by the MeetingConfig

4.1b2 (2018-01-23)
------------------
- Added 'Bourgmestre' MeetingConfig (workflow, adapters, ...) :
  - main_infos history on item
  - bourgmestre WFs for item and meeting
  - hide history transitions for relevant roles

4.1b1 (2017-12-01)
------------------
- When an item is sent from College to Council, keep the 'toDiscuss' field
- Do not call at_post_edit_script directly anymore, use Meeting(Item)._update_after_edit
- Moved to advanced tests/helpers.WF_STATE_NAME_MAPPINGS from PloneMeeting

4.0 (2017-08-18)
----------------
- Finance advisers of an item are now able to add decision annexes
  when the item is decided
- Added possibility to manage MeetingItem.itemIsSigned when item is
  'presented' or 'itemfrozen' besides the fact that it is still manageable
  when the item is decided
- Added a 'Echevinat' faceted advanced criterion based on groupsOfMatter index
- Moved historization of signed financial advice to real versions
- Added listType 'Addendum' for items of Council (added possibility to define 'items
  without a number' as well)
- Added possibility to manually send items from College to Council once item is 'itemfrozen'
- Restricted power observers may not see 'late' council items if not decided
- Added state 'sent_to_council_emergency' on a College item to make it possible
  to keep a link between a College item and a Council item emergency if the original
  College item was not linked to a meeting
- When a Council item is 'delayed', it is automatically sent back to College in 'itemcreated'
  state to make full validation process again in College to be sent again in Council, finance
  advice does not follow
- When a Council item is 'returned', it is automatically sent back to College in 'validated'
  state to be immediatelly presentable in a next meeting, finance advice does follow
- When a Council item is presented, automatically add the COUNCILITEM_DECISIONEND_SENTENCE at
  the end of the item's decisionEnd if not already
- Make sure a MeetingGroup may not be removed if used in MeetingConfig.archivingRefs or
  MeetingCategory.groupsOfMatter
- Do only let ask advices (by item creator or internal reviewer) if some advices will be giveable in
  the state the item will be (itemcreated_waiting_advices or
  proposed_to_internal_reviewer_waiting_advices)
- When a College item was sent to Council (when it was frozen) and the final decision on the College item
  is "delayed", delete the item that was sent to the Council
- Do every manuallyLinkedItems of an item having finance advice accessible to the finance advisers
- Hide some elements for restricted power observers : some fileters, columns and access to element's history
- Added 'positive_with_remarks_finance' to the list of advice_type selectable by finance advisers,
  this behaves exactly like 'positive_finance' in every cases, except the icon that shows to the user
  that a comment has been added to the advice
- Power observers (not restricted) may access every decision annexes
- When an item is 'returned', keep original creator for duplicated items
- Do not rely on Products.MeetingCommunes for the testing part as we do not
  override every PM tests in MC, we just heritate from PM test file
- Get rid of ToolPloneMeeting.formatMeetingDate override that displayed a '*' for meetings where
  adoptsNextCouncilAgenda=True, we use imio.prettylink _leadingIcons now
- Moved finances specific advices to their own portal_type 'meetingadvicefinances'
- Removed field 'MeetingItem.privacyForCouncil', instead we will use new builtin PM functionnality 
  'MeetingItem.otherMeetingConfigsClonableToPrivacy' that does the same