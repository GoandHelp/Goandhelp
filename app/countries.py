"""Safe country-name / ISO code resolution for profile nationality flags.

`resolve_nationality` never raises: unknown input is echoed back in a tidy
title-cased form with no flag, so a typo can never break the profile screen.
"""

import reflex as rx

ISO2_NAMES: dict[str, str] = {
    "AD": "Andorra",
    "AE": "United Arab Emirates",
    "AF": "Afghanistan",
    "AG": "Antigua and Barbuda",
    "AL": "Albania",
    "AM": "Armenia",
    "AO": "Angola",
    "AZ": "Azerbaijan",
    "BA": "Bosnia and Herzegovina",
    "BB": "Barbados",
    "BF": "Burkina Faso",
    "BH": "Bahrain",
    "BI": "Burundi",
    "BJ": "Benin",
    "BN": "Brunei",
    "BS": "Bahamas",
    "BT": "Bhutan",
    "BW": "Botswana",
    "BY": "Belarus",
    "BZ": "Belize",
    "CD": "Democratic Republic of the Congo",
    "CF": "Central African Republic",
    "CG": "Republic of the Congo",
    "CI": "Côte d'Ivoire",
    "CM": "Cameroon",
    "CV": "Cabo Verde",
    "CY": "Cyprus",
    "DJ": "Djibouti",
    "DM": "Dominica",
    "ER": "Eritrea",
    "FJ": "Fiji",
    "FM": "Micronesia",
    "GA": "Gabon",
    "GD": "Grenada",
    "GM": "Gambia",
    "GN": "Guinea",
    "GQ": "Equatorial Guinea",
    "GW": "Guinea-Bissau",
    "GY": "Guyana",
    "HN": "Honduras",
    "HT": "Haiti",
    "KG": "Kyrgyzstan",
    "KI": "Kiribati",
    "KM": "Comoros",
    "KN": "Saint Kitts and Nevis",
    "KP": "North Korea",
    "KW": "Kuwait",
    "KZ": "Kazakhstan",
    "LA": "Laos",
    "LB": "Lebanon",
    "LC": "Saint Lucia",
    "LI": "Liechtenstein",
    "LR": "Liberia",
    "LS": "Lesotho",
    "LY": "Libya",
    "MC": "Monaco",
    "MD": "Moldova",
    "ME": "Montenegro",
    "MG": "Madagascar",
    "MH": "Marshall Islands",
    "MK": "North Macedonia",
    "ML": "Mali",
    "MM": "Myanmar",
    "MN": "Mongolia",
    "MR": "Mauritania",
    "MT": "Malta",
    "MU": "Mauritius",
    "MV": "Maldives",
    "MW": "Malawi",
    "MZ": "Mozambique",
    "NA": "Namibia",
    "NE": "Niger",
    "NI": "Nicaragua",
    "NR": "Nauru",
    "OM": "Oman",
    "PG": "Papua New Guinea",
    "PS": "Palestine",
    "PW": "Palau",
    "QA": "Qatar",
    "RW": "Rwanda",
    "SB": "Solomon Islands",
    "SC": "Seychelles",
    "SD": "Sudan",
    "SL": "Sierra Leone",
    "SM": "San Marino",
    "SO": "Somalia",
    "SR": "Suriname",
    "SS": "South Sudan",
    "ST": "Sao Tome and Principe",
    "SV": "El Salvador",
    "SY": "Syria",
    "SZ": "Eswatini",
    "TD": "Chad",
    "TG": "Togo",
    "TJ": "Tajikistan",
    "TL": "Timor-Leste",
    "TM": "Turkmenistan",
    "TO": "Tonga",
    "TT": "Trinidad and Tobago",
    "TV": "Tuvalu",
    "UZ": "Uzbekistan",
    "VA": "Vatican City",
    "VC": "Saint Vincent and the Grenadines",
    "VU": "Vanuatu",
    "WS": "Samoa",
    "XK": "Kosovo",
    "YE": "Yemen",
    "ZM": "Zambia",
    "ZW": "Zimbabwe",
    "AR": "Argentina",
    "AT": "Austria",
    "AU": "Australia",
    "BD": "Bangladesh",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "BO": "Bolivia",
    "BR": "Brazil",
    "CA": "Canada",
    "CH": "Switzerland",
    "CL": "Chile",
    "CN": "China",
    "CO": "Colombia",
    "CR": "Costa Rica",
    "CU": "Cuba",
    "CZ": "Czechia",
    "DE": "Germany",
    "DK": "Denmark",
    "DO": "Dominican Republic",
    "DZ": "Algeria",
    "EC": "Ecuador",
    "EE": "Estonia",
    "EG": "Egypt",
    "ES": "Spain",
    "ET": "Ethiopia",
    "FI": "Finland",
    "FR": "France",
    "GB": "United Kingdom",
    "GE": "Georgia",
    "GH": "Ghana",
    "GR": "Greece",
    "GT": "Guatemala",
    "HR": "Croatia",
    "HU": "Hungary",
    "ID": "Indonesia",
    "IE": "Ireland",
    "IL": "Israel",
    "IN": "India",
    "IQ": "Iraq",
    "IR": "Iran",
    "IS": "Iceland",
    "IT": "Italy",
    "JM": "Jamaica",
    "JO": "Jordan",
    "JP": "Japan",
    "KE": "Kenya",
    "KH": "Cambodia",
    "KR": "South Korea",
    "LK": "Sri Lanka",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LV": "Latvia",
    "MA": "Morocco",
    "MX": "Mexico",
    "MY": "Malaysia",
    "NG": "Nigeria",
    "NL": "Netherlands",
    "NO": "Norway",
    "NP": "Nepal",
    "NZ": "New Zealand",
    "PA": "Panama",
    "PE": "Peru",
    "PH": "Philippines",
    "PK": "Pakistan",
    "PL": "Poland",
    "PT": "Portugal",
    "PY": "Paraguay",
    "RO": "Romania",
    "RS": "Serbia",
    "RU": "Russia",
    "SA": "Saudi Arabia",
    "SE": "Sweden",
    "SG": "Singapore",
    "SI": "Slovenia",
    "SK": "Slovakia",
    "SN": "Senegal",
    "TH": "Thailand",
    "TN": "Tunisia",
    "TR": "Turkiye",
    "TW": "Taiwan",
    "TZ": "Tanzania",
    "UA": "Ukraine",
    "UG": "Uganda",
    "US": "United States",
    "UY": "Uruguay",
    "VE": "Venezuela",
    "VN": "Vietnam",
    "ZA": "South Africa",
}

