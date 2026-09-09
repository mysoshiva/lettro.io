# Test letters

Five real German letters, redacted (names, addresses, ID numbers, VINs, license plates, policy numbers, DOBs, and login credentials replaced with placeholders). Each file has the redacted input text and the expected `schema.json` output when run through `prompt-v1.md` with `target_language: en`.

Chosen deliberately to cover a spread of cases:

| File | Type | Why it's here |
|---|---|---|
| 01-stadt-heilbronn-kfz-adresse | Fixed-deadline administrative notice | Clean baseline case — absolute date, clear required documents, stated consequences |
| 02-huk-coburg-versicherung | Informational, no action | Tests that the model doesn't manufacture an action out of an FYI document |
| 03-stuttgart-bussgeldstelle | Relative-deadline legal notice | Deadline is "one week from receipt," not a calendar date — tests `is_relative_to_receipt` |
| 04-suewag-werbung | Marketing, no action (negative control) | Tests that promotional mail is correctly flagged as not requiring action |
| 05-arbeitsagentur-einladung | Fixed-deadline notice with statutory consequence | Real legal stakes (benefit suspension), plus a genuinely gray-area exception clause |

When you change the prompt, re-run it against all five and diff the output against the expected JSON in each file before considering the change safe to ship.
