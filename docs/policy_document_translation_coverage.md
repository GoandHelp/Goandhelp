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
- Privacy: all 41 fields in French, German, Spanish, Russian and Urdu (the date
  is already included in Credits).
- User agreement: all 51 fields in French, German, Spanish, Russian and Urdu
  (the shared date is already included in Credits).
- Handbook: all 85 fields in French, German, Spanish, Russian and Urdu,
  including the entire merged safety notice and every safety section (the shared
  date is already included in Credits).
- Spanish batch: `app/policy_catalog_howto_spanish.py` (85),
  `app/policy_catalog_privacy_spanish.py` (41) and
  `app/policy_catalog_agreement_spanish.py` (51) add exactly 177 literal
  whole-field Spanish translations in the app's informal `tú` register. After
  the shared date is deduplicated they supply 174 new distinct authored sources
  and close Spanish's 169 effective gaps. The literal date reuses the existing
  Spanish Credits wording, so the Credits entry is never overwritten. Plan labels
  use the Spanish names already shown on the paywall (Billete mensual, Pase
  anual); Go and Help, Stripe, Resend and OpenFreeMap are kept as proper names.
- Russian and Urdu reader chrome and footer disclaimer remain registered.
- This German-only batch adds exactly 126 literal whole-field translations:
  85 handbook fields and 41 privacy fields, supplying 124 new distinct authored
  sources after shared dates are deduplicated. German agreement and Credits,
  French/Russian/Urdu and every other locale, and canonical English are untouched.

Director-verified current baseline (after the German batch, runtime audit):
**1,000 authored**, **1,170 effective** and **5,746 missing** canonical
source/locale pairs out of 6,916 (38 × 182), with French, German, Russian and
Urdu complete and Spanish at 169 gaps. Expected after this Spanish batch:
1,000 + 174 = **1,174 authored**, 1,170 + 169 = **1,339 effective** and
5,746 − 169 = **5,577 missing** pairs. These post-write totals are pending the
director's run; they are not claimed as an executed test result.
Reader chrome is excluded. French, German, Spanish, Russian and Urdu are expected
to supply all 182 sources each; the other 33 locales retain eight dedicated and
13 effective sources apiece.
not wider interface coverage. The German focused test computes actual catalog
counts and checks these minimum gains without freezing other locales' progress.
The Dutch title `Credits` is a documented natural-language coincidence, not a
paragraph fallback. Proper project names, copyright symbols and licence names are
retained in their attribution contexts.

**Remaining:** 33 non-English locales need full handbook, privacy and agreement
translations beyond their existing entries: 169 effective gaps each, or
**5,577** missing pairs (33 × 169), pending post-write verification. Later
languages follow in later batches. This is not full-document coverage in all
39 languages.
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

The German coverage itself is verified by the current runtime audit. One German
fixture was repaired: the frozen full indemnity paragraph is now looked up by
its canonical source (`startswith('You agree to indemnify')`, index 43) rather
than the magic index 42, which pointed at the heading. The expected paragraph
and the German data are unchanged; that repaired method is pending the
director's run.

`app/test_policy_spanish_translation.py` adds four focused checks: pure literal
85/41/51-field Spanish-only rows that pass `validate_rows`; native whole-field
entries with placeholder, numeral, proper-name, informal-register and
anti-summary guards (word-length minimum and no copied six-word English runs);
all 182 Spanish sources authored and effective without English fallback,
preserved Spanish Credits, and progress-safe global minimums (authored ≥1,174,
effective ≥1,339, covered + missing = 6,916, fr/de/es/ru/ur complete); the full
merged safety inventory plus representative privacy and agreement paragraphs
(500m/1km, 0.5–1 km, 112/999/911/000, age 16, renewal, cancellation, no refund
unless local law requires, the greater of twelve months' fees or fifty US
dollars, non-excludable liability and mandatory consumer rights); and the frozen
canonical English SHA-256 checksum. Fixtures are bound by canonical source,
never by row index. This suite is **pending the director's run**.

The original strict all-38/all-182 release gate is unchanged. No human
linguistic/legal review or legal certification is claimed.
