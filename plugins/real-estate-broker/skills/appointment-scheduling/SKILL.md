---
name: appointment-scheduling
description: >
  Schedule property viewings and appointments with customers. Use when the user
  says "schedule a viewing", "book an appointment", "arrange a viewing", "set up
  a meeting with", "schedule showing", or wants to coordinate a property visit
  with a customer.
version: 1.0.0
---

# Appointment Scheduling

Schedule property viewings and meetings, create tasks in Qobrix, and send confirmations to customers via WhatsApp.

## API Access

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" METHOD "/api/v2/ENDPOINT" '[BODY]'
bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" METHOD "/api/ENDPOINT" '[BODY]'
```

If either script returns `"error":"not_configured"`, tell the user to reinstall the plugin or check their plugin configuration.

## Workflow

1. **Gather details.** Determine:
   - Which customer (look up in Qobrix if needed)
   - Which property or properties to view
   - Preferred date and time
   - Any special requirements

2. **Create the task in Qobrix.**
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" POST "/api/v2/tasks" \
     '{"title":"Viewing: {property} with {customer}","type":"viewing","due_date":"{iso_date}","contact_id":"{contact_id}","property_id":"{property_id}","description":"{address and notes}"}'
   ```

3. **Send confirmation to customer.**

   WhatsApp confirmation:
   ```
   Hi {Name}!

   Your viewing is confirmed:

   Property: {Property Title}
   Address: {Address}
   Date: {Date} at {Time}

   {Any special instructions}

   Please let me know if you need to reschedule. See you there!
   ```

   Send via WaSender:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" POST "/api/send-message" \
     '{"to":"{phone}","text":"{confirmation_message}"}'
   ```

   Optionally send the property photo:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" POST "/api/send-image" \
     '{"to":"{phone}","url":"{image_url}","caption":"{property_title}"}'
   ```

   Optionally send location pin:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" POST "/api/send-location" \
     '{"to":"{phone}","lat":{lat},"lng":{lng},"name":"{property_title}"}'
   ```

4. **Update the opportunity.** If there's a linked opportunity, update its stage to "viewing":
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" PUT "/api/v2/opportunities/{id}" '{"stage":"viewing"}'
   ```

5. **Schedule reminders.** Offer to create a reminder for the day before:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" POST "/api/v2/tasks" \
     '{"title":"Reminder: Viewing tomorrow with {name}","type":"follow_up","due_date":"{day_before}","contact_id":"{id}"}'
   ```

## Multiple Viewings

When scheduling a viewing tour (multiple properties):
- Create a task for each property viewing
- Space them appropriately (suggest 30-45 min between viewings)
- Send a single combined confirmation message with all viewings listed
- Include a suggested route order based on locations

## Rescheduling

When the user says "reschedule viewing":
1. Find the existing viewing task in Qobrix
2. Update the task with the new date/time
3. Send an updated confirmation to the customer
4. Note the change: "Rescheduled from {old date} to {new date}"

## Important Notes

- Always send confirmations — customers expect written confirmation of viewing times.
- Include the property address and any access instructions.
- For same-day viewings, prefer WhatsApp for faster delivery.
