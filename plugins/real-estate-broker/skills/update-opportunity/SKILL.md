---
name: update-opportunity
description: >
  Update an opportunity or deal in Qobrix CRM. Use when the user says "update
  the deal", "move opportunity to next stage", "update CRM", "change deal status",
  "add notes to opportunity", "update the pipeline", "mark deal as", or wants to
  modify any aspect of an existing opportunity in Qobrix.
version: 1.0.0
---

# Update Opportunity in Qobrix CRM

Modify an existing opportunity/deal in the Qobrix CRM pipeline — change stage, add notes, update amount, set next actions, or reassign.

## API Access

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" METHOD "/api/v2/ENDPOINT" '[BODY]'
```

If the script returns `"error":"not_configured"`, tell the user to run `/setup` to configure their API credentials.

## Workflow

1. **Identify the opportunity.** If the user mentions a customer name or property, search:

   By customer name:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/contacts?search=first_name%20contains%20%22{name}%22&limit=10"
   ```
   Then filter opportunities by contact:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/opportunities?search=contact_name%20%3D%3D%20%22{contact_id}%22&limit=10"
   ```

   By stage:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/opportunities?search=status%20%3D%3D%20%22{stage}%22&limit=25"
   ```

   If multiple matches, present a numbered list and ask the user to choose.

2. **Fetch current state.**
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/opportunities/{id}"
   ```
   Show current details: stage, amount, contact, property, notes, last activity.

3. **Determine changes.** Based on the user's request, identify what needs updating. Common updates:
   - **Status change** (field is `status`, not `stage`): new → assigned → informative → proposal → viewing → negotiation → closed_won / closed_lost
   - **Price range**: update `list_selling_price_from` / `list_selling_price_to`
   - **Description / notes**: update `description`
   - **Next follow-up**: update `next_follow_up_date`

4. **Confirm and update.** Show the user what will change (before → after) and get confirmation.
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" PUT "/api/v2/opportunities/{id}" \
     '{"status":"{new_status}","description":"{updated_notes}"}'
   ```

5. **Create follow-up task if needed.**
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" POST "/api/v2/tasks" \
     '{"subject":"{next_action}","end_date":"{iso_date}","related_opportunity":"{id}","contact":"{contact_uuid}"}'
   ```

## Status Values (verified)

| Status | Description |
|--------|-------------|
| new | Fresh lead, not yet actioned |
| assigned | Assigned to an agent |
| informative | Information gathering phase |
| proposal | Proposal sent / properties shown |
| viewing | Viewing scheduled or completed |
| negotiation | Active negotiation |
| closed_won | Deal completed |
| closed_lost | Deal lost |

## Field Name Reference (Opportunities)

| Field | Notes |
|-------|-------|
| `contact_name` | UUID of related contact (confusingly named — it's a foreign key, not text) |
| `status` | NOT `stage` |
| `source` | Fixed enum: `direct`, `agent` only |
| `buy_rent` | `to_buy` or `to_rent` |
| `enquiry_type` | Property type they're looking for |
| `construction_stage` | `completed`, `under_construction`, `off_plan` |

## Field Name Reference (Tasks)

| Field | Notes |
|-------|-------|
| `subject` | NOT `title` |
| `contact` | UUID of related contact (NOT `contact_id`) |
| `related_opportunity` | UUID of related opportunity (NOT `opportunity_id`) |
| `property_id` | UUID of related property |
| `start_date` / `end_date` | ISO dates (NOT `due_date`) |
| `status` | `new_task`, `in_progress`, `completed`, etc. |
| `priorities` | `low`, `normal`, `high` |

## Important Notes

- Always show current state before applying changes so the user can verify the right opportunity.
- When moving to "closed_lost", prompt for a reason.
- When moving to "closed_won", confirm the final amount.
- Log meaningful notes — these become the deal history for the team.

## Reference Files

- **`references/qobrix-search-expressions.md`** — Search expression syntax reference
