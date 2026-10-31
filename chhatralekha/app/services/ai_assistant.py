"""ChhatraLekha AI Assistant Knowledge Base and Grounded Query Engine.

Provides platform guidance, role-aware answers, and multilingual responses
grounded in documentation, operational rules, and user-authorized records.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# Core knowledge articles for platform features
KNOWLEDGE_BASE = [
    {
        "id": "attendance",
        "keywords": ["attendance", "present", "absent", "leave", "उपस्थिति", "ଉପସ୍ଥାନ"],
        "roles": ["student", "parent", "teacher", "institution_admin", "aicte_admin"],
        "en": (
            "You can check your attendance by navigating to the Attendance or Home tab in your portal. "
            "Students and parents see daily subject-wise percentages and session status. "
            "Teachers can record attendance by opening the Teacher Workspace, selecting the active class session, "
            "and marking students as Present, Absent, or Late."
        ),
        "hi": (
            "आप अपने पोर्टल में उपस्थिति या होम टैब पर जाकर अपनी उपस्थिति देख सकते हैं। "
            "छात्र और अभिभावक विषयवार प्रतिशत और स्थिति देख सकते हैं। "
            "शिक्षक 'टीचर वर्कस्पेस' में जाकर कक्षा सत्र चुनकर उपस्थिति दर्ज कर सकते हैं।"
        ),
        "or": (
            "ଆପଣ ଆପଣଙ୍କ ପୋର୍ଟାଲରେ ଉପସ୍ଥାନ କିମ୍ବା ହୋମ ଟ୍ୟାବକୁ ଯାଇ ନିଜର ଉପସ୍ଥାନ ଯାଞ୍ଚ କରିପାରିବେ। "
            "ଛାତ୍ରଛାତ୍ରୀ ଏବଂ ଅଭିଭାବକ ପ୍ରତି ବିଷୟର ଶତକଡ଼ା ହାର ଦେଖିପାରିବେ। "
            "ଶିକ୍ଷକମାନେ ଟିଚର ୱାର୍କସ୍ପେସରେ ଯାଇ ଉପସ୍ଥାନ ଦର୍ଜ କରିପାରିବେ।"
        ),
        "actions": [
            {"label": "Check Attendance", "url": "/me"},
            {"label": "Teacher Workspace", "url": "/teacher"},
        ],
    },
    {
        "id": "timetable",
        "keywords": ["timetable", "class schedule", "schedule", "routine", "टाइम टेबल", "समय सारणी", "ଟାଇମ୍ ଟେବୁଲ୍", "ସମୟ ସାରଣୀ"],
        "roles": ["student", "parent", "teacher", "institution_admin"],
        "en": (
            "Your weekly class timetable is available on the Home dashboard and under Class Schedule. "
            "It displays scheduled course periods, room numbers, assigned faculty, and timings for every day of the week. "
            "You can also use the voice assistant: click the microphone and say 'Show my class timetable'."
        ),
        "hi": (
            "आपकी साप्ताहिक कक्षा की समय सारणी होम डैशबोर्ड पर उपलब्ध है। "
            "इसमें प्रत्येक दिन के लिए कक्षाएं, विषय, कक्ष संख्या और शिक्षक की जानकारी मिलती है। "
            "आप माइक पर क्लिक करके 'मेरा टाइम टेबल दिखाओ' भी बोल सकते हैं।"
        ),
        "or": (
            "ଆପଣଙ୍କ ସାପ୍ତାହିକ କ୍ଲାସ୍ ଟାଇମ୍ ଟେବୁଲ୍ ହୋମ୍ ଡ୍ୟାସବୋର୍ଡରେ ଉପଲବ୍ଧ। "
            "ଏଥିରେ ବିଷୟ, କ୍ଲାସରୁମ୍ ଏବଂ ଶିକ୍ଷକଙ୍କ ସମୟ ସାରଣୀ ଦେଖିପାରିବେ। "
            "ଆପଣ ମାଇକ୍ରୋଫୋନରେ 'ମୋର ଆଜିର କ୍ଲାସ୍ ଟାଇମ୍ ଟେବୁଲ୍ ଦେଖାଅ' ମଧ୍ୟ କହିପାରିବେ।"
        ),
        "actions": [
            {"label": "View Schedule", "url": "/me"},
        ],
    },
    {
        "id": "language_and_voice",
        "keywords": ["language", "change language", "voice", "speech", "bhasha", "ଭାଷା", "भाषा"],
        "roles": ["student", "parent", "teacher", "institution_admin", "aicte_admin", "verifier"],
        "en": (
            "ChhatraLekha supports all 22 Eighth Schedule Indian languages. "
            "To change your language, click the Language dropdown in the top navigation bar and select your preferred language. "
            "To use voice navigation, click the microphone button in the header and speak your query in English, Hindi, or Odia."
        ),
        "hi": (
            "छात्रलेखा भारत के संविधान की 8वीं अनुसूची की सभी 22 भाषाओं का समर्थन करता है। "
            "भाषा बदलने के लिए शीर्ष नेविगेशन बार में भाषा ड्रॉपडाउन पर क्लिक करें। "
            "आवाज से नेविगेट करने के लिए हेडर में माइक्रोफ़ोन बटन पर क्लिक करें।"
        ),
        "or": (
            "ଛାତ୍ରଲେଖା ଭାରତୀୟ ସମ୍ବିଧାନର ଅଷ୍ଟମ ଅନୁସୂଚୀର ସମସ୍ତ ୨୨ଟି ଭାଷାକୁ ସମର୍ଥନ କରେ। "
            "ଭାଷା ପରିବର୍ତ୍ତନ ପାଇଁ ଉପର ନେଭିଗେସନ୍ ବାରରେ ଭାଷା ଡ୍ରପଡାଉନ୍ ଚୟନ କରନ୍ତୁ। "
            "ଭଏସ୍ ବ୍ୟବହାର ପାଇଁ ମାଇକ୍ରୋଫୋନ୍ ବଟନ୍ ଦବାନ୍ତୁ।"
        ),
        "actions": [
            {"label": "Explore Languages", "url": "/about"},
        ],
    },
    {
        "id": "id_card_and_apaar",
        "keywords": ["apaar", "id card", "identity", "qr", "badge", "token", "पहचान पत्र", "ପରିଚୟ ପତ୍ର"],
        "roles": ["student", "parent", "institution_admin"],
        "en": (
            "Your digital APAAR ID card is accessible under the 'ID Card' tab (/me/id-card). "
            "It features your verified academic details and an opaque, time-limited cryptographic QR code. "
            "Your 12-digit APAAR ID is masked for privacy (****-****-XXXX), and the QR token allows employers or institutions "
            "to verify your credentials tamper-evidently without revealing your personal private data."
        ),
        "hi": (
            "आपका डिजिटल अपार पहचान पत्र 'ID Card' टैब (/me/id-card) पर उपलब्ध है। "
            "इसमें आपके सत्यापित विवरण और एक सुरक्षित क्यूआर कोड शामिल है। "
            "गोपनीयता के लिए आपका 12-अंकों का अपार नंबर मास्क किया जाता है।"
        ),
        "or": (
            "ଆପଣଙ୍କର ଡିଜିଟାଲ୍ ଅପାର୍ ଆଇଡି କାର୍ଡ 'ID Card' ଟ୍ୟାବ (/me/id-card) ରେ ଉପଲବ୍ଧ। "
            "ଏଥିରେ ସତ୍ୟାପିତ ବିବରଣୀ ଏବଂ ଏକ ସୁରକ୍ଷିତ କ୍ରିପ୍ଟୋଗ୍ରାଫିକ୍ QR କୋଡ୍ ରହିଛି। "
            "ଗୋପନୀୟତା ପାଇଁ ଆପଣଙ୍କର ୧୨ ଅଙ୍କ ବିଶିଷ୍ଟ ଅପାର୍ ନମ୍ବର ମାସ୍କ ହୋଇ ରହିଥାଏ।"
        ),
        "actions": [
            {"label": "Open Digital ID Card", "url": "/me/id-card"},
            {"label": "Credential Wallet", "url": "/wallet"},
        ],
    },
    {
        "id": "results_and_marks",
        "keywords": ["results", "marks", "grades", "cgpa", "sgpa", "exam", "परिणाम", "ଫଳାଫଳ"],
        "roles": ["student", "parent", "teacher", "institution_admin"],
        "en": (
            "Examination results, semester SGPA, and cumulative CGPA are listed under the 'Results' tab (/me/results). "
            "You can view subject-wise credits, grade letters, and download signed mark transcripts. "
            "Teachers can publish term grades through the Assessments section."
        ),
        "hi": (
            "परीक्षा परिणाम, सेमेस्टर SGPA और संचयी CGPA 'Results' टैब (/me/results) पर उपलब्ध हैं। "
            "आप विषयवार क्रेडिट और ग्रेड देख सकते हैं तथा हस्ताक्षरित अंकतालिका डाउनलोड कर सकते हैं।"
        ),
        "or": (
            "ପରୀକ୍ଷା ଫଳାଫଳ, ସେମିଷ୍ଟାର SGPA ଏବଂ CGPA 'Results' ଟ୍ୟାବ (/me/results) ରେ ଦେଖିପାରିବେ। "
            "ଆପଣ ବିଷୟବାର ମାର୍କ ଏବଂ ପ୍ରମାଣପତ୍ର ଡାଉନଲୋଡ୍ କରିପାରିବେ।"
        ),
        "actions": [
            {"label": "View Results", "url": "/me/results"},
            {"label": "Assessments", "url": "/assessments"},
        ],
    },
    {
        "id": "admin_operations",
        "keywords": ["institution", "add student", "class", "course", "anomaly", "upload", "प्रबंधन", "ଅନୁଷ୍ଠାନ"],
        "roles": ["institution_admin", "aicte_admin"],
        "en": (
            "Institution administrators can manage campus operations through the Institution Dashboard (/institution). "
            "To add students or batches, use 'Bulk CSV Ingestion' (/upload). "
            "To check quota ceilings and regulatory compliance, review 'Anomalies' (/anomalies). "
            "Before saving any correction to a student record, simulate its downstream effects using the 'Impact Engine' (/impact)."
        ),
        "hi": (
            "संस्थान प्रशासक 'संस्थान डैशबोर्ड' (/institution) के माध्यम से संचालन का प्रबंधन कर सकते हैं। "
            "छात्रों को जोड़ने के लिए 'बल्क सीएसवी अपलोड' (/upload) का उपयोग करें। "
            "नियमों और विसंगतियों की जांच के लिए 'विसंगति' (/anomalies) पृष्ठ देखें।"
        ),
        "or": (
            "ଅନୁଷ୍ଠାନ ପ୍ରଶାସକମାନେ ଇନଷ୍ଟିଚ୍ୟୁସନ୍ ଡ୍ୟାସବୋର୍ଡ (/institution) ମାଧ୍ୟମରେ କାର୍ଯ୍ୟ ପରିଚାଳନା କରିପାରିବେ। "
            "ଛାତ୍ରଛାତ୍ରୀ ଯୋଡ଼ିବା ପାଇଁ 'ଅପଲୋଡ୍' (/upload) ବ୍ୟବହାର କରନ୍ତୁ। "
            "ଅନିୟମିତତା ଯାଞ୍ଚ ପାଇଁ 'ଅନୋମାଲିଜ୍' (/anomalies) ପୃଷ୍ଠା ଦେଖନ୍ତୁ।"
        ),
        "actions": [
            {"label": "Institution Dashboard", "url": "/institution"},
            {"label": "Upload CSV", "url": "/upload"},
            {"label": "Anomaly Inspector", "url": "/anomalies"},
        ],
    },
    {
        "id": "platform_overview",
        "keywords": ["chhatralekha", "about", "what is", "free", "platform", "छत्रलेखा", "କ'ଣ"],
        "roles": ["student", "parent", "teacher", "institution_admin", "aicte_admin", "verifier"],
        "en": (
            "ChhatraLekha is a free, public-benefit education platform connecting Indian schools, colleges, universities, "
            "students, parents, and educators. It provides unified academic identity (APAAR integration), tamper-evident "
            "digital credentials, attendance tracking, examination publishing, and multilingual accessibility across all 22 Indian languages."
        ),
        "hi": (
            "छात्रलेखा भारतीय स्कूलों, कॉलेजों, विश्वविद्यालयों, छात्रों, अभिभावकों और शिक्षकों को जोड़ने वाला एक निःशुल्क शिक्षा मंच है। "
            "यह डिजिटल अपार पहचान, सुरक्षित क्रेडेंशियल, उपस्थिति, परीक्षा परिणाम और 22 भारतीय भाषाओं में पहुंच प्रदान करता है।"
        ),
        "or": (
            "ଛାତ୍ରଲେଖା ହେଉଛି ଏକ ମାଗଣା ଡିଜିଟାଲ୍ ଶିକ୍ଷା ପ୍ଲାଟଫର୍ମ ଯାହା ଭାରତର ସ୍କୁଲ, କଲେଜ, ବିଶ୍ୱବିଦ୍ୟାଳୟ, ଛାତ୍ରଛାତ୍ରୀ ଏବଂ ଶିକ୍ଷକମାନଙ୍କୁ ସଂଯୋଗ କରେ। "
            "ଏହା ଅପାର୍ ଆଇଡି, ସୁରକ୍ଷିତ ପ୍ରମାଣପତ୍ର, ଉପସ୍ଥାନ ଏବଂ ସମସ୍ତ ୨୨ଟି ଭାରତୀୟ ଭାଷାକୁ ସମର୍ଥନ କରେ।"
        ),
        "actions": [
            {"label": "About Platform", "url": "/about"},
            {"label": "Explore Demo", "url": "/"},
        ],
    },
]

ROLE_QUICK_PROMPTS = {
    "student": [
        "How do I check my timetable?",
        "Where can I find my digital APAAR ID card?",
        "How do I view my semester results?",
        "How do I create a verified share link?",
        "How can I change the platform language?",
    ],
    "parent": [
        "How do I check my child's attendance?",
        "Where are the latest class announcements?",
        "How do I verify academic mark sheets?",
        "How can I listen to notices with voice output?",
    ],
    "teacher": [
        "How do I mark daily class attendance?",
        "How do I upload student assessment marks?",
        "How do I post a notice to my class?",
        "Where can I review student roll numbers?",
    ],
    "institution_admin": [
        "How do I upload student rosters via CSV?",
        "How does the Anomaly Detection engine work?",
        "How do I preview the impact of a record correction?",
        "Where do I configure academic years and classes?",
    ],
    "aicte_admin": [
        "What are the national enrollment metrics?",
        "How do I inspect cross-institution duplicate APAAR IDs?",
        "How do I export regulatory compliance reports?",
    ],
    "verifier": [
        "How do I verify a student credential using a token?",
        "Are student personal details exposed during verification?",
    ],
}


def find_grounded_answer(
    query: str,
    role: str = "student",
    language: str = "en",
    user_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Retrieve grounded answer matching the user's intent and active language."""
    clean_q = query.lower().strip()
    lang = language.lower()
    if lang not in ["en", "hi", "or"]:
        # Fall back to English for languages without dedicated neural phrasing
        lang = "en"

    # Score knowledge base entries
    best_match = None
    highest_score = 0

    for article in KNOWLEDGE_BASE:
        score = 0
        for kw in article["keywords"]:
            if re.search(r"\b" + re.escape(kw) + r"\b", clean_q) or kw in clean_q:
                score += 2
        # Boost if relevant to current role
        if role in article.get("roles", []):
            score += 1

        if score > highest_score:
            highest_score = score
            best_match = article

    if best_match and highest_score >= 2:
        reply_text = best_match.get(lang) or best_match.get("en", "")
        # Add personalized context if available
        if user_context and user_context.get("name"):
            name = user_context["name"]
            if "my" in clean_q or "ମୋର" in clean_q or "मेरा" in clean_q:
                if best_match["id"] == "id_card_and_apaar" and user_context.get("student_id"):
                    reply_text += f" (Record: {user_context['student_id']})"
        return {
            "reply": reply_text,
            "actions": best_match.get("actions", []),
            "source": f"ChhatraLekha Documentation [{best_match['id']}]",
            "confidence": min(0.95, 0.70 + (highest_score * 0.05)),
        }

    # Default fallback answer
    if lang == "hi":
        fallback = (
            "मैं छात्रलेखा सहायक हूं। मैं उपस्थिति, टाइम टेबल, अपार पहचान पत्र, परिणाम, भाषा परिवर्तन "
            "और संस्थान प्रबंधन के बारे में आपकी सहायता कर सकता हूं। कृपया इनमें से कोई प्रश्न पूछें।"
        )
    elif lang == "or":
        fallback = (
            "ମୁଁ ଛାତ୍ରଲେଖା ସହାୟକ। ମୁଁ ଉପସ୍ଥାନ, ଟାଇମ୍ ଟେବୁଲ୍, ଅପାର୍ ଆଇଡି କାର୍ଡ, ପରୀକ୍ଷା ଫଳାଫଳ ଏବଂ "
            "ଅନୁଷ୍ଠାନ ପରିଚାଳନା ସମ୍ପର୍କରେ ସାହାଯ୍ୟ କରିପାରିବି। ଦୟାକରି ଏକ ପ୍ରଶ୍ନ ପଚାରନ୍ତୁ।"
        )
    else:
        fallback = (
            "I am the ChhatraLekha Assistant. I can guide you on checking your attendance, timetable, "
            "digital APAAR ID card, examination results, changing languages, or managing institution records. "
            "Feel free to ask a specific question or choose from the suggested prompts below."
        )

    return {
        "reply": fallback,
        "actions": [
            {"label": "Explore Demo", "url": "/"},
            {"label": "Help Center", "url": "/help"},
        ],
        "source": "ChhatraLekha Platform Guide",
        "confidence": 0.5,
    }


def get_quick_prompts_for_role(role: str) -> List[str]:
    """Return tailored quick question prompts for the user's role."""
    return ROLE_QUICK_PROMPTS.get(role, ROLE_QUICK_PROMPTS["student"])

