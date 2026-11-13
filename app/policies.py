"""In-app handbook and policy content for Go and Help.

These screens are app content written for an international adult audience. They
are not legal advice for any particular country, and they do not claim any
certification, audit or legal guarantee. Where local law gives a person rights
that cannot be signed away, those rights always come first.
"""

from typing import TypedDict


class PolicySection(TypedDict):
    heading: str
    icon: str
    paragraphs: list[str]


class PolicyDocument(TypedDict):
    key: str
    title: str
    subtitle: str
    icon: str
    updated: str
    notice: str
    sections: list[PolicySection]


EFFECTIVE_DATE = "Updated and effective 1 June 2024"

HOW_TO_USE: PolicyDocument = {
    "key": "howto",
    "title": "How to use Go and Help",
    "subtitle": "A short handbook for travellers, locals and anyone in between.",
    "icon": "compass",
    "updated": EFFECTIVE_DATE,
    "notice": (
        "Go and Help connects people. It does not employ, supervise, train or "
        "vet anyone. Every meeting, journey and task is arranged between "
        "adults who decide for themselves — so read this page before you "
        "arrange to meet anybody."
    ),
    "sections": [
        {
            "heading": "The map, and the two ways to read it",
            "icon": "map",
            "paragraphs": [
                "The map fills the screen because it is the heart of the app. "
                "Two modes sit side by side. Give shows people who are asking "
                "for help: each pin is an open request you could take on. Get "
                "shows members who have said they are willing to offer help, "
                "so you can read a profile and then post a request they can "
                "accept.",
                "Pinch to zoom, drag with one finger to pan, and use two "
                "fingers to rotate. Whenever the map is turned away from "
                "north, a small compass appears near the map and list toggle. "
                "Tap it once and the map swings back to north.",
                "Switch to list view whenever the map feels crowded. The list "
                "always shows every single request separately, even when the "
                "map has grouped several requests from the same person behind "
                "one profile marker. Tap a grouped marker to see that "
                "person's requests one by one.",
            ],
        },
        {
            "heading": "Choosing what you share about where you are",
            "icon": "map-pin",
            "paragraphs": [
                "Set my location offers three positions and nothing in "
                "between. Off keeps you off every map and out of people "
                "search: your saved coordinates stay in your account but no "
                "coordinate is sent anywhere. Approximate keeps your exact "
                "point private and publishes only a land-safe point between "
                "500m and 1km away, seen by all users. Live publishes your "
                "accurate position to all users, refreshed whenever you press "
                "Refresh my position.",
                "Please be clear-eyed about this: in Live mode all users can "
                "see your accurate point on the map, not a vague circle. Do "
                "not use Live at your home address if you would not want a "
                "stranger standing outside it. Approximate, or a nearby "
                "square, market or café, is usually a better choice.",
                "Live location depends on your browser and your device. Most "
                "browsers only offer it on a secure https:// address, and all "
                "of them ask your permission first. If you decline, or if the "
                "signal is poor, the app will tell you and nothing is saved. "
                "People who are not signed in never receive member "
                "coordinates of any kind.",
            ],
        },
        {
            "heading": "Posting a request for help",
            "icon": "notebook-pen",
            "paragraphs": [
                "Write plainly. Say what the task is, roughly how long it "
                "takes, what tools or skills matter, when you are free, and "
                "what you are offering in return — a meal, a bed for the "
                "night, a guided walk, a lesson, or simple thanks. Photographs "
                "help enormously; a picture of the fence, the wall or the "
                "kitchen saves a dozen messages.",
                "Free membership keeps a small number of requests open at "
                "once, and each one expires after a while so the map stays "
                "honest. Premium membership raises that to ten simultaneous "
                "requests. Close or complete a request as soon as it is done "
                "so nobody travels for nothing.",
                "Never advertise anything unlawful, unsafe, sexual, or "
                "anything that asks a person to work in conditions you would "
                "refuse yourself. Do not ask for money transfers, deposits, "
                "documents or account details.",
            ],
        },
        {
            "heading": "Accepting a request, and meeting safely",
            "icon": "hand-helping",
            "paragraphs": [
                "When you accept a request, a conversation opens with the "
                "person who posted it. Agree the details there: exact meeting "
                "point, time, what to bring, and what the reward is. Put it in "
                "writing inside the app so you both have the same version.",
                "Meet in a public place first. Tell somebody you trust where "
                "you are going and when you expect to be back. Keep your "
                "phone charged. Do not hand over your passport, keys or bank "
                "details to anybody. If a task turns out to be different from "
                "the description, or if anything feels wrong, stop and leave — "
                "you are never obliged to continue.",
                "Think about insurance, permits and local rules before doing "
                "anything physical, electrical, structural, medical or "
                "childcare-related. Some tasks require a licensed person in "
                "some countries, and no post on this app changes that.",
            ],
        },
        {
            "heading": "Messages, contacts and the forum",
            "icon": "mail",
            "paragraphs": [
                "Job conversations belong to a specific request. Contact "
                "requests are separate: once two people accept each other, a "
                "direct message thread stays open between them.",
                "The community forum is the long-form room — questions, "
                "stories, route advice and hard-won practical knowledge. "
                "Reading it is free. Writing topics and comments is part of "
                "premium membership.",
                "Keep conversations inside the app for as long as you can. It "
                "keeps a record, and it means you are not handing out a "
                "personal phone number or email to somebody you have not met.",
            ],
        },
        {
            "heading": "Membership",
            "icon": "ticket",
            "paragraphs": [
                "Offering and giving help is always free. Membership is a "
                "contribution that keeps the project running, and it opens the "
                "forum, ten simultaneous requests, priority placement, "
                "advanced search options and the extra display choices.",
                "There are two options — a monthly Ticket to ride and a yearly "
                "Annual pass — and they unlock exactly the same benefits. "
                "Payment is handled by Stripe; the app never sees or stores "
                "your card details. You can cancel at any time from the "
                "billing portal on your profile.",
            ],
        },
        {
            "heading": "Reviews",
            "icon": "star",
            "paragraphs": [
                "After a completed task both people can review each other "
                "across four scores: Timeliness, Work ethic, Skill and "
                "Friendliness, for both posters and helpers. The four "
                "are averaged into one combined star rating shown on the "
                "profile.",
                "Write reviews the way you would want to read one: specific, "
                "fair and free of personal details. A review is your genuine "
                "experience, not a weapon, and not a favour.",
            ],
        },
        {
            "heading": "Reporting and safety",
            "icon": "shield-alert",
            "paragraphs": [
                "If somebody behaves unsafely, dishonestly or abusively, stop "
                "the conversation and report them from the profile or the "
                "conversation. Keep the messages — they are the record.",
                "In an emergency, contact your local emergency services "
                "first. Go and Help is not an emergency service and cannot "
                "intervene at the scene. We can review accounts and remove "
                "content or access, but we cannot undo something that has "
                "already happened.",
            ],
        },
    ],
}

