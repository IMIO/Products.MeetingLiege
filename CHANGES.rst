Products.MeetingLiege Changelog
===============================

4.2.14 (2025-08-28)
-------------------

- In `MLItemDocumentGenerationHelperView.printActeContentForCouncil`, insert
  `votesResult` before `decisionEnd` when `include_decisionEnd=True`.
  [gbastien]

4.2.13 (2025-04-02)
-------------------

- Adapted `MeetingItemCollegeLiegeWorkflowConditions.mayDecide` to use
  `Meeting.is_decided` so it fixes `testWFAdaptations.test_pm_WFA_no_decide`.
  [gbastien]
- On the `MeetingItem` view, do not `includeAuto=True` for groups in charge,
  display really stored groups in charge.
  [gbastien]

4.2.12 (2025-02-04)
-------------------

- When finances advice is negative, automatically send the item back to the
  internal reviewer instead sending it back to the director.
  [gbastien]
- Removed custom field `MeetingItem.archivingRef`,
  we use `MeetingItem.classifier` instead.
  [gbastien]

4.2.11 (2024-04-23)
-------------------

- Removed field `advice_substep_number` from `meetingadvicefinances.xml`.
  [gbastien]
- Fixed testing `import_data` configs title.
  [gbastien]
- Renamed `test_pm_WFA_waiting_advices` to `test_pm_WFA_waiting_advices_base`.
  [gbastien]
- Use custom icon for WF transition `wait_advices_from_proposed_to_director`
  to use a `€` icon.
  [gbastien]

4.2.10 (2024-03-05)
-------------------

- Adapted code for `ToolPloneMeeting.advisersConfig`, added upgrade step to 4201.
  [gbastien]

4.2.9 (2023-10-05)
------------------

- Fixed translation of `Data that will be used on new item` on `meetingitem_view.pt`.
  [gbastien]
- Fixed `MLAdviceActionsPanelView` that inherits from `AdviceActionsPanelView` and
  not `BaseActionsPanelView` so we get the `renderOwnDeleteWithComments`.
  [gbastien]
- Adapted code as `MeetingConfig.useCopies` field was removed.
  [gbastien]

4.2.8 (2023-03-20)
------------------

- Fixed cachekey for `CustomMeetingItem._roles_in_context`.
  [gbastien]
- Fixed `meetingitem_view.pt` to use `structure` to display groups in charge.
  [gbastien]
- `ToolPloneMeeting.get_plone_groups_for_user` is deprecated,
  use `imio.helpers.cache.get_plone_groups_for_user` instead.
  [gbastien]
- Advices is no more using Plone versioning, removed `repositorytool.xml`
  from `default` profile (migration is managed by `Products.PloneMeeting`),
  fixed code and tests.
  [gbastien]
- Updated `meetingitem_view` regarding changes in `PloneMeeting`
  (votesResult after motivation or after decision).
  [gbastien]
- Adapted code regarding removal of `MeetingConfig.useGroupsAsCategories`.
  [gbastien]

4.2.7 (2022-09-22)
------------------

- Adapted `MeetingItem._annex_decision_addable_states_after_validation`
  to make decision annexes addable in every item WF states.
  [gbastien]
- Use new adaptable method
  `MeetingItem._assign_roles_to_all_groups_managing_item_suffixes`
  to manage managing groups access to the `Bourgmestre` item.
  [gbastien]

4.2.6 (2022-07-11)
------------------

- Fixed `CustomMeetingItem.mayGenerateFDAdvice`, `False` for an `ItemTemplate`.
  [gbastien]

4.2.5 (2022-06-17)
------------------

- Fixed item pretty link icon `wf_down_finances.png` was displayed on BG items,
  must only be displayed on College items.
  [gbastien]
- Don't fail printActeContentForCollege if no category supplied.
  [odelaere]
- Bypass `test_pm_SendItemToOtherMCTransitionsTriggeredOnlyWhenAutomaticOrHasMeeting`
  as item created in `cfg2` is directly `validated`.
  [gbastien]

4.2.4 (2022-05-10)
------------------

- Fixed `WAITING_ADVICES_FROM_STATES.use_custom_transition_title_for`
  that is now a dict instead a tuple.
  [gbastien]

4.2.3 (2022-05-04)
------------------

- Fixed code still using item College transition `proposeToFinance`, was replaced
  by `wait_advices_from_proposed_to_director` (`wf_down_finances.png` icon and
  finances advice popup comment message).
  [gbastien]
