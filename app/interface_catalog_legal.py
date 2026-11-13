from app.interface_catalog_legal_east_asian import LEGAL_EAST_ASIAN_ROWS
from app.interface_catalog_legal_european_a import LEGAL_EUROPEAN_A_ROWS
from app.interface_catalog_legal_european_b import LEGAL_EUROPEAN_B_ROWS
from app.interface_catalog_legal_south_asian_a import LEGAL_SOUTH_ASIAN_A_ROWS
from app.interface_catalog_legal_south_asian_b import LEGAL_SOUTH_ASIAN_B_ROWS
from app.models import LANGUAGE_OPTIONS

LEGAL_KEYS: tuple[str, ...] = (
    "Go and Help legal policies",
    "Terms and Conditions",
    "Privacy Policy",
    "Cookies Policy",
    "Go and Help connects members who offer help with members who need it. You must be 16 or over, give accurate details and keep your account to yourself. Agree tasks, rewards and meeting points inside the platform, turn up when you say you will, and treat every member with respect. Go and Help is not an employer and does not supervise work: you remain responsible for your own safety, permits, tax and insurance. Illegal requests, harassment, discrimination, spam and attempts to move payment or identity checks off-platform lead to removal. Ratings must reflect real, completed work.",
    "We store the details you give us — first and family name, email, phone number, date of birth and profile content — to run your account, confirm your email and match you with nearby requests. Your date of birth is private account-verification data: we use it only to confirm you are 16 or over and never show it, or an age derived from it, to other members or guests. Guests only ever see job titles, categories and a rough area; exact meeting points, contact details and identities are unlocked for confirmed members involved in a task. We never sell your data and only share it with the services that deliver our emails and host the platform. You can update your profile, change your language, or ask us to delete your account and its data at any time.",
    "Go and Help uses a small number of essential cookies and local storage entries to keep you signed in, remember your language and protect the sign-in form from abuse. We use privacy-friendly, aggregated measurement to understand which features members use, and no advertising or cross-site tracking cookies. Clearing your browser storage signs you out and resets these preferences.",
)