PRIVACY_POLICY: PolicyDocument = {
    "key": "privacy",
    "title": "Privacy and cookies policy",
    "subtitle": "What we collect, why, and the choices that stay yours.",
    "icon": "shield-check",
    "updated": EFFECTIVE_DATE,
    "notice": (
        "Location sharing is off until you switch it on. If you choose Fixed "
        "place or Live location, other signed-in members can see your exact "
        "coordinates on member maps. You can return to Hidden at any moment."
    ),
    "sections": [
        {
            "heading": "What we collect",
            "icon": "database",
            "paragraphs": [
                "Account information: your email address, the name parts you "
                "give at registration, an optional phone number and date of "
                "birth, a password stored only as a cryptographic hash, and "
                "whether your email has been confirmed.",
                "Profile information: your handle, headline, biography, "
                "nationality, languages, skills, availability note, chosen "
                "help categories, photo, home and current city, and your "
                "location mode with its saved latitude and longitude.",
                "Activity: help requests and their photos, applications and "
                "acceptances, message threads, contact requests, forum topics "
                "and comments, completed tasks and reviews, and membership "
                "state mirrored from our payment processor.",
                "Technical information: the timestamps of your visits, an IP "
                "address and user-agent string recorded when verification "
                "emails are requested (used to limit abuse), and the ordinary "
                "server logs any web application produces.",
            ],
        },
        {
            "heading": "Why we use it",
            "icon": "target",
            "paragraphs": [
                "To run the service you asked for: signing you in, showing "
                "requests and people, delivering messages, keeping the forum, "
                "recording reviews and applying your membership.",
                "To keep the community safer: confirming email addresses, "
                "limiting repeated sending, spotting abuse, and acting on "
                "reports.",
                "To take payment for membership through our payment processor, "
                "and to know which benefits your account should have.",
                "We do not sell your personal information, and we do not use "
                "your messages to build advertising profiles.",
            ],
        },
        {
            "heading": "Geolocation: off or approximate",
            "icon": "map-pin",
            "paragraphs": [
                "Off is the default for every account. With Set my location "
                "Off your saved coordinates are not shown to anyone, you do "
                "not appear on maps or in people search, and no coordinate is "
                "transmitted.",
                "Approximate reads your position from your browser once, only "
                "when you tap the control, and stores that point privately "
                "along with the time it was taken. There is no background "
                "tracking and no continuous watching of your device. Your "
                "browser will ask your permission before it shares anything, "
                "and most browsers require a secure https:// connection.",
                "We never publish your stored point: we derive a stable, "
                "land-safe point between 500m and 1km away and publish only "
                "that. Choosing Off again stops the sharing immediately "
                "without deleting the coordinates you saved, so you can turn "
                "it back on later.",
                "Help requests work the same way: publicly they are shown as "
                "an approximate area 0.5–1 km from the real spot, and the "
                "address you type is never published. The exact meeting place "
                "is shared only with the helper you confirm.",
                "Location sharing is a choice you make and can withdraw. "
                "Please think about who might see the point you choose before "
                "you switch it on.",
            ],
        },
        {
            "heading": "How long we keep it",
            "icon": "clock",
            "paragraphs": [
                "Account, profile and activity records are kept while your "
                "account exists, because they are what the service shows.",
                "Help requests expire from public view after their lifetime "
                "ends, and email verification links expire within an hour of "
                "being issued.",
                "When you ask us to close your account we remove or "
                "anonymise your personal records, except where we must keep "
                "something to meet a legal obligation, resolve a dispute or "
                "prevent abuse. Content other people have quoted or replied "
                "to may remain visible in their own posts.",
            ],
        },
        {
            "heading": "Processors and international transfers",
            "icon": "globe",
            "paragraphs": [
                "We use a small number of service providers to operate the "
                "app: hosting and managed database infrastructure, Stripe for "
                "payments, and Resend for transactional email such as "
                "verification links. Map tiles are served by OpenFreeMap, so "
                "the map area you look at is requested from that tile service "
                "by your browser. Profile placeholder images are generated by "
                "an avatar service. Each provider receives only what it needs "
                "to do its job.",
                "Go and Help is used by people all over the world, so your "
                "information may be stored or processed in a country other "
                "than your own, including countries whose data-protection "
                "rules differ from those where you live. We ask our providers "
                "for appropriate contractual protections, but we cannot "
                "promise that any single country's standards apply "
                "everywhere.",
            ],
        },
        {
            "heading": "Security, and its honest limits",
            "icon": "lock",
            "paragraphs": [
                "Passwords are stored only as hashes. Verification links are "
                "stored only as SHA-256 digests, so a copy of the database "
                "cannot be replayed as a login. Traffic to the app is served "
                "over encrypted connections and access to production data is "
                "restricted.",
                "No online service can promise perfect security, and we do "
                "not. We hold no certification and make no guarantee against "
                "every possible attack. Use a strong, unique password, keep "
                "your email account secure, and tell us promptly if you think "
                "your account has been reached by somebody else.",
            ],
        },
        {
            "heading": "Cookies and local storage",
            "icon": "cookie",
            "paragraphs": [
                "We use a session cookie or an equivalent token in your "
                "browser's local storage to keep you signed in and to keep "
                "your session consistent as you move between screens. Without "
                "it the app cannot know who you are.",
                "We may store small preferences locally — the screen you were "
                "last on, for instance, or your display choices — so the app "
                "feels the same when you return.",
                "We do not run third-party advertising or cross-site tracking "
                "cookies. Blocking or clearing cookies and local storage is "
                "always possible in your browser settings; if you do, you "
                "will be signed out and some features will not work.",
            ],
        },
        {
            "heading": "Your controls and rights",
            "icon": "settings",
            "paragraphs": [
                "You can edit your profile, change or remove your photo, "
                "change your location mode, delete your own posts, comments "
                "and contact links, and cancel your membership at any time.",
                "Depending on where you live you may also have the right to "
                "ask for a copy of the personal information we hold, to have "
                "it corrected, to have it deleted, to restrict or object to "
                "some processing, and to complain to your local data "
                "protection authority. We will act on a request in a "
                "reasonable time once we can confirm it comes from you.",
            ],
        },
        {
            "heading": "Adults only",
            "icon": "user-round-check",
            "paragraphs": [
                "Go and Help is for people aged 16 and over: you must be at least 16 years old "
                "to create an account. We do not knowingly collect "
                "information from children. If you believe a minor has an "
                "account, tell us and we will remove it.",
            ],
        },
        {
            "heading": "Contacting us",
            "icon": "mail",
            "paragraphs": [
                "For any privacy question, a data request, or a report about "
                "another account, write to us from the email address on your "
                "account using the support address shown on the Go and Help "
                "website, and describe clearly what you are asking for. "
                "Please do not send passwords, card numbers or identity "
                "documents in an email.",
            ],
        },
    ],
}

