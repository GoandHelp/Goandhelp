import reflex as rx

from collections import Counter
from string import Formatter

from app.models import LANGUAGE_OPTIONS
from app.interface_catalog_profile_membership_global import (
    PROFILE_MEMBERSHIP_GLOBAL_ROWS,
)
from app.interface_catalog_profile_membership_asian import (
    PROFILE_MEMBERSHIP_ASIAN_ROWS,
)

PROFILE_MEMBERSHIP_KEYS: tuple[str, ...] = (
    "Membership information",
    "Unlock more as a Premium Member",
    "Your tier",
    "Premium members",
    "Free members",
    "Always free",
    "Premium is active on this account, including the Metrics Information section on this page.",
    "See premium membership",
    "See premium membership options",
    "$5 monthly",
    "$49 annually",
    "More information",
    "How to use Go and Help",
    "Privacy and cookies policy",
    "User agreement",
    "Credits",
    "Back to your profile",
    "Section {count}",
    "This screen is part of the Go and Help app. It is written for adults everywhere and is not legal advice for any particular country.",
    "Unlimited community forum topics and comments",
    "Unlimited help offers",
    "Request multiple helpers for events",
    "Priority view help requests",
    "Metrics for increased responses",
    "Advanced Search Options",
    "10 simultaneous help requests",
    "Custom themes and modes",
    "1 help offer a day",
    "2 simultaneous help requests",
    "One-month post visibility",
    "Offer and give help anywhere, always free",
    "Read the community forum",
    "1 forum topic per UTC calendar month",
    "10 forum comments per UTC calendar month across all discussions",
    "Basic search by job category and reward",
)

