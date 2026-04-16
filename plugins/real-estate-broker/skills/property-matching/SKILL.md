---
name: property-matching
description: >
  Match property listings to customer preferences and suggest which properties
  to send. Use when the user says "match properties for", "find suitable listings
  for", "what properties fit", "property recommendations for", "match customer
  to listings", or wants to automatically pair available properties with buyer/tenant
  requirements.
version: 1.0.0
---

# Property Matching

Match available property listings against customer preferences stored in Qobrix CRM and suggest the best fits.

## API Access

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" METHOD "/api/v2/ENDPOINT" '[BODY]'
```

If the script returns `"error":"not_configured"`, tell the user to reinstall the plugin or check their plugin configuration.

## Workflow

1. **Get customer preferences.** Look up the contact in Qobrix:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET "/api/v2/contacts/{id}"
   ```
   Extract their stored preferences:
   - Property type (apartment, villa, house, office, land, etc.)
   - Preferred locations/areas
   - Budget range (min/max price)
   - Minimum bedrooms and bathrooms
   - Other requirements (parking, pool, sea view, garden, furnished, etc.)
   - Purpose: buy or rent

2. **Search matching properties.**
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/qobrix-api.sh" GET \
     "/api/v2/properties?search=status%20%3D%3D%20%22available%22%20and%20property_type%20%3D%3D%20%22{type}%22%20and%20bedrooms%20%3E%3D%20{min_beds}&limit=50"
   ```
   Cast a slightly wider net: include properties 10-15% above budget and in adjacent areas. Only include `status == "available"`.

3. **Score and rank matches.** For each property, calculate a match score:
   - **Location match**: exact area = 100%, adjacent = 70%, same city = 40%
   - **Price match**: within budget = 100%, up to 10% over = 70%, up to 20% over = 40%
   - **Size match**: meets or exceeds bedroom/bathroom requirements = 100%
   - **Feature match**: bonus points for matching extras (pool, view, parking, etc.)

4. **Present results:**

   ```
   PROPERTY MATCHES FOR {Customer Name}

   Looking for: {type} in {locations}, {budget range}, {beds}+ bedrooms

   TOP MATCHES (90%+)
   1. {Property Title} — {Location} — {Price}
      Match: {score}% | {beds} bed | {area}m2
      Location OK | Budget OK | Size OK

   GOOD MATCHES (70-89%)
   2. {Property Title} — {Location} — {Price}
      Match: {score}% | Slightly over budget
      Location OK | Budget: +{amount} over | Size OK

   WORTH CONSIDERING (50-69%)
   3. {Property Title} — {Location} — {Price}
      Match: {score}% | Different area but great value
   ```

5. **Offer actions:**
   - "Want me to send the top matches to {Name} via WhatsApp?"
   - "Should I schedule viewings for the top picks?"
   - "Want to see full details for any of these?"

## Reverse Matching

When the user asks "who should I send this property to":
- Take a property and find contacts whose preferences match
- Search contacts and compare their preferences against the property
- Present a list of contacts who might be interested

## Important Notes

- If customer preferences are incomplete in the CRM, ask the user to fill in the gaps before matching.
- Always include the match reasoning so the broker can make informed decisions.
- Don't exclude properties just because one criterion doesn't match perfectly.
- Flag any properties that were already sent to this customer to avoid duplicates.
