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
  Russian, Turkish, Indonesian, Urdu, Vietnamese, Thai, Hindi, Arabic, Persian,
  Hebrew, Swahili, Amharic, Chinese, Bengali and Gujarati (the shared date is already
  included in Credits).
- User agreement: all 51 fields in French, German, Spanish, Italian, Dutch,
  Swedish, Danish, Finnish, Czech, Polish, Portuguese, Hungarian, Romanian,
  Greek, Russian, Turkish, Indonesian, Urdu, Vietnamese, Thai, Hindi, Arabic,
  Persian, Hebrew, Swahili, Amharic, Chinese, Bengali and Gujarati (the date is already
  included in Credits).
- Handbook: all 85 fields in French, German, Spanish, Italian, Portuguese,
  Dutch, Swedish, Danish, Finnish, Czech, Polish, Hungarian, Romanian, Greek,
  Russian, Turkish, Indonesian, Urdu, Vietnamese, Thai, Hindi, Arabic, Persian,
  Hebrew, Swahili, Amharic, Chinese, Bengali and Gujarati, including the entire merged
  safety notice and every safety section (the shared date is already included in
  Credits).
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
  adds 174 distinct authored sources and closes all 169 Greek gaps. Its four
  focused checks passed at **3,088 authored, 3,198 effective and 3,718 missing**.
  One test-only repair aligned the existing `Emergencies` heading precedence;
  Greek translation data was unchanged.
- Turkish batch: the three `*_turkish.py` catalogs contain 177 literal Turkish
  fields, including all merged safety content. Its four focused checks and the
  unconditional attribution guard passed; actual totals are **3,262 authored,
  3,367 effective and 3,549 missing**. Repair restored the original validator
  and Credits subtitle, added the missing Go and Help name to one Turkish safety
  paragraph, and adjusted the test to preserve the existing effective Credits
  title. Plan labels are Aylık bilet and Yıllık geçiş.
- Indonesian batch: the three `*_indonesian.py` catalogs add 177 literal Bahasa
  Indonesia fields, including the complete merged safety content. Its four focused
  checks passed at **3,436 authored, 3,536 effective and 3,380 missing**, closing
  all 169 Indonesian gaps; 18 locales are complete. Plan labels are Tiket bulanan
  and Pas tahunan. A one-line date-count fixture repair changed no native data.
- Vietnamese batch: the three `*_vietnamese.py` catalogs add 177 literal,
  complete Vietnamese fields, including the full merged safety notice and every
  safety section. The shared date matches the existing Credits date exactly;
  `Vé tháng` and `Vé năm` are the generic plan names. Its four focused checks
  passed at **3,610 authored, 3,705 effective and 3,211 missing**; Vietnamese is
  fully covered and 19 locales are complete.
- Thai batch: `app/policy_catalog_howto_thai.py` (85),
  `app/policy_catalog_privacy_thai.py` (41) and
  `app/policy_catalog_agreement_thai.py` (51) add 177 literal Thai fields,
  including all merged safety content. Reusing the exact Credits date adds 174
  distinct authored sources and closes all 169 Thai effective gaps. Plan labels
  are `ตั๋วรายเดือน` and `บัตรรายปี`. Its four focused checks are **verified
  passed** at **3,784 authored, 3,874 effective and 3,042 missing**; 20 locales
  are complete including Thai.
- Hindi batch: `app/policy_catalog_howto_hindi.py` (85),
  `app/policy_catalog_privacy_hindi.py` (41) and
  `app/policy_catalog_agreement_hindi.py` (51) add 177 literal Devanagari Hindi
  fields in the polite `आप` register, including the full merged safety notice
  and every safety section. The exact Credits date is reused, so the batch adds
  174 authored sources and closes all 169 Hindi effective gaps. Plan labels are
  `मासिक टिकट` and `वार्षिक पास`. Its four focused checks are **verified
  passed** at **3,958 authored, 4,043 effective and 2,873 missing**; 21 locales
  are complete including Hindi.
- Arabic batch: the three `*_arabic.py` catalogs provide 177 full literal
  Modern Standard Arabic fields, including all merged safety content. Its four
  focused checks passed with **4,132 authored, 4,212 effective and 2,704
  missing**; 22 locales were complete at that checkpoint.
- Persian batch: the three `*_persian.py` catalogs provide 177 full literal
  Persian fields, including all merged safety content. Its four checks passed
  with **4,306 authored, 4,381 effective and 2,535 missing**. Persian is among
  the 23 complete locales; the existing eight-field Credits row is unchanged.
- Hebrew batch: the three `*_hebrew.py` catalogs add 177 literal full-field
  translations, including every merged safety field. Its four checks passed;
  verified totals are **4,480 authored, 4,550 effective and 2,366 missing**,
  with 24 complete locales.
- Swahili batch: its three catalogs contain 177 Kiswahili fields, including the
  full merged safety content. Four focused checks passed at **4,654 authored,
  4,719 effective and 2,197 missing**; 25 locales are complete. Two incorrect
  test phrases were aligned with the existing native location paragraph; its
  translation data was unchanged.