WORLD_COUNTRY_NAMES: list[str] = sorted(set(ISO2_NAMES.values()))

# Curated Stripe presentment currencies, not a promise of local payment support.
STRIPE_CURRENCIES: dict[str, str] = {
    "USD": "US Dollar",
    "GBP": "British Pound",
    "EUR": "Euro",
    "CAD": "Canadian Dollar",
    "AUD": "Australian Dollar",
    "NZD": "New Zealand Dollar",
    "JPY": "Japanese Yen",
    "INR": "Indian Rupee",
    "CHF": "Swiss Franc",
    "CNY": "Chinese Yuan",
    "HKD": "Hong Kong Dollar",
    "SGD": "Singapore Dollar",
    "SEK": "Swedish Krona",
    "NOK": "Norwegian Krone",
    "DKK": "Danish Krone",
    "PLN": "Polish Zloty",
    "CZK": "Czech Koruna",
    "HUF": "Hungarian Forint",
    "RON": "Romanian Leu",
    "TRY": "Turkish Lira",
    "UAH": "Ukrainian Hryvnia",
    "BRL": "Brazilian Real",
    "MXN": "Mexican Peso",
    "ARS": "Argentine Peso",
    "CLP": "Chilean Peso",
    "COP": "Colombian Peso",
    "PEN": "Peruvian Sol",
    "UYU": "Uruguayan Peso",
    "CRC": "Costa Rican Colon",
    "DOP": "Dominican Peso",
    "ZAR": "South African Rand",
    "KES": "Kenyan Shilling",
    "NGN": "Nigerian Naira",
    "EGP": "Egyptian Pound",
    "MAD": "Moroccan Dirham",
    "TZS": "Tanzanian Shilling",
    "UGX": "Ugandan Shilling",
    "RWF": "Rwandan Franc",
    "XOF": "West African CFA Franc",
    "XAF": "Central African CFA Franc",
    "AED": "UAE Dirham",
    "SAR": "Saudi Riyal",
    "QAR": "Qatari Riyal",
    "ILS": "Israeli New Shekel",
    "THB": "Thai Baht",
    "IDR": "Indonesian Rupiah",
    "MYR": "Malaysian Ringgit",
    "PHP": "Philippine Peso",
    "VND": "Vietnamese Dong",
    "KRW": "South Korean Won",
    "TWD": "New Taiwan Dollar",
    "PKR": "Pakistani Rupee",
    "BDT": "Bangladeshi Taka",
    "LKR": "Sri Lankan Rupee",
    "NPR": "Nepalese Rupee",
    "ISK": "Icelandic Krona",
}
CURRENCY_OPTIONS: list[dict[str, str]] = [
    {"value": code, "label": f"{code} — {label}"}
    for code, label in sorted(STRIPE_CURRENCIES.items())
]
_CURRENCY_REGIONS: dict[str, str] = {
    "EUR": "AD AT BE BG CY DE EE ES FI FR GR HR IE IT LT LU LV MC ME MT NL PT SI SK SM VA XK",
    "GBP": "GB",
    "USD": "US EC SV PA FM MH PW TL",
    "AUD": "AU KI NR TV",
    "NZD": "NZ",
    "CAD": "CA",
    "JPY": "JP",
    "INR": "IN",
    "CHF": "CH LI",
    "CNY": "CN",
    "SGD": "SG",
    "SEK": "SE",
    "NOK": "NO",
    "DKK": "DK",
    "PLN": "PL",
    "CZK": "CZ",
    "HUF": "HU",
    "RON": "RO",
    "TRY": "TR",
    "UAH": "UA",
    "BRL": "BR",
    "MXN": "MX",
    "ARS": "AR",
    "CLP": "CL",
    "COP": "CO",
    "PEN": "PE",
    "UYU": "UY",
    "CRC": "CR",
    "DOP": "DO",
    "ZAR": "ZA",
    "KES": "KE",
    "NGN": "NG",
    "EGP": "EG",
    "MAD": "MA",
    "TZS": "TZ",
    "UGX": "UG",
    "RWF": "RW",
    "XOF": "BJ BF CI GW ML NE SN TG",
    "XAF": "CM CF TD CG GQ GA",
    "AED": "AE",
    "SAR": "SA",
    "QAR": "QA",
    "ILS": "IL PS",
    "THB": "TH",
    "IDR": "ID",
    "MYR": "MY",
    "PHP": "PH",
    "VND": "VN",
    "KRW": "KR",
    "TWD": "TW",
    "PKR": "PK",
    "BDT": "BD",
    "LKR": "LK",
    "NPR": "NP",
    "ISK": "IS",
}


