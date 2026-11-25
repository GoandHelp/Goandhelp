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
- Privacy: all 41 fields in French, German, Spanish, Italian, Portuguese,
  Dutch, Swedish, Danish, Finnish, Czech, Polish, Hungarian, Romanian, Greek,
  Russian and Urdu (the date is already included in Credits).
- User agreement: all 51 fields in French, German, Spanish, Italian, Dutch,
  Swedish, Danish, Finnish, Czech, Polish, Portuguese, Hungarian, Romanian,
  Greek, Russian and Urdu (the shared date is already included in Credits).
- Handbook: all 85 fields in French, German, Spanish, Italian, Portuguese,
  Dutch, Swedish, Danish, Finnish, Czech, Polish, Hungarian, Romanian, Greek,
  Russian and Urdu, including the entire merged safety notice
  and every safety section (the shared date is already included in Credits).
- Spanish batch: `app/policy_catalog_howto_spanish.py` (85),
  `app/policy_catalog_privacy_spanish.py` (41) and
  `app/policy_catalog_agreement_spanish.py` (51) add exactly 177 literal
  whole-field Spanish translations in the app's informal `tú` register. After
  the shared date is deduplicated they supply 174 new distinct authored sources
  and close Spanish's 169 effective gaps. The literal date reuses the existing
  Spanish Credits wording, so the Credits entry is never overwritten. Plan labels
  use the Spanish names already shown on the paywall (Billete mensual, Pase
  anual); Go and Help, Stripe, Resend and OpenFreeMap are kept as proper names.
- Italian batch: `app/policy_catalog_howto_italian.py` (85),
  `app/policy_catalog_privacy_italian.py` (41) and
  `app/policy_catalog_agreement_italian.py` (51) add 177 literal whole-field
  translations, including the complete merged safety notice and sections.
  After deduplicating the date already present in Italian Credits, these add
  174 distinct authored sources and close Italy's 169 effective gaps. The
  date reuses the existing Italian Credits wording; generic plan labels are
  `Biglietto mensile` and `Pass annuale`.
- Portuguese batch: `app/policy_catalog_howto_portuguese.py` (85),
  `app/policy_catalog_privacy_portuguese.py` (41) and
  `app/policy_catalog_agreement_portuguese.py` (51) contain 177 full literal
  European Portuguese fields, including all merged safety sections. Deduplicating
  the existing Credits date gives 174 new authored sources and closes
  Portuguese's 169 effective gaps. Its four focused checks passed and verified
  the post-batch totals below. The shared date reuses the existing Credits
  wording; plan labels are Bilhete mensal and Passe anual.
- Dutch batch: `app/policy_catalog_howto_dutch.py` (85),
  `app/policy_catalog_privacy_dutch.py` (41) and
  `app/policy_catalog_agreement_dutch.py` (51) provide 177 literal Dutch fields,
  including the complete merged safety content. Deduplicating the Credits date
  adds 174 authored sources and closes all 169 Dutch gaps. The date reuses the
  exact existing Credits wording; plan labels are Maandkaart and Jaarpas. Its
  four focused checks and post-batch totals are **verified passed**.
- Swedish batch: `app/policy_catalog_howto_swedish.py` (85),
  `app/policy_catalog_privacy_swedish.py` (41) and
  `app/policy_catalog_agreement_swedish.py` (51) contain exactly 177 literal
  Swedish fields, including all merged safety content. After deduplicating the
  existing Credits date they add 174 authored sources and close all 169 Swedish
  gaps. The exact existing date is reused; plan labels are Månadskort and
  Årspass. Its four focused checks **passed**: 1,870 authored, 2,015 effective
  and 4,901 missing; nine locales are complete (German, Spanish, French,
  Italian, Dutch, Portuguese, Russian, Swedish and Urdu).