- Amharic batch: the three `*_amharic.py` catalogs add 177 full literal Amharic
  fields, including the complete merged safety content. The exact Credits date
  is reused; plan labels are ወርሃዊ ትኬት and ዓመታዊ ፓስ. Its four focused checks are
  **verified passed** at **4,828 authored, 4,888 effective and 2,028 missing**;
  26 locales are complete including Amharic. Two incorrect fixture expectations
  (the effective Credits title and the complete joint monthly/annual renewal
  clause) were corrected; Amharic translation data was unchanged.
- Chinese batch: `app/policy_catalog_howto_chinese.py` (85),
  `app/policy_catalog_privacy_chinese.py` (41) and
  `app/policy_catalog_agreement_chinese.py` (51) add 177 full literal Simplified
  Chinese fields in the polite 您 register, including the complete merged safety
  content. The exact Credits date `更新并生效于2024年6月1日` is reused and the five
  existing titles/headings are kept exactly; plan labels are 月票 and 年票. The
  batch adds 174 authored sources and closes 169 effective gaps. Its four focused
  checks passed at **5,002 authored, 5,057 effective and 1,859 missing**, with 27
  complete locales including Chinese and 11 remaining locales at 169 gaps each.
- Bengali batch: `app/policy_catalog_howto_bengali.py` (85),
  `app/policy_catalog_privacy_bengali.py` (41) and
  `app/policy_catalog_agreement_bengali.py` (51) implement 177 full literal
  Bengali fields in the polite `আপনি` register, including all merged safety
  content. The exact existing Credits date is reused; the batch adds 174 distinct
  authored sources and is expected to close all 169 Bengali gaps. The expected
  checkpoint is **5,176 authored, 5,226 effective and 1,690 missing**, with 28
  complete locales. Bengali's four focused checks passed and these totals were
  verified; two source-reference fixture fixes changed no Bengali translation data.
- Gujarati batch: `app/policy_catalog_howto_gujarati.py` (85),
  `app/policy_catalog_privacy_gujarati.py` (41) and
  `app/policy_catalog_agreement_gujarati.py` (51) add 177 literal full-field
  Gujarati translations in a polite register, including all merged safety
  content. They reuse the exact Gujarati Credits date, add 174 distinct authored
  sources and close all 169 Gujarati effective gaps. The Credits catalog and its
  existing effective title are unchanged. Focused checks are pending; expected
  checkpoint totals are **5,350 authored, 5,395 effective and 1,521 missing**,
  with 29 complete locales. Overall coverage remains partial for the 39-language
  deliverable.

Chinese's four focused checks verified **5,002 authored, 5,057 effective and
1,859 missing** pairs, with 27 complete locales. Bengali's four focused checks
verified **5,176 authored, 5,226 effective and 1,690 missing** pairs, with 28
complete locales. The Gujarati checkpoint is expected to reach **5,350 authored,
5,395 effective and 1,521 missing** pairs, with 29 complete locales; its focused
checks remain pending. Progress guards do not require other locales to remain
incomplete; reader chrome is excluded. The Dutch title `Credits` is a documented
natural-language coincidence, not a paragraph fallback. Native effective Credits
titles are preserved separately from authored titles. Wider interface gaps are
outside this batch.
Progress guards do not require other locales to remain incomplete; reader chrome
is excluded. The Dutch title `Credits` is a documented natural-language
coincidence, not a paragraph fallback. Native effective Credits titles are
preserved separately from authored titles. Coverage remains partial for the
39-language deliverable; wider interface gaps are outside this batch.

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

`app/test_policy_turkish_translation.py` adds four focused checks for exact
literal 85/41/51-field Turkish-only rows, native text and anti-summary safeguards,
all-source authored/effective coverage, preserved Credits, the merged safety
inventory and source-bound location, age, emergency, renewal, cancellation,
refund, maximum-liability and consumer-rights clauses, progress-safe totals, and
the frozen canonical English checksum. All four checks passed, as did the
unconditional attribution guard; the verified totals are **3,262 authored,
3,367 effective and 3,549 missing**. The repair restored the validator and
original Credits subtitle, fixed one missing Go and Help attribution in a Turkish
safety paragraph, and aligned the test with the existing effective Credits title.

`app/test_policy_indonesian_translation.py` adds four focused checks for exact
literal 85/41/51-field Indonesian-only rows, complete native fields, placeholders,
proper names, numeric facts and anti-summary thresholds; authored/effective
coverage and frozen Credits; merged safety and source-bound location, age,
emergency, renewal, cancellation, refund, liability and consumer-rights clauses;
progress-safe totals; and the frozen English checksum. All four checks passed at
**3,436 authored, 3,536 effective and 3,380 missing**. A one-line date-count test
fixture repair changed no translation data.

`app/test_policy_vietnamese_translation.py` adds four focused checks for literal
85/41/51-field Vietnamese-only rows, native full fields, placeholders, proper
names, numerals and long-paragraph anti-summary safeguards; complete authored
and effective sources with frozen eight-field Credits; all merged safety content
and source-bound privacy, age, emergency, renewal, cancellation, refund,
maximum-liability and consumer-rights clauses; progress-safe totals; and the
frozen English checksum. All four checks passed with **3,610 authored, 3,705
effective and 3,211 missing**.