PROFILE_MEMBERSHIP_EUROPEAN_ROWS: dict[str, str] = {
    "cs": "Informace o členství|Získejte více s prémiovým členstvím|Vaše úroveň|Prémioví členové|Členové zdarma|Vždy zdarma|Prémiové členství je na tomto účtu aktivní, včetně sekce s informacemi o metrikách na této stránce.|Zobrazit prémiové členství|Zobrazit možnosti prémiového členství|$5 měsíčně|$49 ročně|Další informace|Jak používat Go and Help|Zásady ochrany soukromí a cookies|Uživatelská smlouva|Poděkování|Zpět na váš profil|Oddíl {count}|Tato obrazovka je součástí aplikace Go and Help. Je určena dospělým po celém světě a nepředstavuje právní poradenství pro žádnou konkrétní zemi.|Neomezený počet témat a komentářů v komunitním fóru|Neomezené nabídky pomoci|Požádejte o více pomocníků pro události|Přednostní zobrazení žádostí o pomoc|Metriky pro více odpovědí|Pokročilé možnosti vyhledávání|10 současných žádostí o pomoc|Vlastní motivy a režimy|1 nabídka pomoci denně|2 současné žádosti o pomoc|Viditelnost příspěvku po dobu jednoho měsíce|Nabízejte a poskytujte pomoc kdekoli, vždy zdarma|Čtěte komunitní fórum|1 téma ve fóru za kalendářní měsíc podle UTC|10 komentářů ve fóru za kalendářní měsíc podle UTC napříč všemi diskusemi|Základní vyhledávání podle kategorie úkolu a odměny",
    "da": "Oplysninger om medlemskab|Få mere med et premiummedlemskab|Dit niveau|Premiummedlemmer|Gratis medlemmer|Altid gratis|Premium er aktivt på denne konto, inklusive afsnittet med oplysninger om målinger på denne side.|Se premiummedlemskab|Se muligheder for premiummedlemskab|$5 om måneden|$49 om året|Flere oplysninger|Sådan bruger du Go and Help|Politik om privatliv og cookies|Brugeraftale|Tak til bidragyderne|Tilbage til din profil|Afsnit {count}|Denne skærm er en del af Go and Help-appen. Den er skrevet til voksne overalt og er ikke juridisk rådgivning for noget bestemt land.|Ubegrænsede emner og kommentarer i fællesskabets forum|Ubegrænsede tilbud om hjælp|Anmod om flere hjælpere til begivenheder|Prioriteret visning af anmodninger om hjælp|Målinger til at få flere svar|Avancerede søgemuligheder|10 samtidige anmodninger om hjælp|Tilpassede temaer og tilstande|1 tilbud om hjælp om dagen|2 samtidige anmodninger om hjælp|Opslag er synlige i én måned|Tilbyd og giv hjælp overalt, altid gratis|Læs fællesskabets forum|1 forumemne pr. kalendermåned i UTC|10 forumkommentarer pr. kalendermåned i UTC på tværs af alle diskussioner|Grundlæggende søgning efter opgavekategori og belønning",
    "nl": "Informatie over lidmaatschap|Krijg meer als Premiumlid|Jouw niveau|Premiumleden|Gratis leden|Altijd gratis|Premium is actief op dit account, inclusief het gedeelte met informatie over statistieken op deze pagina.|Bekijk Premiumlidmaatschap|Bekijk de opties voor Premiumlidmaatschap|$5 per maand|$49 per jaar|Meer informatie|Go and Help gebruiken|Privacy- en cookiebeleid|Gebruikersovereenkomst|Credits|Terug naar je profiel|Onderdeel {count}|Dit scherm maakt deel uit van de Go and Help-app. Het is geschreven voor volwassenen overal ter wereld en is geen juridisch advies voor een bepaald land.|Onbeperkt onderwerpen en reacties in het communityforum|Onbeperkt hulp aanbieden|Vraag meerdere helpers voor evenementen|Voorrang bij het bekijken van hulpverzoeken|Statistieken om meer reacties te krijgen|Geavanceerde zoekopties|10 gelijktijdige hulpverzoeken|Aangepaste thema’s en modi|1 hulpaanbod per dag|2 gelijktijdige hulpverzoeken|Berichten blijven één maand zichtbaar|Bied en geef overal hulp, altijd gratis|Lees het communityforum|1 forumonderwerp per kalendermaand volgens UTC|10 forumreacties per kalendermaand volgens UTC, verdeeld over alle discussies|Eenvoudig zoeken op taakcategorie en beloning",
    "fi": "Jäsenyystiedot|Saat enemmän Premium-jäsenenä|Jäsenyystasosi|Premium-jäsenet|Ilmaisjäsenet|Aina ilmainen|Premium on käytössä tällä tilillä, myös tämän sivun mittaritietojen osiossa.|Katso Premium-jäsenyys|Katso Premium-jäsenyyden vaihtoehdot|$5 kuukaudessa|$49 vuodessa|Lisätietoja|Go and Help -sovelluksen käyttö|Tietosuoja- ja evästekäytäntö|Käyttäjäsopimus|Kiitokset|Takaisin profiiliisi|Osio {count}|Tämä näkymä on osa Go and Help -sovellusta. Se on kirjoitettu aikuisille kaikkialla maailmassa eikä ole minkään tietyn maan oikeudellista neuvontaa.|Rajattomasti aiheita ja kommentteja yhteisöfoorumilla|Rajattomasti avuntarjouksia|Pyydä useita auttajia tapahtumiin|Avunpyyntöjen ensisijainen katselu|Mittarit vastausten lisäämiseksi|Edistyneet hakuvaihtoehdot|10 samanaikaista avunpyyntöä|Mukautetut teemat ja tilat|1 avuntarjous päivässä|2 samanaikaista avunpyyntöä|Julkaisu näkyy yhden kuukauden|Tarjoa ja anna apua missä tahansa, aina ilmaiseksi|Lue yhteisöfoorumia|1 foorumiaihe UTC-ajan kalenterikuukaudessa|10 foorumikommenttia UTC-ajan kalenterikuukaudessa kaikkien keskustelujen kesken|Perushaku tehtäväluokan ja palkkion mukaan",
    "fr": "Informations sur l’adhésion|Profitez de plus d’avantages en devenant membre Premium|Votre formule|Membres Premium|Membres gratuits|Toujours gratuit|L’adhésion Premium est active sur ce compte, y compris la section Informations sur les statistiques de cette page.|Voir l’adhésion Premium|Voir les options d’adhésion Premium|$5 par mois|$49 par an|Plus d’informations|Comment utiliser Go and Help|Politique de confidentialité et de cookies|Accord utilisateur|Crédits|Retour à votre profil|Rubrique {count}|Cet écran fait partie de l’application Go and Help. Il s’adresse aux adultes du monde entier et ne constitue pas un conseil juridique pour un pays en particulier.|Sujets et commentaires illimités sur le forum communautaire|Offres d’aide illimitées|Demandez plusieurs personnes pour aider lors d’événements|Accès prioritaire aux demandes d’aide|Statistiques pour obtenir davantage de réponses|Options de recherche avancée|10 demandes d’aide simultanées|Thèmes et modes personnalisés|1 offre d’aide par jour|2 demandes d’aide simultanées|Publication visible pendant un mois|Proposez et apportez votre aide partout, toujours gratuitement|Lisez le forum communautaire|1 sujet de forum par mois civil selon UTC|10 commentaires sur le forum par mois civil selon UTC, toutes discussions confondues|Recherche de base par catégorie de tâche et récompense",
    "de": "Informationen zur Mitgliedschaft|Erhalte mehr als Premium-Mitglied|Deine Stufe|Premium-Mitglieder|Kostenlose Mitglieder|Immer kostenlos|Premium ist auf diesem Konto aktiv, einschließlich des Bereichs mit Kennzahleninformationen auf dieser Seite.|Premium-Mitgliedschaft ansehen|Optionen für die Premium-Mitgliedschaft ansehen|$5 monatlich|$49 jährlich|Weitere Informationen|So verwendest du Go and Help|Datenschutz- und Cookie-Richtlinie|Nutzungsvereinbarung|Danksagungen|Zurück zu deinem Profil|Abschnitt {count}|Diese Ansicht ist Teil der Go and Help-App. Sie richtet sich an Erwachsene weltweit und ist keine Rechtsberatung für ein bestimmtes Land.|Unbegrenzt Themen und Kommentare im Community-Forum|Unbegrenzt Hilfsangebote|Mehrere Helfer für Veranstaltungen anfragen|Hilfeanfragen bevorzugt ansehen|Kennzahlen für mehr Antworten|Erweiterte Suchoptionen|10 gleichzeitige Hilfeanfragen|Individuelle Designs und Modi|1 Hilfsangebot pro Tag|2 gleichzeitige Hilfeanfragen|Beiträge einen Monat lang sichtbar|Überall Hilfe anbieten und leisten, immer kostenlos|Das Community-Forum lesen|1 Forumthema pro Kalendermonat nach UTC|10 Forumkommentare pro Kalendermonat nach UTC über alle Diskussionen hinweg|Einfache Suche nach Aufgabenkategorie und Belohnung",
    "el": "Πληροφορίες συνδρομής|Αποκτήστε περισσότερα ως μέλος Premium|Το επίπεδό σας|Μέλη Premium|Δωρεάν μέλη|Πάντα δωρεάν|Η συνδρομή Premium είναι ενεργή σε αυτόν τον λογαριασμό, μαζί με την ενότητα πληροφοριών μετρήσεων σε αυτή τη σελίδα.|Δείτε τη συνδρομή Premium|Δείτε τις επιλογές συνδρομής Premium|$5 μηνιαίως|$49 ετησίως|Περισσότερες πληροφορίες|Πώς να χρησιμοποιήσετε το Go and Help|Πολιτική απορρήτου και cookies|Συμφωνία χρήστη|Ευχαριστίες|Επιστροφή στο προφίλ σας|Ενότητα {count}|Αυτή η οθόνη αποτελεί μέρος της εφαρμογής Go and Help. Απευθύνεται σε ενήλικες παντού και δεν αποτελεί νομική συμβουλή για κάποια συγκεκριμένη χώρα.|Απεριόριστα θέματα και σχόλια στο φόρουμ της κοινότητας|Απεριόριστες προσφορές βοήθειας|Ζητήστε πολλούς βοηθούς για εκδηλώσεις|Προτεραιότητα στην προβολή αιτημάτων βοήθειας|Μετρήσεις για περισσότερες απαντήσεις|Προηγμένες επιλογές αναζήτησης|10 ταυτόχρονα αιτήματα βοήθειας|Προσαρμοσμένα θέματα και λειτουργίες|1 προσφορά βοήθειας την ημέρα|2 ταυτόχρονα αιτήματα βοήθειας|Ορατότητα ανάρτησης για έναν μήνα|Προσφέρετε και παρέχετε βοήθεια παντού, πάντα δωρεάν|Διαβάστε το φόρουμ της κοινότητας|1 θέμα φόρουμ ανά ημερολογιακό μήνα UTC|10 σχόλια φόρουμ ανά ημερολογιακό μήνα UTC σε όλες τις συζητήσεις συνολικά|Βασική αναζήτηση ανά κατηγορία εργασίας και ανταμοιβή",
    "hu": "Tagsági információk|Érj el többet prémium tagként|A te szinted|Prémium tagok|Ingyenes tagok|Mindig ingyenes|A prémium tagság aktív ezen a fiókon, beleértve az oldal mutatószámokról szóló részét is.|Prémium tagság megtekintése|Prémium tagsági lehetőségek megtekintése|$5 havonta|$49 évente|További információk|A Go and Help használata|Adatvédelmi és sütikezelési szabályzat|Felhasználói megállapodás|Köszönetnyilvánítás|Vissza a profilodhoz|{count}. szakasz|Ez a képernyő a Go and Help alkalmazás része. Világszerte felnőtteknek készült, és nem minősül egyetlen konkrét országra vonatkozó jogi tanácsadásnak.|Korlátlan témák és hozzászólások a közösségi fórumon|Korlátlan segítségfelajánlások|Kérj több segítőt az eseményekhez|Segítségkérések elsőbbségi megtekintése|Mutatószámok a több válaszért|Speciális keresési lehetőségek|10 egyidejű segítségkérés|Egyéni témák és módok|Napi 1 segítségfelajánlás|2 egyidejű segítségkérés|A bejegyzés egy hónapig látható|Ajánlj fel és nyújts segítséget bárhol, mindig ingyen|Olvasd a közösségi fórumot|1 fórumtéma UTC szerinti naptári hónaponként|10 fórumhozzászólás UTC szerinti naptári hónaponként, az összes beszélgetésben együttvéve|Alapkeresés feladatkategória és jutalom szerint",
    "it": "Informazioni sull’iscrizione|Ottieni di più come membro Premium|Il tuo livello|Membri Premium|Membri gratuiti|Sempre gratuito|L’iscrizione Premium è attiva su questo account, inclusa la sezione Informazioni sulle metriche di questa pagina.|Visualizza l’iscrizione Premium|Visualizza le opzioni di iscrizione Premium|$5 al mese|$49 all’anno|Altre informazioni|Come usare Go and Help|Informativa sulla privacy e sui cookie|Accordo con l’utente|Crediti|Torna al tuo profilo|Sezione {count}|Questa schermata fa parte dell’app Go and Help. È scritta per gli adulti di tutto il mondo e non costituisce consulenza legale per un paese specifico.|Argomenti e commenti illimitati nel forum della comunità|Offerte di aiuto illimitate|Richiedi più persone per aiutare agli eventi|Visualizzazione prioritaria delle richieste di aiuto|Metriche per ottenere più risposte|Opzioni di ricerca avanzata|10 richieste di aiuto simultanee|Temi e modalità personalizzati|1 offerta di aiuto al giorno|2 richieste di aiuto simultanee|Visibilità del post per un mese|Offri e dai aiuto ovunque, sempre gratuitamente|Leggi il forum della comunità|1 argomento nel forum per mese di calendario secondo UTC|10 commenti nel forum per mese di calendario secondo UTC, complessivamente in tutte le discussioni|Ricerca di base per categoria di attività e ricompensa",
    "pl": "Informacje o członkostwie|Zyskaj więcej jako członek Premium|Twój poziom|Członkowie Premium|Członkowie bezpłatni|Zawsze bezpłatnie|Premium jest aktywne na tym koncie, w tym sekcja informacji o statystykach na tej stronie.|Zobacz członkostwo Premium|Zobacz opcje członkostwa Premium|$5 miesięcznie|$49 rocznie|Więcej informacji|Jak korzystać z Go and Help|Polityka prywatności i plików cookie|Umowa użytkownika|Podziękowania|Wróć do swojego profilu|Sekcja {count}|Ten ekran jest częścią aplikacji Go and Help. Jest przeznaczony dla dorosłych na całym świecie i nie stanowi porady prawnej dotyczącej żadnego konkretnego kraju.|Nieograniczone tematy i komentarze na forum społeczności|Nieograniczone oferty pomocy|Poproś o wielu pomocników na wydarzenia|Priorytetowy podgląd próśb o pomoc|Statystyki zwiększające liczbę odpowiedzi|Zaawansowane opcje wyszukiwania|10 jednoczesnych próśb o pomoc|Własne motywy i tryby|1 oferta pomocy dziennie|2 jednoczesne prośby o pomoc|Widoczność wpisu przez jeden miesiąc|Oferuj i udzielaj pomocy wszędzie, zawsze bezpłatnie|Czytaj forum społeczności|1 temat na forum na miesiąc kalendarzowy według UTC|10 komentarzy na forum na miesiąc kalendarzowy według UTC łącznie we wszystkich dyskusjach|Podstawowe wyszukiwanie według kategorii zadania i nagrody",
    "pt": "Informações sobre a adesão|Tenha mais vantagens como membro Premium|O seu nível|Membros Premium|Membros gratuitos|Sempre gratuito|A adesão Premium está ativa nesta conta, incluindo a secção de informações sobre métricas nesta página.|Ver adesão Premium|Ver opções de adesão Premium|$5 por mês|$49 por ano|Mais informações|Como utilizar o Go and Help|Política de privacidade e cookies|Acordo do utilizador|Créditos|Voltar ao seu perfil|Secção {count}|Este ecrã faz parte da aplicação Go and Help. Destina-se a adultos em todo o mundo e não constitui aconselhamento jurídico para qualquer país específico.|Tópicos e comentários ilimitados no fórum da comunidade|Ofertas de ajuda ilimitadas|Peça vários ajudantes para eventos|Visualização prioritária dos pedidos de ajuda|Métricas para obter mais respostas|Opções de pesquisa avançada|10 pedidos de ajuda simultâneos|Temas e modos personalizados|1 oferta de ajuda por dia|2 pedidos de ajuda simultâneos|Publicação visível durante um mês|Ofereça e dê ajuda em qualquer lugar, sempre gratuitamente|Leia o fórum da comunidade|1 tópico no fórum por mês de calendário segundo UTC|10 comentários no fórum por mês de calendário segundo UTC, no conjunto de todas as discussões|Pesquisa básica por categoria de tarefa e recompensa",
    "ro": "Informații despre abonament|Obține mai mult ca membru Premium|Nivelul tău|Membri Premium|Membri gratuiți|Întotdeauna gratuit|Abonamentul Premium este activ pe acest cont, inclusiv secțiunea cu informații despre indicatori de pe această pagină.|Vezi abonamentul Premium|Vezi opțiunile de abonament Premium|$5 lunar|$49 anual|Mai multe informații|Cum să folosești Go and Help|Politica de confidențialitate și cookie-uri|Acordul utilizatorului|Mulțumiri|Înapoi la profilul tău|Secțiunea {count}|Acest ecran face parte din aplicația Go and Help. Este scris pentru adulți de pretutindeni și nu reprezintă consultanță juridică pentru o anumită țară.|Subiecte și comentarii nelimitate pe forumul comunității|Oferte de ajutor nelimitate|Solicită mai mulți ajutori pentru evenimente|Vizualizare prioritară a cererilor de ajutor|Indicatori pentru mai multe răspunsuri|Opțiuni de căutare avansată|10 cereri de ajutor simultane|Teme și moduri personalizate|1 ofertă de ajutor pe zi|2 cereri de ajutor simultane|Postarea este vizibilă timp de o lună|Oferă și acordă ajutor oriunde, întotdeauna gratuit|Citește forumul comunității|1 subiect pe forum pe lună calendaristică conform UTC|10 comentarii pe forum pe lună calendaristică conform UTC, în total în toate discuțiile|Căutare de bază după categoria sarcinii și recompensă",
}