def supported_currency(raw: str) -> str:
    code = (raw or "").strip().upper()
    return code if code in STRIPE_CURRENCIES else "USD"


def country_default_currency(country: str) -> str:
    if (country or "").strip().lower() in ("hong kong", "hk"):
        return "HKD"
    iso2 = resolve_nationality(country)[1]
    return next(
        (
            code
            for code, regions in _CURRENCY_REGIONS.items()
            if iso2 in regions.split()
        ),
        "USD",
    )


ISO3_TO_ISO2: dict[str, str] = {
    "ARG": "AR",
    "AUS": "AU",
    "AUT": "AT",
    "BEL": "BE",
    "BGD": "BD",
    "BGR": "BG",
    "BOL": "BO",
    "BRA": "BR",
    "CAN": "CA",
    "CHE": "CH",
    "CHL": "CL",
    "CHN": "CN",
    "COL": "CO",
    "CRI": "CR",
    "CUB": "CU",
    "CZE": "CZ",
    "DEU": "DE",
    "DNK": "DK",
    "DOM": "DO",
    "DZA": "DZ",
    "ECU": "EC",
    "EGY": "EG",
    "ESP": "ES",
    "EST": "EE",
    "ETH": "ET",
    "FIN": "FI",
    "FRA": "FR",
    "GBR": "GB",
    "GEO": "GE",
    "GHA": "GH",
    "GRC": "GR",
    "GTM": "GT",
    "HRV": "HR",
    "HUN": "HU",
    "IDN": "ID",
    "IND": "IN",
    "IRL": "IE",
    "IRN": "IR",
    "IRQ": "IQ",
    "ISL": "IS",
    "ISR": "IL",
    "ITA": "IT",
    "JAM": "JM",
    "JOR": "JO",
    "JPN": "JP",
    "KEN": "KE",
    "KHM": "KH",
    "KOR": "KR",
    "LKA": "LK",
    "LTU": "LT",
    "LUX": "LU",
    "LVA": "LV",
    "MAR": "MA",
    "MEX": "MX",
    "MYS": "MY",
    "NGA": "NG",
    "NLD": "NL",
    "NOR": "NO",
    "NPL": "NP",
    "NZL": "NZ",
    "PAK": "PK",
    "PAN": "PA",
    "PER": "PE",
    "PHL": "PH",
    "POL": "PL",
    "PRT": "PT",
    "PRY": "PY",
    "ROU": "RO",
    "RUS": "RU",
    "SAU": "SA",
    "SEN": "SN",
    "SGP": "SG",
    "SRB": "RS",
    "SVK": "SK",
    "SVN": "SI",
    "SWE": "SE",
    "THA": "TH",
    "TUN": "TN",
    "TUR": "TR",
    "TWN": "TW",
    "TZA": "TZ",
    "UGA": "UG",
    "UKR": "UA",
    "URY": "UY",
    "USA": "US",
    "VEN": "VE",
    "VNM": "VN",
    "ZAF": "ZA",
}