- Danish batch: `app/policy_catalog_howto_danish.py` (85),
  `app/policy_catalog_privacy_danish.py` (41) and
  `app/policy_catalog_agreement_danish.py` (51) provide exactly 177 literal
  whole-field translations, including the complete merged safety content. The
  existing Credits date is reused; Danish plan labels are Månedskort and
  Årspas. Deduplicating that date adds 174 authored sources and closes all 169
  Danish gaps. Its four focused checks are verified **passed**; a fixture-only
  repair corrected paragraph-bound plan-label and complete native privacy
  negation assertions without changing correct translation data.
- Finnish batch: `app/policy_catalog_howto_finnish.py` (85),
  `app/policy_catalog_privacy_finnish.py` (41) and
  `app/policy_catalog_agreement_finnish.py` (51) add exactly 177 literal,
  complete Finnish fields, including all merged safety content. Its four focused
  checks **passed** with 2,218 authored, 2,353 effective and 4,563 missing pairs;
  eleven locales are complete (Danish, Finnish, German, Spanish, French, Italian,
  Dutch, Portuguese, Russian, Swedish and Urdu). One incorrect grammatical test
  fixture was repaired; native Finnish data was untouched.
- Czech batch: `app/policy_catalog_howto_czech.py` (85),
  `app/policy_catalog_privacy_czech.py` (41) and
  `app/policy_catalog_agreement_czech.py` (51) contain 177 full literal Czech
  fields, including the complete merged safety content. Its four focused checks
  passed with **2,392 authored, 2,522 effective and 4,394 missing**; all 169 Czech
  effective gaps are closed. One incorrectly shortened refund test token was
  repaired in a single fixture-only line; the correct Czech data was unchanged.
- Russian and Urdu reader chrome and footer disclaimer remain registered.

Verified after Finnish: **2,218 authored**, **2,353 effective** and **4,563
missing** canonical source/locale pairs out of 6,916. Eleven locales (Danish,
Finnish, German, Spanish, French, Italian, Dutch, Portuguese, Russian, Swedish
and Urdu) are complete. Finnish's four focused checks and actual totals are
verified passed; its one-line repair changed only an incorrect grammatical test
fixture, leaving the native Finnish data and all prior locales untouched.

Verified after Czech: **2,392 authored, 2,522 effective and 4,394 missing**
canonical source/locale pairs. Twelve locales (Czech, Danish, Finnish, German,
Spanish, French, Italian, Dutch, Portuguese, Russian, Swedish and Urdu) are
complete. Czech's four focused checks passed; one incorrect refund fixture token
was repaired without changing native Czech data.

- Polish batch: `app/policy_catalog_howto_polish.py` (85),
  `app/policy_catalog_privacy_polish.py` (41) and
  `app/policy_catalog_agreement_polish.py` (51) add exactly 177 full literal
  Polish fields, including all merged safety content. Its four focused checks
  **passed** with actual totals of 2,566 authored, 2,691 effective and 4,225
  missing pairs; thirteen locales (Czech, Danish, Finnish, German, Spanish,
  French, Italian, Dutch, Polish, Portuguese, Russian, Swedish and Urdu) are
  complete. A two-line fixture-only repair corrected one grammatical-case
  assertion and the distinction between 175 unique keys and 177 total rows;
  Polish translation text was unchanged.
- Hungarian batch: `app/policy_catalog_howto_hungarian.py`,
  `app/policy_catalog_privacy_hungarian.py` and
  `app/policy_catalog_agreement_hungarian.py` add 177 complete literal fields,
  including every merged safety field. The exact existing Credits date is
  reused; plan labels are Havi jegy and Éves bérlet. Four focused checks are
  verified passed at **2,740 authored, 2,860 effective and 4,056 missing**. A
  four-string fixture-only wording repair changed no Hungarian translation data.