PROFILE_MEMBERSHIP_ROWS: dict[str, str] = {
    **PROFILE_MEMBERSHIP_EUROPEAN_ROWS,
    **PROFILE_MEMBERSHIP_GLOBAL_ROWS,
    **PROFILE_MEMBERSHIP_ASIAN_ROWS,
}
PROFILE_MEMBERSHIP_SOURCE_COINCIDENCES: frozenset[tuple[str, str]] = frozenset(
    {("nl", "Credits")}
)
_EXPECTED_LOCALES = {code for code, _ in LANGUAGE_OPTIONS if code != "en"}
if (
    len(PROFILE_MEMBERSHIP_KEYS) != 35
    or len(set(PROFILE_MEMBERSHIP_KEYS)) != 35
):
    raise ValueError("Membership catalog requires exactly 35 unique sources")
if set(PROFILE_MEMBERSHIP_ROWS) != _EXPECTED_LOCALES:
    raise ValueError(
        "Membership catalog must cover every offered non-English locale"
    )
if sum(
    map(
        len,
        (
            PROFILE_MEMBERSHIP_EUROPEAN_ROWS,
            PROFILE_MEMBERSHIP_GLOBAL_ROWS,
            PROFILE_MEMBERSHIP_ASIAN_ROWS,
        ),
    )
) != len(PROFILE_MEMBERSHIP_ROWS):
    raise ValueError("Membership locale groups must not overlap")
PROFILE_MEMBERSHIP_CATALOGS: dict[str, dict[str, str]] = {
    locale: dict(zip(PROFILE_MEMBERSHIP_KEYS, row.split("|"), strict=True))
    for locale, row in PROFILE_MEMBERSHIP_ROWS.items()
}
for _locale, _entries in PROFILE_MEMBERSHIP_CATALOGS.items():
    for _source, _value in _entries.items():
        if not _value.strip() or (
            _value == _source
            and (_locale, _source) not in PROFILE_MEMBERSHIP_SOURCE_COINCIDENCES
        ):
            raise ValueError(
                f"Missing native membership phrase: {_locale}: {_source}"
            )
        if Counter(
            slot for _, slot, _, _ in Formatter().parse(_source) if slot
        ) != Counter(
            slot for _, slot, _, _ in Formatter().parse(_value) if slot
        ):
            raise ValueError(
                f"Membership placeholder mismatch: {_locale}: {_source}"
            )