# Common aliases, demonyms and short forms travellers actually type.
ALIASES: dict[str, str] = {
    "uk": "GB",
    "u.k.": "GB",
    "great britain": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "britain": "GB",
    "british": "GB",
    "usa": "US",
    "u.s.": "US",
    "u.s.a.": "US",
    "america": "US",
    "american": "US",
    "united states of america": "US",
    "holland": "NL",
    "dutch": "NL",
    "german": "DE",
    "deutschland": "DE",
    "french": "FR",
    "spanish": "ES",
    "espana": "ES",
    "italian": "IT",
    "italia": "IT",
    "portuguese": "PT",
    "brasil": "BR",
    "brazilian": "BR",
    "mexican": "MX",
    "canadian": "CA",
    "indian": "IN",
    "japanese": "JP",
    "chinese": "CN",
    "korean": "KR",
    "korea": "KR",
    "south korea": "KR",
    "turkey": "TR",
    "turkiye": "TR",
    "czech republic": "CZ",
    "russian": "RU",
    "ukrainian": "UA",
    "south african": "ZA",
    "kenyan": "KE",
    "nigerian": "NG",
    "moroccan": "MA",
    "egyptian": "EG",
    "australian": "AU",
    "kiwi": "NZ",
    "irish": "IE",
    "polish": "PL",
    "swedish": "SE",
    "norwegian": "NO",
    "danish": "DK",
    "finnish": "FI",
    "swiss": "CH",
    "greek": "GR",
    "vietnamese": "VN",
    "thai": "TH",
    "filipino": "PH",
    "indonesian": "ID",
    "argentinian": "AR",
    "argentine": "AR",
    "chilean": "CL",
    "colombian": "CO",
    "peruvian": "PE",
}

_NAME_TO_ISO2: dict[str, str] = {
    name.lower(): code for code, name in ISO2_NAMES.items()
}