USER_AGREEMENT: PolicyDocument = {
    "key": "agreement",
    "title": "User agreement",
    "subtitle": "The terms you accept by using Go and Help.",
    "icon": "scroll-text",
    "updated": EFFECTIVE_DATE,
    "notice": (
        "Go and Help is a platform and intermediary only. We do not verify, "
        "vet, supervise, employ or guarantee any user, task, reward or "
        "meeting. Everything you arrange here, you arrange at your own risk "
        "with another independent adult."
    ),
    "sections": [
        {
            "heading": "What Go and Help is — and is not",
            "icon": "info",
            "paragraphs": [
                "Go and Help is a place where adults publish requests for "
                "practical help and find each other. We provide the listing, "
                "map, messaging and forum tools. That is the whole of our "
                "role.",
                "We are not a party to any arrangement between users. We are "
                "not an employer, employment agency, staffing agency, "
                "contractor, insurer, escrow service, background-check "
                "provider, travel agent or supervisor. We do not check "
                "identity documents, qualifications, licences, insurance, "
                "criminal records, immigration status or tax status, and we do "
                "not confirm that anything written in a post or a profile is "
                "true.",
            ],
        },
        {
            "heading": "Eligibility",
            "icon": "user-round-check",
            "paragraphs": [
                "You must be at least 16 years old and legally able to enter "
                "into this agreement. One account per person. You must not use "
                "Go and Help if a court, a sanctions regime or applicable law "
                "prohibits it, or if we have previously removed your access.",
            ],
        },
        {
            "heading": "Your account",
            "icon": "shield",
            "paragraphs": [
                "Keep your password confidential and your email address "
                "current. Everything done through your account is treated as "
                "done by you. Tell us promptly if you suspect unauthorised "
                "access.",
                "Give accurate information about yourself. Do not impersonate "
                "anybody, do not create an account for somebody else, and do "
                "not use another person's photograph or identity.",
            ],
        },
        {
            "heading": "Your content",
            "icon": "notebook-pen",
            "paragraphs": [
                "You keep ownership of what you write and upload. By posting, "
                "you grant Go and Help a worldwide, non-exclusive, "
                "royalty-free licence to host, store, reproduce, adapt for "
                "display and show that content within the service so the app "
                "can function. You can delete your content at any time; "
                "copies already quoted or replied to by others may remain in "
                "their posts.",
                "You confirm you have the right to post what you post, "
                "including any photograph, and that it does not infringe "
                "anyone's rights or break any law. We may remove content that "
                "breaches this agreement, but we do not pre-screen or approve "
                "content and we are not responsible for what users publish.",
            ],
        },
        {
            "heading": "Arrangements between users are your own",
            "icon": "handshake",
            "paragraphs": [
                "Any agreement to help, to be helped, to travel, to meet, to "
                "stay somewhere, or to give or receive a reward is made "
                "directly between the users involved. It is a private, "
                "independent arrangement. Go and Help is not a party to it, "
                "takes no commission on it, and does not enforce it.",
                "You are responsible for deciding whether an arrangement is "
                "safe, lawful and suitable for you, and for any permit, "
                "licence, insurance, health-and-safety obligation, tax or "
                "reporting duty that applies to you. Some work requires a "
                "qualified or licensed person in some countries; nothing here "
                "changes that.",
                "Rewards described on this app are voluntary gestures of "
                "thanks between people. Nothing on Go and Help creates an "
                "employment relationship, a partnership, an agency, a "
                "franchise or a joint venture between you and us, or between "
                "you and another user.",
            ],
        },
        {
            "heading": "Payments and membership",
            "icon": "credit-card",
            "paragraphs": [
                "Using Go and Help to offer and give help is free. Membership "
                "is optional and is charged by our payment processor, Stripe. "
                "Prices are shown before you confirm. A monthly membership "
                "renews monthly and a yearly membership renews yearly until "
                "you cancel.",
                "You can cancel at any time from the billing portal; your "
                "benefits then run to the end of the period you already paid "
                "for. Except where local law requires otherwise, part-periods "
                "are not refunded. Any statutory right of withdrawal or "
                "cancellation you have where you live continues to apply.",
                "We never handle or store your card details. If a payment "
                "fails or is reversed, premium benefits may pause until it is "
                "resolved.",
            ],
        },
        {
            "heading": "Safety is in your hands",
            "icon": "shield-alert",
            "paragraphs": [
                "Meet in public first. Tell somebody where you are going. Do "
                "not travel to a private address you cannot verify. Do not "
                "send money, deposits, documents or account details to another "
                "user. Do not carry out work you are not competent to do "
                "safely, and stop immediately if a situation changes or feels "
                "wrong.",
                "Consider your own insurance before doing physical, "
                "structural, electrical, mechanical, medical, animal or "
                "childcare work. Consider whether the person you are meeting "
                "has any. In an emergency, call your local emergency services "
                "— we cannot help at the scene.",
            ],
        },
        {
            "heading": "Prohibited conduct",
            "icon": "ban",
            "paragraphs": [
                "Do not use Go and Help for anything unlawful, or to arrange "
                "anything unlawful. Specifically prohibited: harassment, "
                "threats, hate speech, discrimination, stalking, sexual "
                "content or sexual services, exploitation or trafficking of "
                "any kind, child endangerment, coerced or unpaid labour "
                "presented as help, weapons, drugs, smuggling, fraud, money "
                "laundering, phishing, spam, scraping, advertising unrelated "
                "commercial services, or interfering with the security or "
                "operation of the app.",
                "Do not publish another person's private information without "
                "consent, and do not use the map or search to follow, watch or "
                "pressure anybody.",
            ],
        },
        {
            "heading": "Suspension and removal",
            "icon": "user-round-x",
            "paragraphs": [
                "We may remove content, limit features, suspend or close an "
                "account if we reasonably believe this agreement has been "
                "broken, if the law requires it, or if there is a risk to "
                "other people or to the service. Where it is reasonable and "
                "lawful to do so we will tell you why and you may reply.",
                "You may stop using Go and Help and close your account at any "
                "time.",
            ],
        },
        {
            "heading": "Intellectual property",
            "icon": "copyright",
            "paragraphs": [
                "The Go and Help name, logo, design and software belong to us "
                "or our licensors and are protected by intellectual property "
                "law. You may use them only as the app itself allows. Map data "
                "and open-source components remain the property of their own "
                "authors and are used under their own licences.",
                "If you believe content on Go and Help infringes your rights, "
                "tell us what and where it is and we will review it.",
            ],
        },
        {
            "heading": "Service provided as it is",
            "icon": "triangle-alert",
            "paragraphs": [
                "Go and Help is provided on an 'as is' and 'as available' "
                "basis. To the maximum extent the law where you live permits, "
                "we make no warranty that the app will be uninterrupted, "
                "error-free, secure against every attack, or fit for a "
                "particular purpose; that any user is honest, skilled, "
                "insured, licensed or safe; that any request, reward or "
                "profile is accurate; or that any arrangement will be kept.",
                "Locations, distances, availability and ratings are shown as "
                "supplied by users and by third-party map data. They may be "
                "wrong or out of date.",
            ],
        },
        {
            "heading": "Limitation of liability",
            "icon": "scale",
            "paragraphs": [
                "To the maximum extent permitted by the law that applies to "
                "you, Go and Help, its owners, staff and suppliers are not "
                "responsible or liable for any loss or damage arising out of "
                "or connected with other users, their conduct or content, any "
                "meeting or communication between users, any journey or "
                "travel, any task carried out or refused, any reward given or "
                "withheld, or the acts of any third party. That expressly "
                "includes personal injury, illness or death; loss, theft or "
                "damage to property; financial or economic loss; lost profit, "
                "opportunity or data; and distress or other emotional harm.",
                "To the same extent, we are not liable for indirect, "
                "incidental, special, consequential or punitive damages. Where "
                "liability cannot lawfully be excluded but can be limited, our "
                "total liability to you is limited to the greater of the "
                "membership fees you paid us in the twelve months before the "
                "claim, or fifty United States dollars.",
                "Nothing in this agreement excludes or limits liability that "
                "the law does not allow to be excluded or limited — including, "
                "in many countries, liability for death or personal injury "
                "caused by negligence, for fraud or fraudulent "
                "misrepresentation, and mandatory consumer rights. If a court "
                "finds part of this section unenforceable, the rest continues "
                "to apply and your mandatory local rights are unaffected.",
            ],
        },
        {
            "heading": "Indemnity",
            "icon": "file-check",
            "paragraphs": [
                "You agree to indemnify and hold Go and Help harmless from "
                "claims, demands, losses and reasonable costs brought by a "
                "third party and arising from your content, your conduct, your "
                "arrangements with other users, or your breach of this "
                "agreement — except to the extent the law where you live does "
                "not allow this, or the claim results from our own wrongdoing.",
            ],
        },
        {
            "heading": "Disputes and your local rights",
            "icon": "gavel",
            "paragraphs": [
                "Please contact us first: most problems are solved by an "
                "email. If we cannot resolve it, we will try in good faith to "
                "agree a practical way forward before anybody goes to court.",
                "Disputes between users are between those users. We may "
                "provide records where the law requires us to, but we do not "
                "arbitrate, judge or compensate.",
                "This agreement is governed by the law stated on the Go and "
                "Help website, but if you are a consumer, nothing here takes "
                "away the protection of the mandatory consumer law of the "
                "country where you habitually live, or your right to bring a "
                "claim in your local courts. Where a term of this agreement "
                "conflicts with such a mandatory rule, the mandatory rule "
                "wins.",
            ],
        },
        {
            "heading": "Changes to this agreement",
            "icon": "history",
            "paragraphs": [
                "We may update this agreement as the app changes or the law "
                "requires. When a change matters, we will show the new "
                "effective date here and, for significant changes, tell you in "
                "the app. Continuing to use Go and Help after a change means "
                "you accept the updated terms; if you do not accept them, "
                "please close your account.",
                "These screens are app content for an international audience. "
                "They are not legal advice about any particular country, and "
                "they are not a substitute for advice from a qualified lawyer "
                "where you live.",
            ],
        },
    ],
}