- Romanian batch: the three `*_romanian.py` catalogs add 177 literal fields,
  including all merged safety content; deduplicating the exact Credits date adds
  174 authored sources and closes all 169 Romanian gaps. Its four focused checks
  passed at **2,914 authored, 3,029 effective and 3,887 missing**; a two-string
  test-fixture repair changed no native Romanian text. Fifteen locales are
  complete: Czech, Danish, German, Spanish, Finnish, French, Hungarian, Italian,
  Dutch, Polish, Portuguese, Romanian, Russian, Swedish and Urdu.
- Greek batch: the three `*_greek.py` catalogs contain 177 literal Modern Greek
  fields, including all merged safety content. Reusing the exact Credits date
  adds 174 distinct authored sources and is expected to close all 169 Greek
  gaps. Greek checks and post-batch totals are pending execution; expected totals
  are **3,088 authored, 3,198 effective and 3,718 missing**, with 16 complete
  locales including Greek and 22 remaining locales with 169 gaps each.

Verified after Romanian and before Greek: **2,914 authored, 3,029 effective
and 3,887 missing** canonical source/locale pairs. Progress guards do not require
other locales to remain incomplete. Reader chrome is excluded.
The Dutch title `Credits` is a documented natural-language coincidence, not a
paragraph fallback. Swedish's native effective Credits title `Tack till
bidragsgivarna`, Danish's `Tak til bidragyderne`, Finnish's `Kiitokset`, Czech's
`Poděkování` and Polish's `Podziękowania` are preserved separately from their
authored Credits titles. Project names, copyright symbols and licence names are
retained in attribution contexts.

**Remaining:** after the Greek batch is verified, 22 non-English locales are
expected to need full handbook, privacy and agreement translations beyond their
existing entries: 169 effective gaps each, or **3,718** missing pairs (22 × 169).
Greek checks and these projected totals are pending. This is not full-document
coverage in all 39 languages. Wider interface gaps are not addressed here. The
global checklist remains incomplete and its checkmarks were not changed.

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

The four Italian focused checks are verified; its focused checks use canonical source lookups, not magic row indices.

`app/test_policy_spanish_translation.py` adds four focused checks for its
literal field rows, Spanish content, complete source coverage, merged safety,
representative legal wording and the canonical English checksum. These checks
have passed.

`app/test_policy_italian_translation.py` adds four focused checks for literal
85/41/51-field rows, native entries and the complete merged safety inventory,
with legal and progress-safe coverage guards. All four checks passed; Italian
repairs were fixture-only and its data remains unchanged.

`app/test_policy_portuguese_translation.py` adds four focused checks for literal
85/41/51-field rows, full native Portuguese entries, all 182 authored/effective
sources, preserved Credits, merged safety and representative legal conditions.
It also checks progress-safe global totals and the frozen canonical English
SHA-256 checksum. Fixtures use canonical source prefixes. All four checks and
post-write totals have passed verification: **1,522 authored**, **1,677
effective**, **5,239 missing**.

`app/test_policy_dutch_translation.py` adds four focused checks for exact
literal 85/41/51-field Dutch-only rows, native full-field text, all 182 Dutch
authored/effective sources, unchanged Credits, merged safety, representative
privacy and agreement safeguards, progress-safe totals, and the frozen English
checksum. Its fixtures bind to canonical source prefixes. All four Dutch checks
and actual post-write totals are verified passed: **1,696 authored**, **1,846
effective** and **5,070 missing**.

`app/test_policy_swedish_translation.py` adds four focused checks for exact
literal 85/41/51-field Swedish-only rows, native full-field text, placeholders,
proper names, numerals and long-paragraph anti-summary safeguards; all 182
Swedish authored/effective sources; preserved authored Credits and its distinct
native effective title; merged safety inventory; representative location, age,
emergency, payment, cancellation, refund, liability and consumer-rights clauses;
progress-safe totals; and the frozen English checksum. All four Swedish checks
passed with 1,870 authored, 2,015 effective and 4,901 missing pairs.

`app/test_policy_danish_translation.py` adds four focused checks for exact
literal 85/41/51-field Danish-only rows, native full-field text, placeholders,
proper names, numerals (including decimal-comma equivalence) and long-paragraph
anti-summary safeguards; all 182 Danish authored/effective sources; preserved
authored Credits and its distinct native effective title; merged safety
inventory; representative location, age, emergency, renewal, cancellation,
refund, liability and consumer-rights clauses; progress-safe totals; and the
frozen English checksum. Its four checks passed with **2,044 authored, 2,184
effective and 4,732 missing**; only flawed test fixtures were repaired.

`app/test_policy_finnish_translation.py` adds four focused checks for exact
literal 85/41/51-field Finnish-only rows, native full-field content, placeholders,
proper names, numerals and long-paragraph anti-summary safeguards with Finnish
compound-aware thresholds; all 182 authored/effective sources and unchanged
Credits, including its effective native title; the complete merged safety
inventory and source-bound location, age, emergency, renewal, cancellation,
refund, liability and consumer-rights clauses; progress-safe totals; and the
frozen English checksum. All four checks passed; the sole repair was to one
incorrect grammatical fixture, with native Finnish data untouched.

`app/test_policy_czech_translation.py` adds four focused checks for exact literal
85/41/51-field Czech-only rows, full native fields, placeholders, proper names,
numerals and long-paragraph anti-summary safeguards; complete authored/effective
coverage with preserved Credits; the merged safety inventory and source-bound
privacy, age, emergency, renewal, cancellation, refund, liability and consumer
rights clauses; progress-safe totals; and the frozen English checksum. All four
checks passed with **2,392 authored, 2,522 effective and 4,394 missing**. One
incorrectly shortened refund assertion was repaired in a single fixture-only
line; Czech translation data is unchanged. This focused batch does not replace
or waive the unchanged strict all-38/all-182 release gate.

`app/test_policy_polish_translation.py` adds four focused checks for exact
literal 85/41/51-field Polish-only rows, native complete fields, placeholders,
proper names, numerals and long-paragraph anti-summary safeguards; complete
182-source authored/effective coverage with preserved Credits; all merged safety
fields and source-bound privacy, age, emergency, renewal, cancellation, refund,
maximum-liability and consumer-rights clauses; progress-safe totals; and the
frozen English checksum. All four checks passed with actual totals of 2,566
authored, 2,691 effective and 4,225 missing. Two fixture-only assertions were
repaired; the correct Polish text was unchanged. This focused batch does not
replace or waive the unchanged strict all-38/all-182 release gate.

`app/test_policy_hungarian_translation.py` adds four focused checks for exact
literal 85/41/51-field Hungarian-only rows, full native content, placeholders,
proper names, numerals and Hungarian compound-aware anti-summary safeguards;
complete 182-source authored/effective coverage with preserved Credits; every
merged safety field and source-bound location, privacy, age, emergency, payment,
refund, liability and consumer-rights conditions; progress-safe totals; and the
frozen English checksum. All four checks passed with actual totals of **2,740
authored, 2,860 effective and 4,056 missing**. A four-string fixture-only wording
repair changed no Hungarian translation data. This focused batch does not replace
or waive the unchanged strict all-38/all-182 release gate.

`app/test_policy_romanian_translation.py` adds four focused checks for exact
literal 85/41/51-field Romanian-only rows, complete native fields, placeholders,
proper names, numerals and long-paragraph anti-summary safeguards; all 182
Romanian authored/effective sources and unchanged Credits; the complete merged
safety inventory and source-bound location, age, emergency, renewal, cancellation,
refund, maximum-liability and consumer-rights clauses; progress-safe totals; and
the frozen English checksum. All four checks passed; a two-string test-fixture
repair changed no native Romanian text. This focused batch does not replace or
waive the unchanged strict all-38/all-182 release gate.

The Greek focused checks and post-batch totals remain pending execution.

The original strict all-38/all-182 release gate is unchanged. No human
linguistic/legal review or legal certification is claimed.