# International dialling prefixes for the supported countries above.
# Shared codes (NANP +1, +7, +44 crown dependencies) are labelled explicitly.
ISO2_DIAL_CODES: dict[str, str] = {
    "AR": "+54",
    "AT": "+43",
    "AU": "+61",
    "BD": "+880",
    "BE": "+32",
    "BG": "+359",
    "BO": "+591",
    "BR": "+55",
    "CA": "+1",
    "CH": "+41",
    "CL": "+56",
    "CN": "+86",
    "CO": "+57",
    "CR": "+506",
    "CU": "+53",
    "CZ": "+420",
    "DE": "+49",
    "DK": "+45",
    "DO": "+1",
    "DZ": "+213",
    "EC": "+593",
    "EE": "+372",
    "EG": "+20",
    "ES": "+34",
    "ET": "+251",
    "FI": "+358",
    "FR": "+33",
    "GB": "+44",
    "GE": "+995",
    "GH": "+233",
    "GR": "+30",
    "GT": "+502",
    "HR": "+385",
    "HU": "+36",
    "ID": "+62",
    "IE": "+353",
    "IL": "+972",
    "IN": "+91",
    "IQ": "+964",
    "IR": "+98",
    "IS": "+354",
    "IT": "+39",
    "JM": "+1",
    "JO": "+962",
    "JP": "+81",
    "KE": "+254",
    "KH": "+855",
    "KR": "+82",
    "LK": "+94",
    "LT": "+370",
    "LU": "+352",
    "LV": "+371",
    "MA": "+212",
    "MX": "+52",
    "MY": "+60",
    "NG": "+234",
    "NL": "+31",
    "NO": "+47",
    "NP": "+977",
    "NZ": "+64",
    "PA": "+507",
    "PE": "+51",
    "PH": "+63",
    "PK": "+92",
    "PL": "+48",
    "PT": "+351",
    "PY": "+595",
    "RO": "+40",
    "RS": "+381",
    "RU": "+7",
    "SA": "+966",
    "SE": "+46",
    "SG": "+65",
    "SI": "+386",
    "SK": "+421",
    "SN": "+221",
    "TH": "+66",
    "TN": "+216",
    "TR": "+90",
    "TW": "+886",
    "TZ": "+255",
    "UA": "+380",
    "UG": "+256",
    "US": "+1",
    "UY": "+598",
    "VE": "+58",
    "VN": "+84",
    "ZA": "+27",
}

# Extra widely used destinations that share a code with a country above, plus a
# handful of common travel territories, so the picker stays practical.
EXTRA_DIAL_ENTRIES: list[tuple[str, str, str]] = [
    ("PR", "Puerto Rico", "+1"),
    ("TT", "Trinidad and Tobago", "+1"),
    ("BS", "Bahamas", "+1"),
    ("BB", "Barbados", "+1"),
    ("KZ", "Kazakhstan", "+7"),
    ("JE", "Jersey", "+44"),
    ("GG", "Guernsey", "+44"),
    ("IM", "Isle of Man", "+44"),
    ("GI", "Gibraltar", "+350"),
    ("HK", "Hong Kong", "+852"),
    ("MO", "Macao", "+853"),
    ("AE", "United Arab Emirates", "+971"),
    ("QA", "Qatar", "+974"),
    ("KW", "Kuwait", "+965"),
    ("MT", "Malta", "+356"),
    ("CY", "Cyprus", "+357"),
    ("AL", "Albania", "+355"),
    ("BA", "Bosnia and Herzegovina", "+387"),
    ("MK", "North Macedonia", "+389"),
    ("MD", "Moldova", "+373"),
    ("AM", "Armenia", "+374"),
    ("AZ", "Azerbaijan", "+994"),
    ("BY", "Belarus", "+375"),
    ("LB", "Lebanon", "+961"),
    ("OM", "Oman", "+968"),
    ("BH", "Bahrain", "+973"),
    ("CM", "Cameroon", "+237"),
    ("CI", "Cote d'Ivoire", "+225"),
    ("RW", "Rwanda", "+250"),
    ("ZM", "Zambia", "+260"),
    ("ZW", "Zimbabwe", "+263"),
    ("MZ", "Mozambique", "+258"),
    ("AO", "Angola", "+244"),
    ("SD", "Sudan", "+249"),
    ("LY", "Libya", "+218"),
    ("MM", "Myanmar", "+95"),
    ("LA", "Laos", "+856"),
    ("MN", "Mongolia", "+976"),
    ("UZ", "Uzbekistan", "+998"),
    ("AF", "Afghanistan", "+93"),
    ("SY", "Syria", "+963"),
    ("YE", "Yemen", "+967"),
    ("MV", "Maldives", "+960"),
    ("BT", "Bhutan", "+975"),
    ("BN", "Brunei", "+673"),
    ("FJ", "Fiji", "+679"),
    ("PG", "Papua New Guinea", "+675"),
    ("NI", "Nicaragua", "+505"),
    ("HN", "Honduras", "+504"),
    ("SV", "El Salvador", "+503"),
    ("BZ", "Belize", "+501"),
    ("HT", "Haiti", "+509"),
]

