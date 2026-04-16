---
name: send-properties
description: >
  Send a curated selection of property listings to a customer via WhatsApp or email.
  Use when the user says "send properties to", "share listings with", "send this
  customer some options", "WhatsApp properties to", "email listings to", or wants
  to present available properties to a buyer or tenant.
version: 1.0.0
---

# Send Properties to Customer

Send one or more property listings to a customer via WhatsApp (WaSender API), formatted professionally with key details and photos.

## API Access

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" METHOD "/api/v2/ENDPOINT" '[BODY]'
bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" METHOD "/api/ENDPOINT" '[BODY]'
```

If either script returns `"error":"not_configured"`, tell the user to run `/setup` to configure their API credentials.

## Workflow

1. **Identify the customer.** Look up the contact in Qobrix CRM:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/contacts?search=first_name%20contains%20%22{name}%22&limit=10"
   ```
   Confirm their name and phone number (for WhatsApp).

2. **Select properties.** If the user hasn't specified exact properties, search Qobrix:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/properties?search=status%20%3D%3D%20%22available%22%20and%20property_type%20%3D%3D%20%22apartment%22&limit=25"
   ```
   Present a short summary list and let the user confirm which to send.

3. **Fetch full details.** For each selected property:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/properties/{id}"
   ```

4. **Choose delivery channel.** Ask the user: WhatsApp or email? Default to WhatsApp if the customer has a phone number.

5. **Format and send.**

### WhatsApp Format

For each property, compose a message using this template:

```
{Property Title}
{Location}
{Price} {currency}
{Bedrooms} bed | {Bathrooms} bath | {Area} m2

{Short description — 2-3 sentences max}

Ref: {Reference number}
```

If the property has a main photo URL, send the image first with caption:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" POST "/api/send-image" \
  '{"to":"{phone}","url":"{image_url}","caption":"{property_title} — {price}"}'
```

Then send the text details:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" POST "/api/send-message" \
  '{"to":"{phone}","text":"{formatted_message}"}'
```

After all properties, send a closing message:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" POST "/api/send-message" \
  '{"to":"{phone}","text":"These are {count} properties matching your criteria. Let me know which ones interest you and I can arrange viewings!"}'
```

6. **Log the activity.** Create a task/note in Qobrix:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" POST "/api/v2/tasks" \
     '{"title":"Sent {count} properties to {name}","contact_id":"{id}","type":"follow_up","status":"completed"}'
   ```

## Important Notes

- Always confirm with the user before sending. Show a preview of what will be sent.
- Phone numbers must be in international format without + prefix (e.g., 35799123456).
- If a customer doesn't have a phone number, note this and suggest getting it or using email.
- Keep WhatsApp messages concise — customers read them on mobile.
- For more than 5 properties, suggest splitting into a "top picks" message now and the rest later.

## Reference Files

- **`references/message-templates.md`** — Additional message templates for different scenarios (luxury, investment, rental)