`app/test_policy_thai_translation.py` adds four focused checks for literal
85/41/51-field Thai-only rows, Thai-script-aware full-field content, placeholders,
proper names, numerals and character-length anti-summary safeguards without
space-delimited word-count assumptions; all 182 Thai authored/effective sources
with frozen Credits; every merged safety field and source-bound privacy, age,
emergency, renewal, cancellation, refund, maximum-liability and consumer-rights
clauses; progress-safe totals; and the frozen English checksum. All four checks
passed at **3,784 authored, 3,874 effective and 3,042 missing**.

`app/test_policy_hindi_translation.py` adds four focused checks for pure literal
85/41/51-field Hindi-only rows, native Devanagari without English prose,
placeholders, proper names, numerals and anti-summary thresholds; 182-source
authored/effective coverage with the frozen eight-field Credits row; all merged
safety fields and source-bound privacy, age, emergency, renewal, cancellation,
refund, maximum-liability and consumer-rights clauses; progress-safe totals
(authored ≥3,958, effective ≥4,043); and the frozen English checksum. All four
checks passed at **3,958 authored, 4,043 effective and 2,873 missing**.

`app/test_policy_arabic_translation.py` has four focused checks for literal
85/41/51-field Arabic rows, complete merged safety text, legal and privacy
safeguards, the frozen Credits and English source, and progress-safe coverage.
All four checks passed with **4,132 authored, 4,212 effective and 2,704
missing**.

`app/test_policy_persian_translation.py` adds four focused checks for literal
85/41/51-field Persian-only rows, native script and complete paragraphs,
placeholders, names, numerals and anti-summary thresholds; full 182-source
Persian coverage and unchanged Credits; merged safety and source-bound privacy,
age, emergency, renewal, cancellation, refund, liability and consumer-rights
clauses; progress-safe totals; and the frozen English checksum. All four checks
passed at **4,306 authored, 4,381 effective and 2,535 missing**.

`app/test_policy_hebrew_translation.py` adds four focused checks for literal
85/41/51-field rows, merged safety, full privacy and agreement safeguards,
complete coverage, frozen Credits and the canonical English checksum. All four
checks passed; verified totals are **4,480 authored, 4,550 effective and 2,366
missing**.

`app/test_policy_swahili_translation.py` has four focused checks for exact
literal Kiswahili rows, full merged safety and legal/privacy safeguards, full
source coverage, frozen Credits, progress-safe totals and the canonical English
checksum. All four checks passed at **4,654 authored, 4,719 effective and 2,197
missing**. Two fixture phrases were corrected to match the native translation;
no Swahili data changed.

`app/test_policy_amharic_translation.py` adds four focused checks for pure
literal 85/41/51-field Amharic rows, Ethiopic-script-native content, proper names,
placeholders, numerals and character/word-aware anti-summary bounds; full merged
safety and source-bound privacy, age, emergency, renewal, cancellation, refund,
maximum-liability and consumer-rights safeguards; frozen Credits; progress-safe
totals; and the canonical English checksum. All four checks passed at **4,828
authored, 4,888 effective and 2,028 missing**; two fixture expectations were
corrected and the Amharic data was unchanged.

`app/test_policy_chinese_translation.py` adds four focused checks for pure
literal 85/41/51-field Chinese-only rows, native CJK text without English prose,
placeholders, proper names and numerals; a character-based CJK anti-summary
bound (no whitespace word ratios) plus complete source-bound clause guards for
privacy, no-coordinate Off mode, age, emergency numbers, monthly/annual renewal,
cancellation, local-law refunds, the higher-of 12-month fees or 50 USD cap,
non-excludable liability and local consumer rights; merged safety; the frozen
eight-field Credits row with its Credits-only effective title; progress-safe
totals; and the canonical English checksum. Its four focused checks passed with
**5,002 authored, 5,057 effective and 1,859 missing**.

`app/test_policy_bengali_translation.py` adds four focused checks for literal
85/41/51-field Bengali-only rows, native-script full fields, placeholders, proper
names, numeric facts and long-paragraph anti-summary bounds; all 182 authored and
effective sources with unchanged eight-field Credits and frozen Credits/English
checksums; all merged safety fields and source-bound safeguards for location,
age, emergency numbers, monthly and annual renewal, cancellation, refunds,
liability and local consumer rights; and progress-safe global totals. Its four
checks passed at **5,176 authored, 5,226 effective and 1,690 missing**; two
source-reference fixture fixes changed no Bengali translation data.

`app/test_policy_gujarati_translation.py` adds four focused checks for literal
85/41/51-field Gujarati-only rows, complete natural Gujarati fields, coverage of
all 182 sources, the frozen Credits and English catalogs, all merged safety
fields, source-bound location and legal safeguards, and progress-safe totals.
These checks remain pending; the expected totals are 5,350 authored, 5,395
effective and 1,521 missing.

The original strict all-38/all-182 release gate is unchanged. No human
linguistic/legal review or legal certification is claimed.