- Speed up displaying `MeetingConfig` by hidding the `archivingRefs` field in
  `view` (still available in `edit`).
  [gbastien]

4.2.2 (2022-05-03)
------------------

- Fixed in BG transition title for `wait_advices_from_proposed_to_director` to
  use the default `wait_advices_from` because same transition exist in College
  and translation is already overrided.
  [gbastien]

4.2.1 (2022-05-03)
------------------

- Adapted `Migrate_To_4200._migrateItemsWorkflowHistory` to update `MeetingConfigs`
  before `workflow_history` and to call `BaseMigrator.updateWFStatesAndTransitions`
  with `update_local_roles=False` as it is done by the main migrator just after.
  [gbastien]
- Fixed `CustomMeetingItem.getLegalTextForFDAdvice` to be sure that everything is
  `utf-8` to avoid `UnicodeDecodeError` as now `RichTextValue.output` returns `unicode`.
  [gbastien]
- Make sure suffixes `administrativereviewers`, `internalreviewers` and
  `reviewers` have access to the item in the `Council`, as items come validated,
  need to configure the `itemcreated` item WF validation level `extra_suffixes`.
  [gbastien]
- Implemented `MeetingConfig._custom_reviewersFor` to manage `reviewersFor` the
  `Bourgmestre MeetingConfig` because suffix `creators` is used at several levels
  in MeetingConfig.itemWFValidationLevels and this breaks `MeetingConfig._highestReviewerLevel`.
  [gbastien]
- Fixed `ItemWfHistoryAdapter.mayViewComment` to show comment to the
  `MeetingItem.financeAdvice` advisers group for `backToProposedToInternalReviewer`
  action if `previous_review_state` was `proposed_to_finance_waiting_advices`.
  [gbastien]

4.2 (2022-04-28)
----------------

- Updated meetingliege_restrictedpowerobservers.css - SUP-22174
  [aduchene]
- Adapted workflows to use MeetingConfig.itemWFValidationLevels.
  [gbastien]
- Adapted `MeetingItem.labelForCouncil` behavior, use new field
  `MeetingItem.otherMeetingConfigsClonableToFieldLabelForCouncil` on College item
  and data sent is managed by PloneMeeting.
  [gbastien]
- Override `MeetingItem.show_budget_infos` to hide it to `restricted_power_observers`,
  removed override from `MeetingItem` view/edit templates.
  [gbastien]
- Added `Migrate_To_4200` upgrade step to move to PloneMeeting 4200.
  [gbastien]
- Completed `CustomMeetingItem.treasuryCopyGroup` to not set the DF Treasury
  group as copyGroup if item is using some specific RH proposingGroups.
  [gbastien]

4.1.3 (2021-11-05)
------------------

- Optimized `CustomMeetingItem._updateFinanceAdvisersAccessToManuallyLinkedItems`.
  [gbastien]

4.1.2 (2021-05-31)
------------------

- Fixed overrided print methods used for `deliberation_for_restapi`.
  Just change `xhtmlContents` and call `super()`.
  [gbastien]

4.1.1 (2020-11-13)
------------------

- Make `reviewers` able to `ask advices` when item is `proposed_to_internal_reviewer`.
  [gbastien]

4.1 (2020-08-21)
----------------

- Adapted code and tests regarding DX `meetingcategory`.
  [gbastien]
- Adapted templates regarding last changes in `Products.PloneMeeting`.
  [gbastien]
- Adapted code regarding changes in `collective.iconifiedcategory` (`CategorizedObjectAdapter`).
  [gbastien]

4.1rc11 (2020-06-24)
--------------------

- Adapted `meetingitem_view.pt` regarding changes in `Products.PloneMeeting` (`groupsInCharge`).
  [gbastien]
- Adapted item transitions guards to use `MeetingItemWorkflowConditions._check_required_data`.
  [gbastien]

4.1rc10 (2020-06-03)
--------------------

- `TREASURY_GROUP_ID` suffixed Plone group `incopy` is now set in copy of items having finances advice in place of `observers` suffixed Plone group.
  [gbastien]

4.1rc9 (2020-05-08)
-------------------

- Removed field `MeetingItem.itemIsSigned` from `meetingitem_edit`, it is managed thru the `meetingitem_view`

4.1rc8 (2020-04-29)
-------------------

