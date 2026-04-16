---
name: lead-capture
description: >
  Detect new leads from incoming emails and create them in Qobrix CRM. Use when
  the user says "check for new leads", "capture leads from email", "any new
  inquiries", "process incoming leads", "create lead from this email", or wants
  to convert an email inquiry into a CRM contact and opportunity.
version: 1.0.0
---

# Lead Capture

Scan for property inquiries and create contacts and opportunities in Qobrix CRM.

## API Access

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" METHOD "/api/v2/ENDPOINT" '[BODY]'
bash "${CLAUDE_PLUGIN_ROOT}/scripts/wasender-api.sh" METHOD "/api/ENDPOINT" '[BODY]'
```

If either script returns `"error":"not_configured"`, tell the user to reinstall the plugin or check their plugin configuration.

## Workflow

### From Email or Pasted Text

When the user shares an inquiry email or lead details:

1. **Parse the inquiry.** Extract:
   - Sender name and email
   - Phone number (scan for phone patterns)
   - Property interest (type, location, budget if mentioned)
   - Source (which portal or website the inquiry came from)
   - Specific property asked about (reference number, URL, or description)

2. **Check for duplicates.** Search Qobrix for existing contacts:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/contacts?search=email%20%3D%3D%20%22{email}%22&limit=5"
   ```
   Also try by phone:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/contacts?search=phone%20%3D%3D%20%22{phone}%22&limit=5"
   ```

3. **Present findings** to the user:
   ```
   New inquiry found:

   1. {Name} ({email}, {phone})
      Interested in: {property type} in {location}
      Budget: {budget if mentioned}
      Source: {portal/website}
      Status: New contact / Existing: {existing contact name}

   Create in Qobrix?
   ```

4. **Create in CRM** after user confirmation:

   New contact:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" POST "/api/v2/contacts" \
     '{"first_name":"{first}","last_name":"{last}","email":"{email}","phone":"{phone}"}'
   ```

   New opportunity:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" POST "/api/v2/opportunities" \
     '{"name":"{description}","contact_id":"{contact_id}","stage":"new","source":"{source}"}'
   ```

5. **Suggest next steps**: "Want me to send an acknowledgment to {name} via WhatsApp?"

### Manual Entry

When the user wants to manually add a lead:
1. Ask for: name, email, phone, property interest, budget, preferred locations
2. Check for duplicates in Qobrix
3. Create contact and opportunity with user confirmation
4. Offer to send a welcome message via WhatsApp

## Important Notes

- Always check for duplicate contacts before creating new ones.
- If a phone number is found, ensure it's in international format (e.g., 35799123456).
- Tag the lead source accurately — this is critical for marketing ROI tracking.
- Don't auto-create without user confirmation. Always present findings first.
- For portal leads, the portal name should be captured as the lead source.