DEFAULT_PHONE_CODE_VALUE = "GB:+44"


def flag_emoji(iso2: str) -> str:
    """Regional-indicator flag for a validated 2-letter code, else empty."""
    code = (iso2 or "").strip().upper()
    if len(code) != 2 or not code.isalpha():
        return ""
    return "".join(chr(0x1F1E6 + ord(letter) - 65) for letter in code)


def resolve_nationality(raw: str) -> tuple[str, str, str]:
    """Return (display_name, iso2, flag_emoji) for any user text.

    Accepts a country name, a common alias/demonym, an ISO-2 or ISO-3 code.
    Unrecognised input is kept as tidy free text with no flag.
    """
    value = (raw or "").strip()
    if not value:
        return "", "", ""
    key = " ".join(value.lower().split())
    iso2 = ""
    if key in _NAME_TO_ISO2:
        iso2 = _NAME_TO_ISO2[key]
    elif key in ALIASES:
        iso2 = ALIASES[key]
    elif len(key) == 3 and key.upper() in ISO3_TO_ISO2:
        iso2 = ISO3_TO_ISO2[key.upper()]
    elif len(key) == 2 and key.upper() in ISO2_NAMES:
        iso2 = key.upper()
    if iso2:
        return ISO2_NAMES[iso2], iso2, flag_emoji(iso2)
    return value[:120].title(), "", ""


def _build_phone_code_options() -> list[tuple[str, str]]:
    """(option_value, option_label) pairs for the calling-code picker.

    The value is `ISO2:+code` so shared codes (+1, +7, +44) stay distinct while
    the dial prefix is always recoverable. Labels read `🇬🇧 United Kingdom +44`.
    """
    entries: list[tuple[str, str, str]] = [
        (code, ISO2_NAMES[code], dial) for code, dial in ISO2_DIAL_CODES.items()
    ] + list(EXTRA_DIAL_ENTRIES)
    options: list[tuple[str, str]] = []
    for iso2, name, dial in sorted(entries, key=lambda item: item[1]):
        flag = flag_emoji(iso2)
        label = f"{flag} {name} {dial}" if flag else f"{name} {dial}"
        options.append((f"{iso2}:{dial}", label))
    return options


PHONE_CODE_OPTIONS: list[tuple[str, str]] = _build_phone_code_options()

PHONE_CODE_VALUES: set[str] = {value for value, _ in PHONE_CODE_OPTIONS}


def dial_prefix(option_value: str) -> str:
    """Extract the `+NN` prefix from an `ISO2:+NN` option value, else ''."""
    raw = (option_value or "").strip()
    if ":" in raw:
        raw = raw.split(":", 1)[1]
    raw = raw.strip()
    if not raw.startswith("+"):
        raw = f"+{raw}" if raw.isdigit() else ""
    digits = raw[1:]
    if not digits.isdigit() or not 1 <= len(digits) <= 4:
        return ""
    return f"+{digits}"


def national_digits(number: str) -> str:
    """Digits only from a typed national number (spaces, dashes ignored)."""
    return "".join(ch for ch in (number or "") if ch.isdigit())


def is_plausible_phone_number(number: str) -> bool:
    """Structural sanity check for a supplied national number."""
    digits = national_digits(number)
    return 4 <= len(digits) <= 14


def compose_phone(option_value: str, number: str) -> str:
    """Normalize a code + national number pair into one stored phone string.

    An empty national number yields an empty string, so the phone column stays
    optional exactly as before.
    """
    digits = national_digits(number)
    if not digits:
        return ""
    prefix = dial_prefix(option_value)
    if not prefix:
        return digits[:24]
    return f"{prefix} {digits}"[:32]