SAFETY_PRECAUTIONS: PolicyDocument = {
    "key": "safety",
    "title": "Safety and precautions",
    "subtitle": (
        "How to share your location carefully, meet strangers sensibly and "
        "keep your data, your money and your body out of harm's way."
    ),
    "icon": "shield-alert",
    "updated": EFFECTIVE_DATE,
    "notice": (
        "Go and Help is an introduction tool, nothing more. We do not "
        "supervise, chaperone or attend any meeting, we do not check anyone's "
        "identity documents, criminal record, insurance, driving licence or "
        "trade qualifications, and star ratings are opinions from other "
        "members \u2014 never a guarantee of safety, honesty or competence. "
        "Your own judgement is the only real protection you have."
    ),
    "sections": [
        {
            "heading": "Your exact location is the most sensitive thing you can share",
            "icon": "map-pin",
            "paragraphs": [
                "Live publishes your accurate latitude and longitude to all "
                "users — not a vague circle, not a neighbourhood. If those "
                "coordinates sit "
                "on your bed, your hostel dorm, your parked van or your "
                "front door, you have told strangers where you sleep. Think "
                "about that before you switch anything on.",
                "Choose a safer public fixed point instead: a main square, a "
                "transport hub, a busy caf\u00e9 terrace, a library, a market "
                "gate. Somewhere a few minutes from where you actually stay, "
                "with people around it at the hours you would meet. A fixed "
                "point like that says 'I am roughly here and happy to meet "
                "here' without handing over your address.",
                "Use Live location only while you genuinely need it \u2014 for "
                "instance during a job you have already agreed, when a helper "
                "is walking towards you \u2014 and switch back to Hidden or a "
                "fixed public point the moment it is over. Live sharing that "
                "you forget about is the single easiest way to be followed "
                "home.",
                "Hidden removes you from member maps and member search "
                "entirely. You can still write, read, offer help and reply to "
                "messages. If you are travelling alone, staying somewhere "
                "isolated, or simply unsure, Hidden is a perfectly normal way "
                "to use Go and Help.",
                "People who are not signed in never receive member "
                "coordinates, and your phone number is never shared with "
                "other users at all. Even so, treat every coordinate you "
                "publish as permanently public: once someone has seen it, "
                "you cannot take it back.",
            ],
        },
        {
            "heading": "Meeting someone for the first time",
            "icon": "users-round",
            "paragraphs": [
                "Meet in a public place, in daylight, where other people can "
                "see you: a square, a station, a caf\u00e9, the entrance of a "
                "shop. Do not go to a private home, a locked yard, a boat, a "
                "basement, a building site or a remote road for a first "
                "meeting, however reasonable the request sounds.",
                "Tell a trusted person \u2014 a friend, a relative, your hostel "
                "reception \u2014 who you are meeting, what the job is, where, "
                "and when you expect to be back. Send them the other "
                "person's profile handle and a screenshot of your "
                "conversation. Agree that you will message them when you are "
                "done.",
                "Arrange your own transport, both directions, and keep enough "
                "money or battery to leave immediately. Never depend on the "
                "other person for your ride home, and never let your only way "
                "back be their car, their boat or their goodwill. Know your "
                "exit before you arrive.",
                "Keep the conversation inside Go and Help until you are "
                "comfortable. Anyone who rushes you off the app, pressures "
                "you to come alone, changes the meeting point at the last "
                "minute to somewhere quieter, or refuses to be seen in "
                "public, has told you something important. Stop.",
                "You may cancel, leave or say no at any moment, without a "
                "reason and without apologising. Feeling uneasy is reason "
                "enough. A genuine neighbour will understand; someone who "
                "punishes you for it was never safe.",
            ],
        },
        {
            "heading": "Read reviews \u2014 and read them sceptically",
            "icon": "star",
            "paragraphs": [
                "Before you agree to anything, open the other person's "
                "profile and read the reviews they have received, in both "
                "directions: as a helper and as someone who asked for help. "
                "Look at what people actually wrote, not only the number of "
                "stars.",
                "Walk away from poor reviews. Repeated mentions of pushiness, "
                "lateness, unwanted advances, unpaid or unmet promises, "
                "drinking, aggression or unsafe conditions are exactly the "
                "warnings they appear to be. One bad review can be a "
                "misunderstanding; a pattern is a pattern.",
                "Be equally careful with suspicious praise: a brand-new "
                "account with several glowing identical reviews, reviews "
                "written in the same voice, or a profile whose story keeps "
                "changing. Ratings can be gamed, and an empty profile simply "
                "tells you nothing at all.",
                "The same applies to places. If members report that a "
                "particular address, site, bar or workshop felt unsafe, "
                "believe them and choose somewhere else \u2014 including for "
                "jobs you would otherwise happily do.",
                "Ratings are opinions collected after the fact. They are not "
                "a background check, an insurance policy or a promise from Go "
                "and Help about anybody's behaviour.",
            ],
        },
        {
            "heading": "Work you should refuse",
            "icon": "triangle-alert",
            "paragraphs": [
                "Do not enter unsafe places: unfinished or derelict "
                "buildings, roofs, scaffolding, ladders you did not inspect, "
                "trenches, tanks, wells, confined or airless spaces, "
                "flood water, or anywhere you would need equipment and "
                "training you do not have.",
                "Do not take on work you are not qualified, licensed or "
                "insured to do. Electrical work, gas, plumbing into mains, "
                "structural repairs, tree felling, driving other people's "
                "vehicles, childcare, animal handling, care of vulnerable "
                "adults, medical or medicine-related help and anything "
                "involving chemicals or power tools all carry real legal and "
                "physical risk. Being helpful is not a qualification.",
                "Refuse anything illegal, dishonest or simply strange: moving "
                "unknown packages, carrying items across a border, handling "
                "someone else's cash, cards, documents or crypto, collecting "
                "or forwarding money, or 'small favours' that are never "
                "explained properly.",
                "Ask plainly what the job involves, where, how long, who else "
                "will be present and what equipment exists. Vague answers are "
                "an answer. If the reality on arrival is not what was agreed, "
                "leave \u2014 you owe nobody an unsafe afternoon.",
                "Stop if conditions change: weather, darkness, alcohol or "
                "drugs, extra people arriving, or a task that quietly grows "
                "into something bigger and more dangerous than the request.",
            ],
        },
        {
            "heading": "Emergencies",
            "icon": "siren",
            "paragraphs": [
                "In an emergency, contact your local emergency services "
                "first \u2014 not us. Go and Help has no emergency line, no "
                "security team and no way to reach anyone on your behalf. "
                "Police, ambulance and fire services are the only people who "
                "can come to you.",
                "Learn the emergency number where you are before you need it. "
                "112 works across the European Union and in many other "
                "countries; 999, 911, 000 and other numbers are used "
                "elsewhere. Write it down somewhere that does not need a "
                "charged phone or a data connection.",
                "Keep your phone charged, keep some offline map or address "
                "notes, know the name and street of where you are staying, "
                "and keep a little emergency cash separate from your wallet.",
                "If you have been hurt, threatened or robbed, report it to "
                "the local authorities and keep any reference number. Then "
                "report the member to us as well, so we can act on the "
                "account.",
            ],
        },
        {
            "heading": "Harassment, reporting and blocking",
            "icon": "shield-x",
            "paragraphs": [
                "Nobody on Go and Help has to tolerate sexual advances, "
                "racism, threats, insults, repeated unwanted contact, "
                "pressure to drink, pressure to stay, or requests for money, "
                "nudity or personal documents. There is no version of a "
                "help request that includes any of that.",
                "Stop replying, keep the evidence, and report the member from "
                "their profile or the conversation. Screenshots, dates and "
                "the exact words help us far more than a general complaint. "
                "Do not delete the thread before you report it.",
                "Blocking removes the person from your conversations and "
                "stops them contacting you again. Reporting also tells us, so "
                "we can review the account, limit it, or remove it from Go "
                "and Help entirely. Do both when someone frightens you.",
                "Please report bad experiences even when nothing terrible "
                "happened \u2014 the near-misses are exactly what protects the "
                "next traveller. And write honest reviews: your calm, "
                "factual account is worth more than a furious one.",
            ],
        },
        {
            "heading": "Protect your phone, your address, your documents and your money",
            "icon": "lock",
            "paragraphs": [
                "Never hand over your phone unlocked, never share your "
                "passwords or verification codes, and never let someone "
                "'just check something' on your accounts. Anyone asking for a "
                "code sent to your phone is trying to take something from "
                "you.",
                "Keep your home address, hostel room number, workplace, "
                "passport, visa, ID card and travel documents to yourself. "
                "Do not photograph them for anyone, do not leave them as "
                "security or deposit, and do not let anyone hold them while "
                "you work.",
                "Your phone number is never shared with other users. It is "
                "kept for your own account only, and no member or guest can "
                "see it. If you choose to give somebody your number, do it "
                "yourself and only when you are comfortable.",
                "Go and Help never asks for money for a job, and never sends "
                "a stranger to collect payment. Do not send deposits, gift "
                "cards, crypto or bank transfers to members, do not accept "
                "overpayment-and-refund arrangements, and be very wary of "
                "anyone moving a friendly conversation towards your finances "
                "or a romance.",
                "Payments for membership are handled by Stripe. We never ask "
                "for your full card number, PIN or banking password in a "
                "message, and neither should anyone claiming to work for us.",
            ],
        },
        {
            "heading": "Borders, local law and local custom",
            "icon": "globe",
            "paragraphs": [
                "Go and Help is used all over the world, and what is normal "
                "in one country is illegal in the next. Working for payment "
                "or reward \u2014 including food, a bed or a tour \u2014 can breach "
                "visa or immigration rules even when no money changes hands. "
                "Check your own visa conditions; they are your "
                "responsibility, not ours.",
                "Take local law seriously: tax and reporting rules, insurance "
                "requirements, licences for trades and driving, alcohol and "
                "drug law, photography restrictions, protest and curfew "
                "rules, and rules about who may work at all. Ignorance is "
                "rarely a defence abroad.",
                "Be aware of local custom and risk too: neighbourhoods that "
                "are unwise after dark, dress or behaviour that draws "
                "unwanted attention, water and food safety, animals, and "
                "seasonal dangers such as heat, storms or flooding.",
                "Crossing a border for a job deserves particular caution: "
                "never carry anything for anyone, keep your documents on your "
                "person, and be sure you can return.",
            ],
        },
        {
            "heading": "What Go and Help does not do",
            "icon": "info",
            "paragraphs": [
                "We do not supervise, attend or monitor meetings. There is no "
                "escort, no chaperone, no observer and no insurance behind "
                "your arrangement. Adults arrange it, adults carry it out, "
                "adults carry the risk.",
                "A verified badge on Go and Help means only that a member "
                "confirmed their email address. It is not an identity check, "
                "a criminal record check, a qualification check or a "
                "character reference of any kind.",
                "Star ratings, kindness points and helpful reviews describe "
                "what happened before. They cannot predict what someone will "
                "do next, and they are not a promise from us that a meeting "
                "will be safe.",
                "If something feels wrong \u2014 in a message, at a meeting "
                "point, on arrival \u2014 trust that feeling, leave, and tell us. "
                "No job, favour, meal or bed is worth your safety.",
            ],
        },
    ],
}

