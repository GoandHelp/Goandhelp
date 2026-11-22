# Policy document translation coverage

## Status: partial — not the completed 39-language deliverable

The canonical English content in `app/policies.py` is unchanged. The inventory
contains 182 distinct sources from the four visible documents after the complete
safety notice and sections are appended to the handbook. The compatibility
`safety` document is not a fifth visible link.

The reader now performs reactive `ui()` lookup for its title, subtitle, effective
date, notice, section headings and full paragraphs. Its language and direction
follow the current account language. English stays in reader state; switching
languages does not cache translated documents. No member-written content, account
rules, dependencies, database schema, external APIs or logo assets were changed.

## Authored offline data

- Credits: all eight fields, including all three attribution paragraphs, in all
  38 non-English Settings locales (304 source/locale entries).
- Privacy: all 41 fields in French, Russian and Urdu (123 entries, with the date
  already included in Credits).
- User agreement: all 51 fields in French and German (102 entries, with the date
  already included in Credits).
- Handbook: all 85 fields in French, including the entire merged safety content
  (85 entries, with the date already included in Credits).
- Russian and Urdu reader chrome, footer disclaimer, handbook title and agreement
  title are supplied as literal offline entries.

There are 612 distinct document source/locale entries in the newly authored
catalogs, out of 6,916 required. These include 322 whole-paragraph translations.
French has all 182 document sources; German has 58; Russian and Urdu have 50 each;
the other 34 non-English Settings locales have eight each in these new catalogs.
Existing effective catalogs may already contain additional translated headings.
The Dutch title `Credits` is a documented natural-language coincidence, not a
paragraph fallback. Proper project names, copyright symbols and licence names are
retained in their attribution contexts.

**Remaining:** full handbook, privacy and agreement translations across the other
locales, including Urdu's merged safety handbook. This must not be described as
full-document coverage in all 39 languages. Wider Russian/Urdu interface gaps are
not addressed here. Checklist items were not changed.

## Checks

`app/test_policy_document_translation.py` includes source inventory, complete
Credits coverage, validation of actual authored entries, attribution and slot
checks, reactive field/RTL checks, real component construction, small-fixture
Node evaluation of compiled dynamic `ui()` lookup, and canonical open/switch/close
event checks without database writes. Its strict all-38/all-182 release gate
reports missing effective catalog entries and is expected to fail until the
remaining translations are authored. Tests have not been executed in this turn.
An independently frozen full-English checksum fixture and human linguistic/legal
review are not supplied. No human review or legal certification is claimed.
