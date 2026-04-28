# Description Cleanup Patterns

Phrases and regex patterns to strip from external listing descriptions (Bazaraki, Index.cy, BuySellCyprus, etc.) before importing into Qobrix.

## Phrases to remove (case-insensitive, EN/RU/GR)

**English presentation phrases:**
- "We are pleased to present"
- "We are delighted to present"
- "We proudly offer"
- "for sale", "price negotiable", "urgent sale", "must sell", "quick sale"
- "reduced price", "bargain", "below market value", "investment opportunity"
- "rare opportunity", "don't miss", "call now", "call today", "contact us"
- "viewing available", "viewing arranged", "viewing by appointment"
- "from owner", "by owner", "private sale/seller/owner"
- "no agents", "no commission", "agent-free"
- "without agents/commission/intermediaries"
- "direct from owner/developer/builder", "owner sells/selling"

**Russian:**
- "Имеется возможность", "Представляем", "Предлагаем вашему вниманию"
- "продается", "на продажу", "срочно", "срочная продажа"
- "от собственника", "без посредников", "без агентов", "без комиссии"
- "от застройщика", "торг уместен", "цена договорная"
- "звоните", "обращайтесь", "пишите", "не упустите"
- "уникальное/ая предложение", "выгодное/ая предложение/цена/инвестиция"

**Greek:**
- "Παρουσιάζουμε", "Με χαρά παρουσιάζουμε"
- "πωλείται", "προς πώληση", "ευκαιρία", "τιμή ευκαιρίας"
- "χωρίς μεσίτη", "από ιδιοκτήτη"
- "καλέστε", "επικοινωνήστε"

## Regex patterns

```
# English sales/owner
/\bfor\s+sale\b/gi
/\bprice\s+negotiable\b/gi
/\burgent\s+sale\b/gi
/\bmust\s+sell\b/gi
/\bquick\s+sale\b/gi
/\breduced\s+price\b/gi
/\bbargain\b/gi
/\bbelow\s+market\s+(value|price)\b/gi
/\binvestment\s+opportunity\b/gi
/\brare\s+opportunity\b/gi
/\bdon'?t\s+miss\b/gi
/\bcall\s+(now|today|us)\b/gi
/\bcontact\s+(us|me|now)\b/gi
/\bviewing\s+(available|arranged|by\s+appointment)\b/gi
/\bwe\s+are\s+(pleased|delighted|proud)\s+to\s+(present|offer)\b/gi
/\bfrom\s+owner\b/gi
/\bby\s+owner\b/gi
/\bprivate\s+(sale|seller|owner)\b/gi
/\bno\s+agents?\b/gi
/\bno\s+commission\b/gi
/\bagent-?free\b/gi
/\bwithout\s+(agents?|commission|intermediar(y|ies))\b/gi
/\bdirect\s+from\s+(owner|developer|builder)\b/gi
/\bowner\s+sell(s|ing)?\b/gi

# Russian
/продается/gi
/на\s+продажу/gi
/срочн(о|ая\s+продажа)/gi
/от\s+собственника/gi
/без\s+(посредников|агентов|комисси[ий])/gi
/от\s+застройщика/gi
/торг(\s+уместен)?/gi
/цена\s+договорная/gi
/звоните/gi
/обращайтесь/gi
/пишите/gi
/не\s+упустите/gi
/уникальн(ое|ая)\s+предложение/gi
/выгодн(ое|ая)\s+(предложение|цена|инвестиция)/gi
/имеется\s+возможность/gi
/представляем/gi
/предлагаем\s+вашему\s+вниманию/gi

# Greek
/πωλείται/gi
/προς\s+πώληση/gi
/ευκαιρία/gi
/χωρίς\s+μεσίτη/gi
/από\s+ιδιοκτήτη/gi
/τιμή\s+ευκαιρίας/gi
/καλέστε/gi
/επικοινωνήστε/gi
/παρουσιάζουμε/gi

# Contact info (all languages)
/\+?357[\s\-]?\d{2}[\s\-]?\d{6}/g          # Cyprus phone numbers
/\b(99|96|97|95|94|70|22|25|24|26)\d{6}\b/g  # Local Cyprus numbers
/[\w.-]+@[\w.-]+\.\w{2,}/g                    # Email
/\b(WhatsApp|Viber|Telegram|Signal)\s*:?\s*[\+\d\s\-()]+/gi
/\b(WhatsApp|Viber|Telegram|Signal)\b/gi

# Portal references / footers
/bazaraki\.com/gi
/bazaraki/gi
/index\.cy/gi
/buysellcyprus(\.com)?/gi
/\bcheck\s+(my|our|the)\s+(other\s+)?listings?\b/gi
/\bsee\s+(my|our|the)\s+(other\s+)?ads?\b/gi
/\blisted\s+(on|at)\s+\w+/gi
```

## Cleanup rules

1. Apply regex patterns to remove matches.
2. Post-clean leftovers:
   - Double spaces → single
   - 3+ newlines → 2 newlines max
   - Sentences left empty / only-punctuation → drop
   - Trim each line
3. Drop bullet points/list items that became empty.
4. Preserve paragraph structure of remaining content.
5. **Keep** factual property info even if it sounds promotional ("sea view", "walking distance to beach").
