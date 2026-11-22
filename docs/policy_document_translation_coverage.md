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
- User agreement: all 51 fields in French, German, Russian and Urdu (204 field
  entries, with the shared date already included in Credits).
- Handbook: all 85 fields in French, Russian and Urdu, including the entire
  merged safety notice and every safety section (255 field entries, with the
  shared date already included in Credits).
- Russian and Urdu reader chrome and footer disclaimer remain registered.
- This bounded batch supplies exactly 272 literal whole-field translations:
  170 handbook fields and 102 agreement fields. Privacy and Credits files and
  values are unchanged. English sources and all other locale data are unchanged.

The dedicated catalogs now contain 876 distinct canonical document source/locale
entries out of 6,916 required (38 × 182). Whole-paragraph translations total 512.
These counts deduplicate the effective date shared across the four documents;
reader chrome is excluded. French, Russian and Urdu each have all 182 sources;
German has 58; the other 34 non-English Settings locales have eight each in the
 dedicated document catalogs. Russian and Urdu each increased from 50 authored
sources to 182, a gain of 132 distinct sources despite 136 newly authored fields
per locale (shared dates and previously supplied titles account for duplicates).

Effective interface catalogs cover 1,050 of the 6,916 canonical source/locale
pairs: French, Russian and Urdu have 182 each, German has 62, and the other 34
locales have 13 each. Before this batch Russian and Urdu each had 51 effective
sources and 131 gaps, rather than 50 effective sources. They now have no policy
source gaps. These are **policy-only** counts, not wider interface-key coverage.
The focused test computes these totals from the actual dedicated and effective
catalogs and asserts the inventory and remaining gap distribution.
The Dutch title `Credits` is a documented natural-language coincidence, not a
paragraph fallback. Proper project names, copyright symbols and licence names are
retained in their attribution contexts.

**Remaining:** 35 non-English locales still have policy gaps: German lacks 120
sources, and each of the other 34 locales lacks 169 effective sources, for 5,866
missing source/locale pairs. German's agreement is already complete; its handbook
and privacy data remain incomplete. The other 34 need full handbook, privacy and
agreement authoring beyond their existing entries. This must not be described as
full-document coverage in all 39 languages. Wider Russian/Urdu interface gaps are
not addressed here. The global translation checklist remains incomplete and its
checkmarks were not changed.

## Checks

`app/test_policy_document_translation.py` includes source inventory, complete
Credits coverage, validation of actual authored entries, attribution and slot
checks, reactive field/RTL checks, real component construction, small-fixture
Node evaluation of compiled dynamic `ui()` lookup, and canonical open/switch/close
event checks without database writes. Its strict all-38/all-182 release gate
reports missing effective catalog entries and is expected to fail until the
remaining translations are authored. That original gate is unchanged and has not
been rerun in this bounded batch.

`app/test_policy_russian_urdu_translation.py` independently checks exact literal
85/51-field rows for precisely two locales (272 fields), runtime merged safety
inventory, 50→182 authored coverage, 182-source effective coverage without English
fallback, retained privacy/Credits values and attribution, placeholders, dates,
age, distance and emergency numbers, native-word liability limits and legal
exceptions, long-paragraph anti-summary checks, and a small Node fixture executing
the compiled reactive lookup across Russian, Urdu and English. It also computes
the dedicated/effective global counts and documents the 35 remaining locale gaps;
this partial-status check is not a replacement or waiver of the all-38 gate.

Focused tests and programmatic coverage verification are **pending the director's
run**; no tests were executed in this turn. An independently frozen full-English
checksum fixture and human linguistic/legal review are not supplied. No human
review or legal certification is claimed.