CREDITS: PolicyDocument = {
    "key": "credits",
    "title": "Credits",
    "subtitle": (
        "The open maps and open-source projects that draw every Go and Help "
        "map."
    ),
    "icon": "heart-handshake",
    "updated": EFFECTIVE_DATE,
    "notice": (
        "Go and Help is drawn on open data made by volunteers all over the "
        "world. These credits are part of the licence terms we happily keep."
    ),
    "sections": [
        {
            "heading": "Maps and map data",
            "icon": "map",
            "paragraphs": [
                "Map tiles by OpenFreeMap, data \u00a9 OpenStreetMap "
                "contributors, under the Open Database License (ODbL).",
                "Map data is made available under the Open Database License "
                "(ODbL) by OpenStreetMap.",
                "OpenFreeMap builds upon several fantastic open-source "
                "projects including tools like: MapLibre, Planetiler and "
                "OpenMapTiles.",
            ],
        },
    ],
}

# The standalone Safety and precautions screen is retired as a visible button:
# its full notice and every section now live inside How to use Go and Help, so
# nothing substantive is lost. The `safety` key stays registered below purely so
# any older in-app link still opens a valid document.
HOW_TO_USE["sections"] = (
    list(HOW_TO_USE["sections"])
    + [
        {
            "heading": "Safety and precautions — read this before you meet anyone",
            "icon": "shield-alert",
            "paragraphs": [SAFETY_PRECAUTIONS["notice"]],
        },
    ]
    + list(SAFETY_PRECAUTIONS["sections"])
)

POLICY_DOCUMENTS: dict[str, PolicyDocument] = {
    HOW_TO_USE["key"]: HOW_TO_USE,
    PRIVACY_POLICY["key"]: PRIVACY_POLICY,
    USER_AGREEMENT["key"]: USER_AGREEMENT,
    # Compatibility only — no visible button points here any more.
    SAFETY_PRECAUTIONS["key"]: SAFETY_PRECAUTIONS,
    CREDITS["key"]: CREDITS,
}

POLICY_LINKS: list[dict[str, str]] = [
    {"key": "howto", "label": "How to use Go and Help", "icon": "compass"},
    {
        "key": "privacy",
        "label": "Privacy and cookies policy",
        "icon": "shield-check",
    },
    {"key": "agreement", "label": "User agreement", "icon": "scroll-text"},
    {"key": "credits", "label": "Credits", "icon": "heart-handshake"},
]
