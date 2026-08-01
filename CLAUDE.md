# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is this project?

Products.MeetingLiege is a **PloneMeeting profile** for the City of Liège (Ville de Liège). It extends `Products.PloneMeeting` (located at `../Products.PloneMeeting`) with Liège-specific workflows, organizational rules, and UI customizations. PloneMeeting's own CLAUDE.md explains the base framework — read it for context on the tech stack (Python 2.7, Plone 4.3, Archetypes/Dexterity mix, buildout).

This package manages three simultaneous meeting configurations:
- **College** (`meeting-config-college`) — Collège communal
- **Council** (`meeting-config-council`) — Conseil communal
- **Bourgmestre** (`meeting-config-bourgmestre`) — Décisions du Bourgmestre

## Running tests

```bash
# Bootstrap once (from project root)
python bootstrap.py
bin/buildout

# Run all MeetingLiege tests
bin/testliege

# Run a single test module
bin/testliege -t testCustomWorkflows

# Run a single test method
bin/testliege -t testCustomWorkflows.testXxx
```

The test runner is configured in `buildout.cfg` via the `[testliege]` part (uses `zc.recipe.testrunner` with `--auto-color --auto-progress`).

## Architecture

### Extension model

MeetingLiege does **not** subclass PloneMeeting content types directly. Instead it registers ZCML adapters that override PloneMeeting's adapter lookups. The central file is `src/Products/MeetingLiege/adapters.py` (~2 500 lines), which provides:

- `CustomMeeting`, `CustomMeetingItem`, `CustomMeetingConfig`, `CustomToolPloneMeeting` — override cross-cutting methods via the `IMeetingCustom`, `IMeetingItemCustom`, etc. interfaces.
- Twelve workflow adapter classes (Actions + Conditions) for the three meeting types: `MeetingCollegeLiege*`, `MeetingItemCollegeLiege*`, `MeetingCouncilLiege*`, `MeetingItemCouncilLiege*`, `MeetingBourgmestre*`, `MeetingItemBourgmestre*`.
- `MeetingAdviceFinancesWorkflowActions/Conditions` — adapter for the finance advice sub-workflow.

All adapters are registered in `configure.zcml`. Schema field extensions (`labelForCouncil`, `financeAdvice`) live in `src/Products/MeetingLiege/model/pm_updates.py`.

### Finance advice workflow

The finance advice is a key feature. It uses a dedicated content type `meetingadvicefinances` with its own DCWorkflow (`meetingadviceliege_workflow`). States progress through three finance roles:

```
proposed_to_financial_controller
  → proposed_to_financial_reviewer
    → proposed_to_financial_manager
      → financial_advice_signed (historized)
```

The three finance group suffixes (`financialcontrollers`, `financialreviewers`, `financialmanagers`) are added to `PMconfig.EXTRA_GROUP_SUFFIXES` at import time in `config.py`. Finance groups are restricted to orgs listed in `FINANCE_GROUP_IDS`.

Event handlers in `events.py` drive automatic item state changes: when all required advices are given, `_sendWaitingAdvicesItemBackInWFIfNecessary` fires and returns the item to its pre-waiting state.

### Group/permission model

Beyond standard PloneMeeting suffixes, Liège adds:
- `administrativereviewers`, `internalreviewers` — pre-validation review chain
- `incopy` — read-only access to items
- `financialcontrollers`, `financialreviewers`, `financialmanagers` — finance advice chain

The item validation workflow for College follows:
`itemcreated → proposeToAdministrativeReviewer → proposeToInternalReviewer → proposeToDirector → validate → present`

Constants for special groups: `BOURGMESTRE_GROUP_ID = 'bourgmestre'`, `GENERAL_MANAGER_GROUP_ID = 'sc'`, `TREASURY_GROUP_ID = 'df-controle-tresorerie'`.

### Key files

| File | Purpose |
|---|---|
| `adapters.py` | All workflow adapters and content-type customizations |
| `events.py` | Event subscribers (advice lifecycle, local roles) |
| `config.py` | Constants — group suffixes, finance IDs, legal text |
| `interfaces.py` | Workflow interface declarations |
| `setuphandlers.py` | Post-install GenericSetup hooks |
| `overrides.py` | ZCML overrides for PloneMeeting UI components |
| `utils.py` | Memoized helpers (`finance_group_uids`, `bg_group_uid`, …) |
| `model/pm_updates.py` | `MeetingItem` schema extensions |
| `browser/views.py` | `MainInfosHistoryView` |
| `migrations/migrate_to_42xx.py` | Upgrade steps |

### Profiles

- `profiles/default/` — Zope/Plone profile (workflows, type definitions, registry); metadata version `4203`.
- `profiles/liege/` — Organization/user import data for production.
- `profiles/testing/` — Test-specific import data.
- `profiles/zbourgmestre/` — Bourgmestre-specific import data.

The custom advice type XML is at `profiles/default/types/meetingadvicefinances.xml`.

### Migrations

Migration classes in `migrations/migrate_to_42xx.py` extend `Products.PloneMeeting.migrations.Migrator`. They handle configuration updates (labels, field reordering, custom adviser setup). Triggered via the standard PloneMeeting upgrade machinery (portal_setup upgrade steps).

### Tests

Tests live in `src/Products/MeetingLiege/tests/`. Base infrastructure:

- `MeetingLiegeTestCase` — extends `PloneMeetingTestCase`; sets up all three configs; use `setUpBourgmestreConfig()` to initialize the bourgmestre config.
- `MeetingLiegeTestingHelpers` — overrides PloneMeeting's transition constants (e.g. `TRANSITIONS_FOR_PROPOSING_ITEM_1`) to match Liège's longer validation chain; provides `_setupFinanceGroups()` and `_giveFinanceAdvice()`.

Ignored test files (inherited from PloneMeeting but not applicable): `test_robot.py`, `testPerformances.py`, `testContacts.py`, `testVotes.py`.

## Item history tracking

Liège uses a custom `ITEM_MAIN_INFOS_HISTORY = 'main_infos_history'` annotation on items (separate from the standard workflow history) to record changes to main fields. `MainInfosHistoryView` in `browser/views.py` renders this history.
