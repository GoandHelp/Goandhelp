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
- Privacy: all 41 fields in French, German, Russian and Urdu (164 field entries,
  with the date already included in Credits).
- User agreement: all 51 fields in French, German, Russian and Urdu (204 field
  entries, with the shared date already included in Credits).
- Handbook: all 85 fields in French, German, Russian and Urdu, including the
  entire merged safety notice and every safety section (340 field entries,
  with the shared date already included in Credits).
- Russian and Urdu reader chrome and footer disclaimer remain registered.
- This German-only batch adds exactly 126 literal whole-field translations:
  85 handbook fields and 41 privacy fields, supplying 124 new distinct authored
  sources after shared dates are deduplicated. German agreement and Credits,
  French/Russian/Urdu and every other locale, and canonical English are untouched.

Coverage arithmetic from the director-verified pre-write baseline and this batch
is 876 + 124 = **1,000 authored** and 1,050 + 120 = **1,170 effective** canonical
source/locale pairs out of 6,916 (38 × 182). These post-write totals await the
 director's runtime verification; they are not claimed as an executed test result.
Reader chrome is excluded. French, German, Russian and Urdu now each supply all
182 sources; the other 34 locales retain eight dedicated and 13 effective sources
apiece. German moves from 58 to 182 authored sources and from 62 to 182 effective
sources, eliminating its 120 effective gaps. These are **policy-only** counts,
not wider interface coverage. The German focused test computes actual catalog
counts and checks these minimum gains without freezing other locales' progress.
The Dutch title `Credits` is a documented natural-language coincidence, not a
paragraph fallback. Proper project names, copyright symbols and licence names are
retained in their attribution contexts.

**Remaining:** 34 non-English locales need full handbook, privacy and agreement
translations beyond their existing entries: 169 effective gaps each, or
5,866 − 120 = **5,746** missing pairs (34 × 169), pending post-write verification.
Spanish is not included in this batch. This is not full-document coverage in all
39 languages. Wider interface gaps are not addressed here. The global checklist
remains incomplete and its checkmarks were not changed.

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
dedicated/effective global totals using progress-safe invariants (38 locales,
182 sources, French/Russian/Urdu complete, authored ≥876, effective ≥1,050 and
covered + missing = 6,916), rather than requiring any other locale to remain
incomplete. Only that method and the Russian indemnity token fixture were repaired;
the correct Russian translation itself was not changed. This check does not
replace or waive the unchanged strict all-38/all-182 release gate.

`app/test_policy_german_translation.py` adds five focused checks: pure literal
85/41-field German-only rows; nonempty native entries, placeholders, names and
anti-summary checks; complete 182-source authored/effective German coverage and
computed progress; all merged safety fields plus representative full privacy and
safety paragraphs and numerical facts; preserved agreement/Credits values; and
the director-frozen canonical English SHA-256 checksum
`404ee59a08a5b8fc3f5238768659a8df32b7ff7eda9279353cb86110ff575f3d`.

The seven Russian/Urdu checks and five German checks, including post-write actual
coverage verification, are **pending the director's run**; no tests were executed
in this turn. No human linguistic/legal review or legal certification is claimed.
