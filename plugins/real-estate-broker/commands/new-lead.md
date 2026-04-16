---
description: Create a new lead from an email or manual entry
argument-hint: [email-subject or contact-details]
allowed-tools: [Bash, Read, AskUserQuestion]
---

Create a new lead in coWork CRM. Use the lead-capture skill for the full workflow.

User arguments: $ARGUMENTS

Two modes:

**From email:** If the argument looks like an email subject or the user says "from email":
1. Ask the user to paste the email content
2. Parse the email content for contact details and property interest
3. Check for duplicate contacts in coWork
4. Create the contact and opportunity after confirmation

**Manual entry:** If the argument contains contact details or no argument given:
1. Ask for: name, email, phone, property interest, budget, preferred locations
2. Check for duplicates in coWork using the API helper script
3. Create contact and opportunity
4. Offer to send a welcome message via WhatsApp
