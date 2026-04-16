# Qobrix CRM Search Expressions Reference

Qobrix uses a custom query language for filtering records. Pass these via the URL-encoded `search` query parameter.

## Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `==` | Equals | `status == "available"` |
| `!=` | Not equals | `status != "closed"` |
| `>` | Greater than | `bedrooms > 2` |
| `>=` | Greater or equal | `list_selling_price_amount >= 100000` |
| `<` | Less than | `list_selling_price_amount < 500000` |
| `<=` | Less or equal | `bedrooms <= 5` |
| `in` | In list | `type in ["house", "apartment"]` |
| `not in` | Not in list | `status not in ["sold", "rented"]` |
| `contains` | Contains substring | `description contains "sea view"` |
| `not contains` | Doesn't contain | `name not contains "test"` |
| `is null` | Is empty/null | `email is null` |
| `is not null` | Has value | `phone is not null` |

## Logical Operators

| Operator | Example |
|----------|---------|
| `and` | `bedrooms >= 3 and city == "Limassol"` |
| `or` | `city == "Limassol" or city == "Paphos"` |

## Special Variables

| Variable | Description |
|----------|-------------|
| `CURRENT_USER` | Currently authenticated user |
| `TODAY` | Today's date |
| `YESTERDAY` | Yesterday's date |
| `THIS_WEEK` | Start of current week |
| `THIS_MONTH` | Start of current month |
| `THIS_YEAR` | Start of current year |

## Common Searches

### Properties
```
# Available apartments in Limassol under 300k
status == "available" and property_type == "apartment" and city == "Limassol" and list_selling_price_amount <= 300000

# 3+ bedroom houses for sale
bedrooms >= 3 and property_type == "house" and sale_rent == "for_sale" and status == "available"
```

### Contacts
```
# By name
first_name contains "Maria"

# With phone number
phone is not null
```

### Opportunities
```
# New leads
stage == "new"

# Overdue follow-ups
next_follow_up_date < TODAY and stage not in ["closed_won", "closed_lost"]
```

### Tasks
```
# Pending tasks for today
status == "pending" and start_date <= TODAY

# Overdue tasks
status == "pending" and end_date < TODAY

# Viewings this week
type == "viewing" and start_date >= THIS_WEEK
```