_EXISTING_LEGAL_ROWS: dict[str, tuple[str, ...]] = {
    "es": (
        "Políticas legales de Go and Help",
        "Términos y condiciones",
        "Política de privacidad",
        "Política de cookies",
        "Go and Help conecta a quienes ofrecen ayuda con quienes la necesitan. Debes tener 16 años o más, dar datos exactos y mantener tu cuenta para tu uso. Acuerda las tareas, recompensas y lugares de encuentro en la plataforma, preséntate como prometiste y respeta a todos. Go and Help no es empleador ni supervisa el trabajo: tú respondes de tu seguridad, permisos, impuestos y seguro. Las solicitudes ilegales, el acoso, la discriminación, el spam y los intentos de sacar pagos o verificaciones de identidad de la plataforma conllevan la expulsión. Las valoraciones deben reflejar trabajo real y completado.",
        "Guardamos nombre y apellidos, correo, teléfono, fecha de nacimiento y contenido del perfil para gestionar tu cuenta, confirmar el correo y relacionarte con solicitudes cercanas. La fecha de nacimiento es información privada de verificación: solo confirma que tienes al menos 16 años; nunca mostramos la fecha ni la edad derivada a otros miembros o visitantes. Los visitantes solo ven títulos de tareas, categorías y una zona aproximada; los puntos exactos de encuentro, contactos e identidades se desbloquean para miembros confirmados que participan en una tarea. Nunca vendemos tus datos y solo los compartimos con los servicios que envían correos y alojan la plataforma. Puedes actualizar tu perfil, cambiar el idioma o pedir que eliminemos la cuenta y sus datos en cualquier momento.",
        "Go and Help usa unas pocas cookies esenciales y almacenamiento local para mantener tu sesión, recordar el idioma y proteger el formulario de acceso contra abusos. Usamos mediciones agregadas respetuosas con la privacidad para saber qué funciones se usan; no hay publicidad ni cookies de seguimiento entre sitios. Borrar el almacenamiento del navegador cierra tu sesión y restablece estas preferencias.",
    ),
    "fr": (
        "Politiques juridiques de Go and Help",
        "Conditions générales",
        "Politique de confidentialité",
        "Politique relative aux cookies",
        "Go and Help met en relation les membres qui proposent de l’aide et ceux qui en ont besoin. Vous devez avoir au moins 16 ans, fournir des renseignements exacts et garder votre compte pour votre usage. Convenez des tâches, récompenses et lieux de rencontre sur la plateforme, soyez présent comme prévu et respectez chaque membre. Go and Help n’est pas un employeur et ne supervise pas le travail : vous restez responsable de votre sécurité, de vos permis, impôts et assurances. Les demandes illégales, le harcèlement, la discrimination, le spam et les tentatives de déplacer paiements ou vérifications d’identité hors plateforme entraînent le retrait du compte. Les évaluations doivent porter sur un travail réel et terminé.",
        "Nous conservons votre prénom et nom, adresse e-mail, téléphone, date de naissance et contenu du profil pour gérer le compte, confirmer l’e-mail et vous mettre en relation avec des demandes proches. La date de naissance est une donnée privée de vérification : elle sert uniquement à confirmer que vous avez au moins 16 ans; nous ne montrons jamais cette date ni l’âge qui en est déduit aux membres ou visiteurs. Les visiteurs ne voient que les titres des tâches, catégories et une zone approximative; les lieux exacts, coordonnées et identités sont accessibles aux membres confirmés participant à une tâche. Nous ne vendons jamais vos données et les partageons uniquement avec les services d’envoi de courriels et d’hébergement. Vous pouvez mettre à jour votre profil, changer de langue ou demander la suppression du compte et de ses données à tout moment.",
        "Go and Help utilise quelques cookies essentiels et éléments de stockage local pour maintenir votre connexion, mémoriser la langue et protéger le formulaire de connexion contre les abus. Nous mesurons de façon agrégée et respectueuse de la vie privée les fonctions utilisées; sans publicité ni cookies de suivi entre sites. Effacer le stockage du navigateur vous déconnecte et réinitialise ces préférences.",
    ),
    "de": (
        "Rechtliche Hinweise zu Go and Help",
        "Allgemeine Geschäftsbedingungen",
        "Datenschutzerklärung",
        "Cookie-Richtlinie",
        "Go and Help verbindet Mitglieder, die Hilfe anbieten, mit denen, die Hilfe benötigen. Du musst mindestens 16 Jahre alt sein, korrekte Angaben machen und dein Konto selbst nutzen. Vereinbare Aufgaben, Belohnungen und Treffpunkte auf der Plattform, erscheine wie zugesagt und behandle alle respektvoll. Go and Help ist kein Arbeitgeber und beaufsichtigt keine Arbeit: Für Sicherheit, Genehmigungen, Steuern und Versicherung bist du selbst verantwortlich. Illegale Anfragen, Belästigung, Diskriminierung, Spam und Versuche, Zahlungen oder Identitätsprüfungen außerhalb der Plattform abzuwickeln, führen zum Ausschluss. Bewertungen müssen tatsächlich erledigte Arbeit widerspiegeln.",
        "Wir speichern Vor- und Nachname, E-Mail-Adresse, Telefonnummer, Geburtsdatum und Profilinhalte, um dein Konto zu betreiben, deine E-Mail zu bestätigen und dich mit Anfragen in der Nähe zusammenzubringen. Das Geburtsdatum ist eine private Angabe zur Kontoverifizierung: Es dient nur zur Bestätigung, dass du mindestens 16 bist; weder Datum noch daraus abgeleitetes Alter zeigen wir anderen Mitgliedern oder Gästen. Gäste sehen nur Aufgabentitel, Kategorien und ein ungefähres Gebiet; genaue Treffpunkte, Kontaktdaten und Identitäten werden bestätigten Mitgliedern freigeschaltet, die an einer Aufgabe beteiligt sind. Wir verkaufen deine Daten nie und teilen sie nur mit Diensten für E-Mail-Versand und Plattform-Hosting. Du kannst jederzeit dein Profil aktualisieren, die Sprache ändern oder die Löschung deines Kontos und seiner Daten beantragen.",
        "Go and Help verwendet wenige notwendige Cookies und lokale Speichereinträge, um dich angemeldet zu halten, deine Sprache zu speichern und das Anmeldeformular vor Missbrauch zu schützen. Wir messen aggregiert und datenschutzfreundlich, welche Funktionen Mitglieder verwenden; es gibt keine Werbung und keine websiteübergreifenden Tracking-Cookies. Das Löschen des Browser-Speichers meldet dich ab und setzt diese Einstellungen zurück.",
    ),
    "ar": (
        "السياسات القانونية في Go and Help",
        "الشروط والأحكام",
        "سياسة الخصوصية",
        "سياسة ملفات تعريف الارتباط",
        "تربط Go and Help الأعضاء الذين يقدمون المساعدة بمن يحتاجون إليها. يجب أن يكون عمرك 16 عامًا على الأقل، وأن تقدم بيانات دقيقة وتحافظ على استخدام حسابك لنفسك. اتفقوا على المهام والمكافآت وأماكن اللقاء داخل المنصة، واحضر كما وعدت، وعامل كل عضو باحترام. Go and Help ليست جهة توظيف ولا تشرف على العمل؛ وتظل مسؤولًا عن سلامتك وتصاريحك وضرائبك وتأمينك. تؤدي الطلبات غير القانونية والتحرش والتمييز والرسائل المزعجة ومحاولات نقل الدفع أو التحقق من الهوية خارج المنصة إلى إزالة الحساب. يجب أن تعكس التقييمات عملًا حقيقيًا مكتملًا.",
        "نخزن اسمك الأول واسم العائلة وبريدك الإلكتروني ورقم هاتفك وتاريخ ميلادك ومحتوى ملفك لتشغيل الحساب وتأكيد البريد ومطابقتك مع الطلبات القريبة. تاريخ الميلاد بيانات خاصة للتحقق من الحساب؛ نستخدمه فقط للتأكد من أن عمرك 16 عامًا أو أكثر، ولا نعرض التاريخ أو العمر المستنتج منه للأعضاء الآخرين أو الضيوف. لا يرى الضيوف إلا عناوين المهام وفئاتها ومنطقة تقريبية؛ وتُتاح نقاط اللقاء الدقيقة وبيانات الاتصال والهويات للأعضاء المؤكدين المشاركين في المهمة. لا نبيع بياناتك مطلقًا ونشاركها فقط مع خدمات إرسال البريد واستضافة المنصة. يمكنك تحديث ملفك أو تغيير اللغة أو طلب حذف الحساب وبياناته في أي وقت.",
        "تستخدم Go and Help عددًا قليلًا من ملفات تعريف الارتباط الضرورية وعناصر التخزين المحلي لإبقائك مسجلًا وتذكر لغتك وحماية نموذج الدخول من إساءة الاستخدام. نستخدم قياسًا مجمعًا يراعي الخصوصية لفهم الميزات المستخدمة؛ ولا نستخدم إعلانات أو ملفات تتبع عبر المواقع. يؤدي مسح تخزين المتصفح إلى تسجيل خروجك وإعادة ضبط هذه التفضيلات.",
    ),
    "zh": (
        "Go and Help 法律政策",
        "条款与条件",
        "隐私政策",
        "Cookie 政策",
        "Go and Help 将提供帮助的会员与需要帮助的会员联系起来。你必须年满16岁、提供准确资料并自行使用账户。在平台内商定任务、报酬和见面地点，按约定赴约并尊重每位会员。Go and Help 不是雇主，也不监督工作；你仍须对自身安全、许可证、税务和保险负责。非法请求、骚扰、歧视、垃圾信息，以及试图将付款或身份核验转移到平台外的行为会导致账号被移除。评价必须基于真实且已完成的工作。",
        "我们保存你提供的名字和姓氏、电子邮箱、电话号码、出生日期及个人资料内容，用于运营账户、确认邮箱并匹配附近请求。出生日期是私密账户验证资料，仅用于确认你已满16岁；绝不向其他会员或访客展示该日期或推算年龄。访客只能看到任务标题、类别和大致区域；准确见面地点、联系方式和身份信息仅向参与任务且已确认的会员开放。我们绝不出售数据，只与发送邮件和托管平台的服务共享。你可随时更新个人资料、更改语言，或要求删除账户及其数据。",
        "Go and Help 使用少量必要 Cookie 和本地存储来保持登录、记住语言并防止登录表单遭到滥用。我们以尊重隐私的汇总测量了解会员使用哪些功能；不使用广告或跨网站跟踪 Cookie。清除浏览器存储会使你退出登录并重置这些偏好。",
    ),
    "hi": (
        "Go and Help की कानूनी नीतियाँ",
        "नियम और शर्तें",
        "गोपनीयता नीति",
        "कुकी नीति",
        "Go and Help मदद देने वाले सदस्यों को मदद चाहने वालों से जोड़ता है। आपकी उम्र कम-से-कम 16 वर्ष होनी चाहिए, विवरण सही देने चाहिए और अपना खाता स्वयं इस्तेमाल करना चाहिए। काम, इनाम और मिलने की जगह प्लेटफ़ॉर्म के भीतर तय करें, वादे के अनुसार पहुँचें और हर सदस्य का सम्मान करें। Go and Help नियोक्ता नहीं है और काम की निगरानी नहीं करता: अपनी सुरक्षा, परमिट, कर और बीमा की ज़िम्मेदारी आपकी है। गैरकानूनी अनुरोध, उत्पीड़न, भेदभाव, स्पैम तथा भुगतान या पहचान-जाँच को प्लेटफ़ॉर्म से बाहर ले जाने के प्रयासों पर खाता हटेगा। रेटिंग वास्तविक और पूरे किए गए काम पर आधारित होनी चाहिए।",
        "हम आपके दिए नाम, उपनाम, ईमेल, फ़ोन नंबर, जन्मतिथि और प्रोफ़ाइल सामग्री को खाता चलाने, ईमेल की पुष्टि करने और पास के अनुरोधों से मिलाने के लिए रखते हैं। जन्मतिथि निजी सत्यापन जानकारी है: केवल यह पुष्टि करने के लिए कि आपकी उम्र कम-से-कम 16 है; तारीख या इससे निकली उम्र अन्य सदस्यों या मेहमानों को कभी नहीं दिखाई जाती। मेहमान केवल काम के शीर्षक, श्रेणियाँ और मोटा-मोटा क्षेत्र देखते हैं; सटीक मिलने की जगह, संपर्क और पहचान केवल उस काम में शामिल पुष्ट सदस्यों को मिलते हैं। हम डेटा नहीं बेचते और इसे केवल ईमेल भेजने तथा मंच होस्ट करने वाली सेवाओं से साझा करते हैं। आप कभी भी प्रोफ़ाइल अपडेट, भाषा बदलने या खाता और डेटा हटाने का अनुरोध कर सकते हैं।",
        "Go and Help साइन-इन बनाए रखने, भाषा याद रखने और फ़ॉर्म को दुरुपयोग से बचाने के लिए कुछ आवश्यक कुकी और स्थानीय संग्रह का उपयोग करता है। हम उपयोग की जाने वाली सुविधाओं को समझने के लिए गोपनीयता-सम्मत समेकित मापन करते हैं; विज्ञापन या साइटों पर नज़र रखने वाली कुकी नहीं हैं। ब्राउज़र संग्रह मिटाने पर आप साइन आउट होंगे और ये प्राथमिकताएँ रीसेट होंगी।",
    ),
    "ja": (
        "Go and Help の法的ポリシー",
        "利用規約",
        "プライバシーポリシー",
        "Cookie ポリシー",
        "Go and Help は、支援を提供するメンバーと必要とするメンバーをつなぎます。16歳以上で、正確な情報を提供し、自分のアカウントを自分で管理してください。タスク、謝礼、待ち合わせ場所はプラットフォーム内で合意し、約束どおりに到着し、すべてのメンバーを尊重してください。Go and Help は雇用主ではなく作業を監督しません。安全、許可、税金、保険はご自身の責任です。違法な依頼、嫌がらせ、差別、スパム、支払いや本人確認をプラットフォーム外に移す試みはアカウント削除の対象です。評価は実際に完了した作業を反映してください。",
        "アカウント運営、メール確認、近くの依頼との照合のため、名、姓、メールアドレス、電話番号、生年月日、プロフィール内容を保存します。生年月日は非公開の確認情報で、16歳以上であることの確認にのみ使用し、日付も算出した年齢も他のメンバーやゲストには表示しません。ゲストに見えるのはタスク名、カテゴリ、おおよその地域のみです。正確な待ち合わせ場所、連絡先、本人情報は、関係する確認済みメンバーにのみ開示されます。データを販売せず、メール配信とプラットフォームのホスティングを行うサービスとのみ共有します。プロフィール更新、言語変更、アカウントとデータの削除依頼はいつでも行えます。",
        "Go and Help は、ログイン状態の維持、言語の記憶、ログインフォームの不正利用防止のため、少数の必須Cookieとローカルストレージを使用します。利用機能を理解するためプライバシーに配慮した集計測定を行います。広告やサイト横断追跡Cookieはありません。ブラウザー保存領域を消去するとサインアウトし、これらの設定がリセットされます。",
    ),
    "ha": (
        "Manufofin doka na Go and Help",
        "Sharuɗɗa da ƙa'idoji",
        "Manufar sirri",
        "Manufar kukis",
        "Go and Help tana haɗa masu bayar da taimako da masu buƙatarsa. Dole ka kai shekara 16, ka bayar da sahihan bayanai, kuma ka yi amfani da asusunka da kanka. Ku amince da aiki, lada da wurin haɗuwa a dandamali, ka je lokacin da ka yi alƙawari, kuma ka mutunta kowane memba. Go and Help ba mai ɗaukar aiki ba ce kuma ba ta sa ido kan aiki: kai ne ke da alhakin tsarons, izini, haraji da inshora. Buƙatun da ba su halatta ba, cin zarafi, wariya, saƙonnin banza da ƙoƙarin fitar da biyan kuɗi ko tantance shaida daga dandamali suna sa a cire asusu. Ra’ayoyi su nuna aikin gaske da aka kammala.",
        "Muna adana sunan farko da na iyali, imel, lambar waya, ranar haihuwa da bayanin martaba domin gudanar da asusu, tabbatar da imel da haɗa ka da buƙatun kusa. Ranar haihuwa bayanin sirri ne na tantance asusu: don tabbatar da ka kai shekara 16 kawai ake amfani da ita; ba ma nuna ranar ko shekarun da aka ƙididdige ga wasu membobi ko baƙi. Baƙi suna ganin taken aiki, rukuni da yankin kusan kawai; ainihin wurin haɗuwa, bayanan tuntuɓa da shaida suna buɗewa ga tabbatattun membobin da ke cikin aikin. Ba ma sayar da bayananka; muna raba su ne kawai da ayyukan imel da karɓar dandamali. Za ka iya sabunta bayanin martaba, canza harshe ko neman share asusu da bayanansa a kowane lokaci.",
        "Go and Help tana amfani da ƴan kukis masu muhimmanci da ajiyar na’ura don kiyaye shigarka, tuna harshenka da kare fom ɗin shiga daga amfani ba daidai ba. Muna amfani da ma’auni na jimilla masu kula da sirri don fahimtar fasalolin da ake amfani da su; babu tallace-tallace ko kukis na bin sawu tsakanin shafuka. Share ajiyar burauza zai fitar da kai kuma ya sake saita zaɓuɓɓukan.",
    ),
}