- Removed custom inserting method `on_decision_first_word`, now using the default `on_item_decision_first_words` that is doing the same
- Fixed `test_GetItemWithFinanceAdvice`, `test_AcceptAndReturnCollege` and `test_ItemSentToCouncilWhenDuplicatedAndLinkKept` as `MeetingItem.onDuplicate`
  and `MeetingItem.onDuplicateAndKeepLink` were removed and replaced by the `@@item_duplicate_form`

4.1rc7 (2020-04-06)
-------------------

- Fixed some tests regarding changes in PloneMeeting
- Adapted code as custom field MeetingItem.decisionSuite is now in Products.PloneMeeting

4.1rc6 (2020-03-12)
-------------------

- Fixed MeetingItem.listArchivingRefs now that values are restricted to organizations UIDs and no more group ids.
  Optimized to be more efficient in view mode
- In ItemWfHistoryAdapter._userIsInProposingGroup, avoid to check if an object is in a list of object because the method uses @memoize
- Adapted meetingitemcollegeliege_workflow and meetingitemcouncilliege_workflow to give view access to role MeetingObserverLocal in every states
- Override MeetingItem.setListType to set 'need_Meeting_updateItemReferences' in the REQUEST so changing it when item is in a meeting will recompute item references
- Adapted page templates regarding changes in PloneMeeting
- Removed override of SignedChangeView._may_set_values as it is now managed in PloneMeeting by MeetingConfig.annexRestrictShownAndEditableAttributes
- Override MLItemDocumentGenerationHelperView.print_public_deliberation_decided to include decisionEnd field
- When an item is proposed_to_finance and is complete (MeetingItem.completeness), it can not be taken back by director or internal reviewer
- Renamed 'Point signé?' to 'Point visé?'
- Optimized code to use ram.cached methods
- Removed override of MeetingItem._itemIsSignedStates as there is a new default behavior where field may be managed by MeetingManagers as soon as item is validated

4.1rc5 (2020-01-10)
-------------------

- Added new collective.contact.plonegroup suffix '_incopy' (In copy) to manage users that will be set in copy of items
- Adapted migration to handle new power observers configuration
- Added migration step to remove empty paragraphs on every items (including recurring items and item templates)
- Adapted item WFs to use normal behavior for '_observers' suffix, that is to have View access to the item frim the beginning (itemcreated)
- Removed the 'getAdoptsNextCouncilAgenda' portal_catalog metadata, seems it was not used anymore
- Implemented print_deliberation and print_public_deliberation that will be used by plonemeeting.restapi
- Adapted templates regarding changes in PloneMeeting (ToolPloneMeeting.modelAdaptations was removed)
- In migration to MeetingLiege 4.1, call PloneMeeting upgrade steps (up to 4104)
- Removed custom MeetingCategory.groupsOfMatter, use default functionnality MeetingCategory.groupsInCharge instead
- Increase padding-bottom of <p> in RichText fields
- Removed <p>&nbsp;</p> that were used in RichText fields between each paragraphs (migration + methods rendering XHTML)

4.1rc4 (2019-10-14)
-------------------

- Updated templates regarding changes in Products.PloneMeeting

4.1rc3 (2019-09-23)
-------------------

- MeetingConfig.onMeetingTransitionItemTransitionToTrigger was moved to MeetingConfig.onMeetingTransitionItemActionToExecute, adapted code accordingly
- Updated meetingitem_view.pt regarding changes in Products.PloneMeeting ase meetingitem_view.pt

4.1rc2 (2019-06-30)
-------------------

- Fixed migration, while migrating MeetingCategory.groupsOfMatter, consider every categories (getCategories(onlySelectable=False), or some
  categories end not migrated.
- Fixed MeetingItem.getGroupsInCharge that was MeetingItem.getGroupInCharge before

4.1rc1 (2019-06-14)
-------------------

- Products.PloneMeeting.utils.getLastEvent was removed, use imio.history.utils.getLastWFAction.
- Adapted profile regarding changes about integration of collective.contact.* in Products.PloneMeeting.
- Adapted finances advice WF to use WF Actions/Conditions adapters and regarding use of dexterity.localrolesfield for meetingadvice.advice_group field
- Get rid of the 'MeetingFinanceEditor' role, we use dexterity.localrolesfield
- Moved the code that gives ability to add annex decision to finances advisers from events.onAdvicesUpdated to
  events.onItemLocalRolesUpdated, the correct place.  Do not use remove role 'MeetingFinanceEditor' but give role
  'MeetingMember' to finances advisers
- Fixed tests as finances advice is only giveable when item is in state 'proposed_to_finance' and no more when item is 'validated/presented'

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
