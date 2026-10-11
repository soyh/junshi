# TEST-028 Timeline Test-First Specification

Status: implementation in progress
Baseline: 196f76c

## Scope

Person Timeline is a read-only aggregation over existing interactions, conversations, and messages. No `timeline_events` table is introduced.

## API

`GET /api/v1/persons/{person_id}/timeline`

Query parameters:

- `limit`: default 50, minimum 1, maximum 100
- `offset`: default 0, minimum 0

Response:

- `items`: TimelineEvent objects
- `limit`
- `offset`
- `total`

## Timeline Event

Fields:

- `id`
- `user_id`
- `person_id`
- `event_type`
- `occurred_at`
- `source_type`
- `source_id`
- `title`
- `content`
- `metadata`

Sources:

- Interaction: `occurred_at`
- Conversation: `created_at`, represented as `conversation.created`
- Message: `sent_at`, with `person_id` resolved through its Conversation

Message event types are `message.user`, `message.person`, `message.system`, and `message.assistant`.

Interaction event types are `interaction.message`, `interaction.call`, `interaction.meeting`, `interaction.date`, `interaction.gift`, and `interaction.other`.

## Ordering

Events are ordered by `occurred_at DESC`, then `source_type ASC`, then `source_id ASC` for deterministic ordering.

## Isolation

Every source query is restricted by the current `user_id` and requested `person_id`. A person belonging to another user returns `404 Person not found`.

## Tests

The API test suite covers empty timelines, three-source aggregation, person/user isolation, pagination, pagination validation, missing persons, message-to-conversation person resolution, and deletion reflection.
