# Chillar reading rules

Rules the Chillar app downloads to recognise receipt and bank alert emails. This file holds sender domains and text patterns only; it contains no user data and the app sends nothing when it fetches it.

`rules.json` is downloaded by the app (at most every six hours, and on demand from More → Reading health). It only adds to the rules built into the app, so a receipt layout that changes can be fixed without a store release. It is data: the app never runs anything from it.

To ship a fix, edit the file, **raise `version`**, and publish. When a phone sees a new version it re-reads the emails it could not read before (up to 300, from the last 120 days).

```jsonc
{
  "version": 2,                                   // whole number, raise on every change
  "merchants": [
    { "id": "instamart", "domains": ["newsender.instamart.in"] },                      // extend a built-in platform
    { "id": "freshtohome", "name": "FreshToHome", "category": "Groceries",             // or add a new one
      "domains": ["freshtohome.com"], "subscription": false, "memberships": [],
      "variants": [{ "match": "instamart", "id": "instamart" }] }                      // subject pattern → other platform
  ],
  "subjectWords": ["settled"],                    // extra words that make a subject worth fetching
  "totalLabels": ["here is what it came to"],     // patterns for the label of the amount paid
  "ignoreSubjects": ["^your weekly summary"],     // subjects that are never a payment
  "bankDomains": ["newbank.in"],
  "bankSubjectWords": ["debit"],
  "bankAlerts": [                                 // a bank alert layout; numbers are capture groups
    { "re": "Rs\\.?\\s*([\\d,.]+) paid to (\\S+@\\w+) \\(([^)]+)\\)", "via": "UPI", "amount": 1, "vpa": 2, "payee": 3 }
  ]
}
```

Patterns are JavaScript regular expressions, matched without regard to case, at most 300 characters. A malformed entry is dropped; the rest of the file still applies. Categories: Food delivery, Quick commerce, Groceries, Shopping, Subscriptions, Rides, Bills, Health, Other.