_LEGAL_PARTS: tuple[dict[str, tuple[str, ...]], ...] = (
    LEGAL_EUROPEAN_A_ROWS,
    LEGAL_EUROPEAN_B_ROWS,
    LEGAL_SOUTH_ASIAN_A_ROWS,
    LEGAL_SOUTH_ASIAN_B_ROWS,
    LEGAL_EAST_ASIAN_ROWS,
)
_LEGAL_PART_LOCALES = [locale for part in _LEGAL_PARTS for locale in part]
if len(_LEGAL_PART_LOCALES) != len(set(_LEGAL_PART_LOCALES)):
    raise ValueError("Legal translation locale groups must be disjoint")
if set(_LEGAL_PART_LOCALES) & set(_EXISTING_LEGAL_ROWS):
    raise ValueError("New legal locale groups must not replace legacy rows")

_EXPECTED_LEGAL_LOCALES = {
    code for code, _label in LANGUAGE_OPTIONS if code != "en"
} | {"ha"}
LEGAL_ROWS: dict[str, tuple[str, ...]] = {
    **_EXISTING_LEGAL_ROWS,
    **{locale: row for part in _LEGAL_PARTS for locale, row in part.items()},
}
if set(LEGAL_ROWS) != _EXPECTED_LEGAL_LOCALES:
    raise ValueError("Legal translation locales do not match supported locales")
if any(len(row) != len(LEGAL_KEYS) for row in LEGAL_ROWS.values()):
    raise ValueError("Every legal translation must provide all seven sources")

LEGAL_CATALOGS: dict[str, dict[str, str]] = {
    language: dict(zip(LEGAL_KEYS, row, strict=True))
    for language, row in LEGAL_ROWS.items()
}
