"""Authorization-aware grounding engine for the ChhatraLekha assistant.

The assistant answers in two modes:

* **Guidance** - documentation and product help, available to anyone.
* **Grounded records** - real, already-authorised data for the signed-in
  caller. The caller's role and identity always come from the authenticated
  session, never from the request body.

The engine prefers an honest "I could not find that" over a plausible guess.
Every grounded answer carries the collection it was read from, so the UI can
show a citation instead of pretending the text fell from the sky.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.ai_assistant import find_grounded_answer, get_quick_prompts_for_role

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids an import cycle
    from app.api.deps import Principal

# Roles that may read records across institutions.
NATIONAL_ROLES = {
    "national_admin",
    "aicte_admin",
    "platform_operator",
    "regulator_admin",
    "state_admin",
    "district_admin",
}

# Roles that operate inside a single institution.
INSTITUTION_STAFF_ROLES = {"institution_admin", "academic_admin", "teacher"}

# Intents that need real records rather than a documentation answer.
RECORD_INTENTS = {
    "attendance",
    "results",
    "timetable",
    "notices",
    "id_card",
    "anomalies",
    "campus_stats",
    "national_stats",
}

INTENT_KEYWORDS: Dict[str, List[str]] = {
    "attendance": [
        "attendance",
        "present",
        "absent",
        "bunk",
        "hajiri",
        "उपस्थित",
        "हाजिरी",
        "अनुपस्थित",
        "ଉପସ୍ଥିତି",
        "ଉପସ୍ଥାନ",
        "ଅନୁପସ୍ଥିତ",
        "வருகை",
        "హాజరు",
        "ಹಾಜರಿ",
        "হাজিরা",
        "हजेरी",
    ],
    "results": [
        "result",
        "results",
        "marks",
        "mark sheet",
        "marksheet",
        "grade",
        "grades",
        "cgpa",
        "sgpa",
        "score",
        "percentage",
        "परिणाम",
        "अंक",
        "अंकतालिका",
        "ग्रेड",
        "ଫଳାଫଳ",
        "ମାର୍କ",
        "மதிப்பெண்",
        "ఫలితం",
        "ಫಲಿತಾಂಶ",
        "ফলাফল",
    ],
    "timetable": [
        "timetable",
        "time table",
        "schedule",
        "routine",
        "period",
        "periods",
        "which class",
        "what class",
        "टाइम टेबल",
        "समय सारणी",
        "शेड्यूल",
        "ଟାଇମ୍ ଟେବୁଲ୍",
        "ସମୟ ସାରଣୀ",
        "அட்டவணை",
        "కాలపట్టిక",
        "ವೇಳಾಪಟ್ಟಿ",
        "রুটিন",
    ],
    "notices": [
        "notice",
        "notices",
        "announcement",
        "announcements",
        "circular",
        "news",
        "सूचना",
        "घोषणा",
        "ଘୋଷଣା",
        "ସୂଚନା",
        "அறிவிப்பு",
        "నోటీసు",
        "সূচনা",
    ],
    "id_card": [
        "id card",
        "identity card",
        "apaar",
        "qr",
        "credential",
        "badge",
        "wallet",
        "पहचान पत्र",
        "अपार",
        "ପରିଚୟ ପତ୍ର",
        "ଅପାର",
        "அடையாள அட்டை",
        "ఐడి కార్డు",
        "আইডি কার্ড",
    ],
    "anomalies": [
        "anomaly",
        "anomalies",
        "duplicate",
        "compliance",
        "flagged",
        "intake breach",
        "विसंगति",
        "अनियमितता",
        "ଅନିୟମିତତା",
        "முரண்பாடு",
        "అసమానత",
    ],
    "campus_stats": [
        "how many students",
        "how many teachers",
        "enrolment",
        "enrollment",
        "enrolled",
        "campus",
        "institution stats",
        "institution statistics",
        "attendance rate",
        "utilisation",
        "utilization",
        "कितने छात्र",
        "नामांकन",
        "କେତେ ଛାତ୍ର",
        "ଭର୍ତ୍ତି",
    ],
    "national_stats": [
        "national",
        "national enrollment",
        "national enrolment",
        "national metrics",
        "national statistics",
        "national student",
        "national report",
        "pan-india",
        "pan india",
        "total institutions",
        "across india",
        "राष्ट्रीय",
        "ଜାତୀୟ",
    ],
    "verification": [
        "verify",
        "verification",
        "employer",
        "token",
        "seal",
        "tamper",
        "सत्यापन",
        "ଯାଞ୍ଚ",
        "சரிபார்ப்பு",
        "ధృవీకరణ",
        "যাচাই",
    ],
}

_GENERAL_EXPLANATION_MARKERS = (
    "what is ",
    "what are ",
    "what does ",
    "how does ",
    "how do ",
    "how can i ",
    "how can a ",
    "explain ",
    "tell me about ",
    "guide me ",
    "क्या है",
    "कैसे",
    "କ'ଣ",
    "କିପରି",
)

_PERSONAL_MARKERS = (
    " my ",
    "my ",
    "mera",
    "meri",
    "मेरा",
    "मेरी",
    "मेरे",
    "ମୋର",
    "ମୋ",
    "என்",
    "నా",
    "ನನ್ನ",
    "আমার",
)

_LANGUAGE_ALIASES = {
    "en": "en",
    "en-in": "en",
    "en-gb": "en",
    "en-us": "en",
    "hi": "hi",
    "hi-in": "hi",
    "or": "or",
    "or-in": "or",
    "odia": "or",
    "ory": "or",
}


def normalize_language(value: Optional[str]) -> str:
    """Map a UI locale (``hi-IN``) onto a supported answer language."""
    return _LANGUAGE_ALIASES.get((value or "en").strip().lower(), "en")


def _t(language: str, english: str, hindi: str, odia: str) -> str:
    """Pick one of the reviewed answer languages, falling back to English."""
    return {"en": english, "hi": hindi, "or": odia}.get(language, english)


def _has(text: str, needle: str) -> bool:
    if needle.isascii():
        return re.search(r"\b" + re.escape(needle) + r"\b", text) is not None
    return needle in text


def detect_intent(query: str) -> tuple[str, int]:
    """Return the best supported intent and its keyword score."""
    text = (query or "").lower().strip()
    best_intent = ""
    best_score = 0

    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(2 if _has(text, keyword) else 0 for keyword in keywords)
        # Longer phrases are more specific than a single word.
        score += sum(1 for keyword in keywords if len(keyword.split()) > 1 and _has(text, keyword))
        if score > best_score:
            best_score = score
            best_intent = intent

    return best_intent, best_score


def _is_general_explanation(query: str) -> bool:
    text = f" {(query or '').lower().strip()} "
    return any(marker in text for marker in _GENERAL_EXPLANATION_MARKERS)


def _is_personal(query: str) -> bool:
    text = f" {(query or '').lower().strip()} "
    return any(marker in text for marker in _PERSONAL_MARKERS)


def _wants_guidance(query: str, role: str, intent: str) -> bool:
    """Decide whether a record intent is really a product-help question."""
    if intent in {"verification", "help"}:
        return True

    text = (query or "").lower()

    # "How does the anomaly engine work?" is documentation, not a data dump.
    if intent in {"anomalies", "campus_stats", "national_stats"}:
        return any(
            marker in text
            for marker in ("how does", "how do", "what is", "what are", "explain", "guide")
        ) and not any(
            marker in text
            for marker in (
                "how many",
                "how much",
                "show",
                "total",
                "current",
                "count",
                "number",
                "metric",
                "statistic",
                "rate",
            )
        )

    # Teachers and administrators asking "how do I mark attendance?" want help.
    if role in INSTITUTION_STAFF_ROLES and intent in {"attendance", "results", "timetable"}:
        return _is_general_explanation(query) and not _is_personal(query)

    # A student asking "what is an APAAR ID?" wants the concept, not their card.
    if intent == "id_card" and any(
        marker in text for marker in ("what is", "what are", "explain", "tell me about")
    ):
        return True

    return False


def _is_national(principal: Principal) -> bool:
    return principal.role in NATIONAL_ROLES


def _is_staff(principal: Principal) -> bool:
    return principal.role in INSTITUTION_STAFF_ROLES or _is_national(principal)


def _mask_apaar(value: Optional[str]) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "not linked"
    tail = raw[-4:] if len(raw) >= 4 else raw
    return f"****-****-{tail}"


def _iso(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _result(
    *,
    reply: str,
    actions: List[Dict[str, str]],
    source: str,
    confidence: float,
    intent: str,
    language: str,
    grounded: bool,
    data: Optional[Dict[str, Any]] = None,
    citations: Optional[List[Dict[str, str]]] = None,
    followups: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "reply": reply,
        "actions": actions,
        "source": source,
        "confidence": confidence,
        "intent": intent,
        "language": language,
        "grounded": grounded,
        "data": data,
        "citations": citations or [],
        "followups": followups or [],
    }


def _sign_in_required(intent: str, language: str) -> Dict[str, Any]:
    return _result(
        reply=_t(
            language,
            "That answer depends on your own academic record, so I need you to sign in first. "
            "I will only read the record your account is allowed to see.",
            "यह उत्तर आपके अपने शैक्षणिक रिकॉर्ड पर निर्भर करता है, इसलिए पहले साइन इन करें। "
            "मैं केवल वही रिकॉर्ड पढ़ूंगा जिसे आपका खाता देख सकता है।",
            "ଏହି ଉତ୍ତର ଆପଣଙ୍କ ନିଜ ଶୈକ୍ଷିକ ରେକର୍ଡ ଉପରେ ନିର୍ଭର କରେ, ତେଣୁ ପ୍ରଥମେ ସାଇନ୍ ଇନ୍ କରନ୍ତୁ। "
            "ମୁଁ କେବଳ ସେହି ରେକର୍ଡ ପଢ଼ିବି ଯାହା ଆପଣଙ୍କ ଖାତା ଦେଖିପାରିବ।",
        ),
        actions=[
            {"label": "Sign in", "url": "/login"},
            {"label": "Explore the platform", "url": "/"},
        ],
        source="ChhatraLekha privacy policy",
        confidence=0.95,
        intent=intent,
        language=language,
        grounded=False,
        followups=["How do I create an account?", "What is an APAAR ID?"],
    )


def _not_linked(intent: str, language: str) -> Dict[str, Any]:
    return _result(
        reply=_t(
            language,
            "Your account is not linked to a student record yet, so I cannot read attendance, "
            "results or a card for you. Your institution can issue a one-time claim code, or an "
            "administrator can attach the record to your account.",
            "आपका खाता अभी किसी छात्र रिकॉर्ड से जुड़ा नहीं है, इसलिए मैं आपके लिए उपस्थिति, परिणाम "
            "या कार्ड नहीं पढ़ सकता। आपका संस्थान वन-टाइम क्लेम कोड दे सकता है, या प्रशासक रिकॉर्ड जोड़ सकता है।",
            "ଆପଣଙ୍କ ଖାତା ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି ଛାତ୍ର ରେକର୍ଡ ସହ ଯୋଡ଼ାଯାଇନାହିଁ, ତେଣୁ ମୁଁ ଆପଣଙ୍କ ପାଇଁ ଉପସ୍ଥାନ, "
            "ଫଳାଫଳ କିମ୍ବା କାର୍ଡ ପଢ଼ିପାରିବି ନାହିଁ। ଆପଣଙ୍କ ଅନୁଷ୍ଠାନ ଏକ ୱାନ୍-ଟାଇମ୍ କ୍ଲେମ୍ କୋଡ୍ ଦେଇପାରେ।",
        ),
        actions=[
            {"label": "Student portal", "url": "/me"},
            {"label": "Help centre", "url": "/help"},
        ],
        source="ChhatraLekha student portal",
        confidence=0.9,
        intent=intent,
        language=language,
        grounded=False,
        followups=["How do I claim my student record?", "What is an APAAR ID?"],
    )


def _not_permitted(intent: str, language: str) -> Dict[str, Any]:
    return _result(
        reply=_t(
            language,
            "Your role can verify credentials but cannot read student records. "
            "I will not bypass that boundary for you.",
            "आपकी भूमिका क्रेडेंशियल सत्यापित कर सकती है, लेकिन छात्र रिकॉर्ड नहीं पढ़ सकती। "
            "मैं आपके लिए यह सीमा नहीं तोड़ूंगा।",
            "ଆପଣଙ୍କ ଭୂମିକା ପ୍ରମାଣପତ୍ର ଯାଞ୍ଚ କରିପାରିବ, କିନ୍ତୁ ଛାତ୍ର ରେକର୍ଡ ପଢ଼ିପାରିବ ନାହିଁ। "
            "ମୁଁ ଆପଣଙ୍କ ପାଇଁ ଏହି ସୀମା ଭାଙ୍ଗିବି ନାହିଁ।",
        ),
        actions=[
            {"label": "Verify a credential", "url": "/verify"},
            {"label": "Help centre", "url": "/help"},
        ],
        source="ChhatraLekha access control",
        confidence=0.95,
        intent=intent,
        language=language,
        grounded=False,
        followups=["How do I verify a credential token?", "What data is exposed during verification?"],
    )


def _no_scope(language: str, intent: str) -> Dict[str, Any]:
    return _result(
        reply=_t(
            language,
            "Your account is not attached to an institution yet, so I cannot read campus records. "
            "Ask an administrator to attach your account; I will not guess which campus you mean.",
            "आपका खाता अभी किसी संस्थान से जुड़ा नहीं है, इसलिए मैं परिसर के रिकॉर्ड नहीं पढ़ सकता। "
            "किसी प्रशासक से अपना खाता जोड़ने को कहें; मैं अनुमान नहीं लगाऊंगा।",
            "ଆପଣଙ୍କ ଖାତା ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି ଅନୁଷ୍ଠାନ ସହ ଯୋଡ଼ାଯାଇନାହିଁ, ତେଣୁ ମୁଁ କ୍ୟାମ୍ପସ୍ ରେକର୍ଡ ପଢ଼ିପାରିବି ନାହିଁ। "
            "ଜଣେ ପ୍ରଶାସକଙ୍କୁ ଆପଣଙ୍କ ଖାତା ଯୋଡ଼ିବାକୁ କୁହନ୍ତୁ; ମୁଁ ଅନୁମାନ କରିବି ନାହିଁ।",
        ),
        actions=[{"label": "Profile", "url": "/profile"}],
        source="ChhatraLekha access control",
        confidence=0.9,
        intent=intent,
        language=language,
        grounded=False,
        followups=["How do I link my institution?", "What can the assistant read?"],
    )


async def _resolve_students(
    db: AsyncIOMotorDatabase, principal: Principal
) -> List[Dict[str, Any]]:
    """Resolve the student records the caller may read, and only those."""
    apaar_ids: List[str] = []

    if principal.role == "student":
        own = principal.apaar_id or (principal.user or {}).get("apaar_id")
        if own:
            apaar_ids.append(str(own))
    elif principal.role == "parent":
        links = await db["guardian_relationships"].find(
            {
                "parent_user_id": principal.subject,
                "status": "VERIFIED",
            }
        ).to_list(20)
        apaar_ids.extend(str(link.get("student_id")) for link in links if link.get("student_id"))
        ward = (principal.user or {}).get("ward_apaar_id")
        if ward:
            apaar_ids.append(str(ward))

    # De-duplicate while preserving order.
    unique_ids = list(dict.fromkeys(apaar_ids))
    if not unique_ids:
        return []

    rows = await db["students"].find({"apaar_id": {"$in": unique_ids}}).to_list(50)
    by_id = {str(row.get("apaar_id")): row for row in rows}
    return [by_id[apaar_id] for apaar_id in unique_ids if apaar_id in by_id]


def _student_scope_label(principal: Principal) -> str:
    return "your verified ward's record" if principal.role == "parent" else "your own record"


def _scope_institution_id(principal: Principal) -> Optional[str]:
    """``None`` means "all institutions" for a national role."""
    if _is_national(principal):
        return None
    return principal.institution_id or ""


async def _handle_attendance(
    db: AsyncIOMotorDatabase, principal: Principal, language: str
) -> Dict[str, Any]:
    students = await _resolve_students(db, principal)
    if principal.role in {"student", "parent"} and not students:
        return _not_linked("attendance", language)

    if students:
        entries: List[Dict[str, Any]] = []
        for student in students:
            student_id = student.get("apaar_id")
            records = (
                await db["attendance_records"]
                .find({"student_id": student_id})
                .sort("session_date", -1)
                .to_list(500)
            )
            total = len(records)
            present = sum(1 for row in records if row.get("status") in {"PRESENT", "LATE"})
            absent = sum(1 for row in records if row.get("status") == "ABSENT")
            excused = sum(1 for row in records if row.get("status") == "EXCUSED")
            rate = round(present / total * 100, 1) if total else None
            entries.append(
                {
                    "student_name": student.get("student_name", ""),
                    "student_ref": _mask_apaar(student_id),
                    "total_sessions": total,
                    "present_sessions": present,
                    "absent_sessions": absent,
                    "excused_sessions": excused,
                    "attendance_rate": rate,
                    "recent": [
                        {
                            "date": row.get("session_date", ""),
                            "status": row.get("status", ""),
                            "class": row.get("target_label", ""),
                        }
                        for row in records[:5]
                    ],
                }
            )

        with_data = [entry for entry in entries if entry["total_sessions"] > 0]
        if not with_data:
            names = ", ".join(entry["student_name"] or entry["student_ref"] for entry in entries)
            return _result(
                reply=_t(
                    language,
                    f"I could not find any attendance sessions recorded for {names} yet. "
                    "I will not guess a percentage. Once a teacher records a session it will appear here.",
                    f"{names} के लिए अभी कोई उपस्थिति सत्र दर्ज नहीं मिला। "
                    "मैं प्रतिशत का अनुमान नहीं लगाऊंगा। शिक्षक द्वारा सत्र दर्ज करने पर वह यहां दिखेगा।",
                    f"{names} ପାଇଁ ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି ଉପସ୍ଥାନ ସେସନ୍ ରେକର୍ଡ ମିଳିଲା ନାହିଁ। "
                    "ମୁଁ ଶତକଡ଼ା ଅନୁମାନ କରିବି ନାହିଁ। ଶିକ୍ଷକ ସେସନ୍ ରେକର୍ଡ କଲେ ଏହା ଏଠାରେ ଦେଖାଯିବ।",
                ),
                actions=_attendance_actions(principal),
                source="ChhatraLekha attendance register",
                confidence=0.9,
                intent="attendance",
                language=language,
                grounded=False,
                data={"kind": "attendance", "students": entries},
                citations=[
                    {
                        "label": "Attendance register (no sessions found)",
                        "collection": "attendance_records",
                        "scope": _student_scope_label(principal),
                    }
                ],
                followups=["Where is my timetable?", "Show my latest results"],
            )

        if len(with_data) == 1:
            entry = with_data[0]
            reply = _t(
                language,
                f"{entry['student_name'] or 'You'} attended {entry['present_sessions']} of "
                f"{entry['total_sessions']} recorded sessions - {entry['attendance_rate']}%. "
                f"{entry['absent_sessions']} session(s) were marked absent.",
                f"{entry['student_name'] or 'आप'} ने {entry['total_sessions']} दर्ज सत्रों में से "
                f"{entry['present_sessions']} में उपस्थिति दी - {entry['attendance_rate']}%. "
                f"{entry['absent_sessions']} सत्र अनुपस्थित रहे।",
                f"{entry['student_name'] or 'ଆପଣ'} {entry['total_sessions']} ଟି ରେକର୍ଡ ସେସନ୍ ମଧ୍ୟରୁ "
                f"{entry['present_sessions']} ଟିରେ ଉପସ୍ଥିତ ଥିଲେ - {entry['attendance_rate']}%. "
                f"{entry['absent_sessions']} ଟି ସେସନରେ ଅନୁପସ୍ଥିତ ଥିଲେ।",
            )
        else:
            lines = [
                f"- {entry['student_name'] or entry['student_ref']}: "
                f"{entry['attendance_rate']}% ({entry['present_sessions']}/{entry['total_sessions']})"
                for entry in with_data
            ]
            reply = _t(
                language,
                "Here is the attendance I am allowed to show you:\n" + "\n".join(lines),
                "यहां वह उपस्थिति है जिसे दिखाने की मुझे अनुमति है:\n" + "\n".join(lines),
                "ଏଠାରେ ସେହି ଉପସ୍ଥାନ ଅଛି ଯାହା ଦେଖାଇବାକୁ ମୋତେ ଅନୁମତି ଅଛି:\n" + "\n".join(lines),
            )

        return _result(
            reply=reply,
            actions=_attendance_actions(principal),
            source="ChhatraLekha attendance register",
            confidence=0.95,
            intent="attendance",
            language=language,
            grounded=True,
            data={"kind": "attendance", "students": with_data},
            citations=[
                {
                    "label": "Attendance register",
                    "collection": "attendance_records",
                    "scope": _student_scope_label(principal),
                }
            ],
            followups=["Show my latest results", "What notices are there for me?"],
        )

    # Staff and national views are aggregates only - never individual students.
    if not _is_staff(principal):
        return _not_permitted("attendance", language)

    institution_id = _scope_institution_id(principal)
    if institution_id == "":
        return _no_scope(language, "attendance")

    query: Dict[str, Any] = {}
    if institution_id:
        query["institution_id"] = institution_id
    if principal.role == "teacher":
        assignments = await db["teacher_assignments"].find(
            {"teacher_id": principal.subject}
        ).to_list(100)
        target_ids = [row.get("target_id") for row in assignments if row.get("target_id")]
        if not target_ids:
            return _result(
                reply=_t(
                    language,
                    "You have no class assignments yet, so there is no attendance for me to summarise.",
                    "आपके पास अभी कोई कक्षा असाइनमेंट नहीं है, इसलिए सारांश के लिए उपस्थिति नहीं है।",
                    "ଆପଣଙ୍କ ପାଖରେ ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି କ୍ଲାସ୍ ଅସାଇନମେଣ୍ଟ ନାହିଁ, ତେଣୁ ସାରାଂଶ ପାଇଁ ଉପସ୍ଥାନ ନାହିଁ।",
                ),
                actions=[{"label": "Teacher workspace", "url": "/teacher"}],
                source="ChhatraLekha attendance register",
                confidence=0.9,
                intent="attendance",
                language=language,
                grounded=False,
                followups=["Show my teaching assignments", "How do I record attendance?"],
            )
        query["target_id"] = {"$in": target_ids}

    records = await db["attendance_records"].find(query).to_list(5000)
    sessions = await db["attendance_sessions"].count_documents(query)
    total = len(records)
    present = sum(1 for row in records if row.get("status") in {"PRESENT", "LATE"})
    absent = sum(1 for row in records if row.get("status") == "ABSENT")
    rate = round(present / total * 100, 1) if total else None

    if not total:
        return _result(
            reply=_t(
                language,
                "No attendance has been recorded in your scope yet. I will not invent a rate.",
                "आपके दायरे में अभी कोई उपस्थिति दर्ज नहीं हुई है। मैं दर का अनुमान नहीं लगाऊंगा।",
                "ଆପଣଙ୍କ ପରିସରରେ ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି ଉପସ୍ଥାନ ରେକର୍ଡ ହୋଇନାହିଁ। ମୁଁ ହାର ଅନୁମାନ କରିବି ନାହିଁ।",
            ),
            actions=_attendance_actions(principal),
            source="ChhatraLekha attendance register",
            confidence=0.9,
            intent="attendance",
            language=language,
            grounded=False,
            data={
                "kind": "attendance_summary",
                "total_records": 0,
                "present_records": 0,
                "absent_records": 0,
                "attendance_rate": None,
                "session_count": sessions,
            },
            citations=[
                {
                    "label": "Attendance register (no records in scope)",
                    "collection": "attendance_records",
                    "scope": "institution aggregate",
                }
            ],
            followups=["How do I record attendance?", "How many students are enrolled?"],
        )

    return _result(
        reply=_t(
            language,
            f"In the records you can access, {present} of {total} attendance entries are present "
            f"or late - an attendance rate of {rate}%. {absent} entries are absent, across "
            f"{sessions} recorded session(s).",
            f"आपकी पहुंच के रिकॉर्ड में {total} में से {present} उपस्थिति प्रविष्टियां उपस्थित या देर से हैं - "
            f"उपस्थिति दर {rate}%। {absent} प्रविष्टियां अनुपस्थित हैं, कुल {sessions} सत्र दर्ज हैं।",
            f"ଆପଣଙ୍କ ପ୍ରବେଶ ଅଧିକାରରେ ଥିବା ରେକର୍ଡରେ {total} ମଧ୍ୟରୁ {present} ଟି ଉପସ୍ଥିତ କିମ୍ବା ବିଳମ୍ବିତ - "
            f"ଉପସ୍ଥାନ ହାର {rate}%। {absent} ଟି ଅନୁପସ୍ଥିତ, ମୋଟ {sessions} ଟି ସେସନ୍ ରେକର୍ଡ ହୋଇଛି।",
        ),
        actions=_attendance_actions(principal),
        source="ChhatraLekha attendance register",
        confidence=0.95,
        intent="attendance",
        language=language,
        grounded=True,
        data={
            "kind": "attendance_summary",
            "total_records": total,
            "present_records": present,
            "absent_records": absent,
            "attendance_rate": rate,
            "session_count": sessions,
        },
        citations=[
            {
                "label": "Attendance register",
                "collection": "attendance_records",
                "scope": "institution aggregate" if institution_id else "national aggregate",
            }
        ],
        followups=["Show campus statistics", "How many anomalies are flagged?"],
    )


def _attendance_actions(principal: Principal) -> List[Dict[str, str]]:
    if principal.role == "student":
        return [
            {"label": "My attendance", "url": "/me/attendance"},
            {"label": "My timetable", "url": "/me/timetable"},
        ]
    if principal.role == "parent":
        return [{"label": "Parent portal", "url": "/parent"}]
    if principal.role == "teacher":
        return [{"label": "Teacher workspace", "url": "/teacher"}]
    if principal.role in NATIONAL_ROLES:
        return [{"label": "National dashboard", "url": "/dashboard"}]
    return [{"label": "Institution dashboard", "url": "/institution"}]


async def _handle_results(
    db: AsyncIOMotorDatabase, principal: Principal, language: str
) -> Dict[str, Any]:
    students = await _resolve_students(db, principal)
    if principal.role in {"student", "parent"} and not students:
        return _not_linked("results", language)

    if students:
        student_payloads: List[Dict[str, Any]] = []
        for student in students:
            student_id = student.get("apaar_id")
            marks = (
                await db["assessment_marks"]
                .find({"student_id": student_id, "is_published": True})
                .sort("published_at", -1)
                .to_list(100)
            )
            assessment_ids = [row.get("assessment_id") for row in marks if row.get("assessment_id")]
            assessments = await db["assessments"].find(
                {"_id": {"$in": assessment_ids}, "status": "PUBLISHED"}
            ).to_list(100)
            by_id = {str(row.get("_id")): row for row in assessments}

            rows: List[Dict[str, Any]] = []
            for mark in marks:
                assessment = by_id.get(str(mark.get("assessment_id")))
                if assessment is None:
                    continue
                rows.append(
                    {
                        "assessment": assessment.get("name", ""),
                        "subject": assessment.get("subject_name", ""),
                        "term": assessment.get("term", ""),
                        "marks_obtained": mark.get("marks_obtained", 0.0),
                        "max_marks": mark.get("max_marks", 100.0),
                        "percentage": mark.get("percentage", 0.0),
                        "grade": mark.get("grade", "N/A"),
                        "status": mark.get("status", ""),
                        "published_at": _iso(mark.get("published_at")),
                    }
                )

            percentages = [float(row["percentage"]) for row in rows]
            average = round(sum(percentages) / len(percentages), 1) if percentages else None
            student_payloads.append(
                {
                    "student_name": student.get("student_name", ""),
                    "student_ref": _mask_apaar(student_id),
                    "result_count": len(rows),
                    "average_percentage": average,
                    "results": rows[:10],
                }
            )

        if not any(payload["result_count"] for payload in student_payloads):
            return _result(
                reply=_t(
                    language,
                    "No results have been published to your account yet. Draft marks are private "
                    "until the institution publishes them, so I will not show or guess them.",
                    "आपके खाते में अभी कोई परिणाम प्रकाशित नहीं हुआ है। संस्थान द्वारा प्रकाशित करने तक "
                    "ड्राफ्ट अंक निजी रहते हैं, इसलिए मैं उन्हें नहीं दिखाऊंगा या अनुमान नहीं लगाऊंगा।",
                    "ଆପଣଙ୍କ ଖାତାରେ ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି ଫଳାଫଳ ପ୍ରକାଶିତ ହୋଇନାହିଁ। ଅନୁଷ୍ଠାନ ପ୍ରକାଶ କରିବା ପର୍ଯ୍ୟନ୍ତ "
                    "ଡ୍ରାଫ୍ଟ ମାର୍କ ଗୋପନୀୟ, ତେଣୁ ମୁଁ ସେଗୁଡ଼ିକ ଦେଖାଇବି ନାହିଁ କିମ୍ବା ଅନୁମାନ କରିବି ନାହିଁ।",
                ),
                actions=_results_actions(principal),
                source="ChhatraLekha published results",
                confidence=0.9,
                intent="results",
                language=language,
                grounded=False,
                data={"kind": "results", "students": student_payloads},
                citations=[
                    {
                        "label": "Published results (none found)",
                        "collection": "assessment_marks",
                        "scope": _student_scope_label(principal),
                    }
                ],
                followups=["What is my attendance?", "What notices are there for me?"],
            )

        with_results = [payload for payload in student_payloads if payload["result_count"]]
        if len(with_results) == 1:
            payload = with_results[0]
            latest = payload["results"][0]
            reply = _t(
                language,
                f"{payload['student_name'] or 'You'} have {payload['result_count']} published result(s), "
                f"with an average of {payload['average_percentage']}%. The latest is "
                f"{latest['subject'] or latest['assessment']}: {latest['marks_obtained']}/"
                f"{latest['max_marks']} ({latest['grade']}).",
                f"{payload['student_name'] or 'आप'} के {payload['result_count']} प्रकाशित परिणाम हैं, "
                f"औसत {payload['average_percentage']}%. नवीनतम: "
                f"{latest['subject'] or latest['assessment']}: {latest['marks_obtained']}/"
                f"{latest['max_marks']} ({latest['grade']}).",
                f"{payload['student_name'] or 'ଆପଣ'}ଙ୍କର {payload['result_count']} ଟି ପ୍ରକାଶିତ ଫଳାଫଳ ଅଛି, "
                f"ହାରାହାରି {payload['average_percentage']}%. ସର୍ବଶେଷ: "
                f"{latest['subject'] or latest['assessment']}: {latest['marks_obtained']}/"
                f"{latest['max_marks']} ({latest['grade']}).",
            )
        else:
            lines = [
                f"- {payload['student_name'] or payload['student_ref']}: "
                f"{payload['result_count']} result(s), average {payload['average_percentage']}%"
                for payload in with_results
            ]
            reply = _t(
                language,
                "Here are the published results I am allowed to show you:\n" + "\n".join(lines),
                "यहां वे प्रकाशित परिणाम हैं जिन्हें दिखाने की मुझे अनुमति है:\n" + "\n".join(lines),
                "ଏଠାରେ ସେହି ପ୍ରକାଶିତ ଫଳାଫଳ ଅଛି ଯାହା ଦେଖାଇବାକୁ ମୋତେ ଅନୁମତି ଅଛି:\n" + "\n".join(lines),
            )

        return _result(
            reply=reply,
            actions=_results_actions(principal),
            source="ChhatraLekha published results",
            confidence=0.95,
            intent="results",
            language=language,
            grounded=True,
            data={"kind": "results", "students": with_results},
            citations=[
                {
                    "label": "Published assessment marks",
                    "collection": "assessment_marks",
                    "scope": _student_scope_label(principal),
                }
            ],
            followups=["What is my attendance?", "Open my digital ID card"],
        )

    if not _is_staff(principal):
        return _not_permitted("results", language)

    institution_id = _scope_institution_id(principal)
    if institution_id == "":
        return _no_scope(language, "results")

    query: Dict[str, Any] = {}
    if institution_id:
        query["institution_id"] = institution_id
    marks = await db["assessment_marks"].find({**query, "is_published": True}).to_list(5000)
    assessments = await db["assessments"].count_documents({**query, "status": "PUBLISHED"})
    percentages = [
        float(row.get("percentage", 0.0))
        for row in marks
        if isinstance(row.get("percentage"), (int, float))
    ]
    average = round(sum(percentages) / len(percentages), 1) if percentages else None

    if not marks:
        return _result(
            reply=_t(
                language,
                "No results have been published in your scope yet. I will not fabricate an average.",
                "आपके दायरे में अभी कोई परिणाम प्रकाशित नहीं हुआ है। मैं औसत नहीं गढ़ूंगा।",
                "ଆପଣଙ୍କ ପରିସରରେ ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି ଫଳାଫଳ ପ୍ରକାଶିତ ହୋଇନାହିଁ। ମୁଁ ହାରାହାରି ତିଆରି କରିବି ନାହିଁ।",
            ),
            actions=_results_actions(principal),
            source="ChhatraLekha published results",
            confidence=0.9,
            intent="results",
            language=language,
            grounded=False,
            data={
                "kind": "results_summary",
                "published_assessments": assessments,
                "published_marks": 0,
                "average_percentage": None,
            },
            citations=[
                {
                    "label": "Published assessment marks (none in scope)",
                    "collection": "assessment_marks",
                    "scope": "institution aggregate",
                }
            ],
            followups=["Show campus statistics", "How do I publish results?"],
        )

    return _result(
        reply=_t(
            language,
            f"In your scope there are {assessments} published assessment(s) and "
            f"{len(marks)} published marks, with an average of {average}%.",
            f"आपके दायरे में {assessments} प्रकाशित मूल्यांकन और {len(marks)} प्रकाशित अंक हैं, "
            f"औसत {average}%।",
            f"ଆପଣଙ୍କ ପରିସରରେ {assessments} ଟି ପ୍ରକାଶିତ ମୂଲ୍ୟାଙ୍କନ ଏବଂ {len(marks)} ଟି ପ୍ରକାଶିତ ମାର୍କ ଅଛି, "
            f"ହାରାହାରି {average}%।",
        ),
        actions=_results_actions(principal),
        source="ChhatraLekha published results",
        confidence=0.95,
        intent="results",
        language=language,
        grounded=True,
        data={
            "kind": "results_summary",
            "published_assessments": assessments,
            "published_marks": len(marks),
            "average_percentage": average,
        },
        citations=[
            {
                "label": "Published assessment marks",
                "collection": "assessment_marks",
                "scope": "institution aggregate" if institution_id else "national aggregate",
            }
        ],
        followups=["Show campus statistics", "How many anomalies are flagged?"],
    )


def _results_actions(principal: Principal) -> List[Dict[str, str]]:
    if principal.role == "student":
        return [
            {"label": "My results", "url": "/me/results"},
            {"label": "My academics", "url": "/me/academics"},
        ]
    if principal.role == "parent":
        return [{"label": "Parent portal", "url": "/parent"}]
    if principal.role == "teacher":
        return [{"label": "Assessments", "url": "/assessments"}]
    return [{"label": "Institution dashboard", "url": "/institution"}]


async def _handle_timetable(
    db: AsyncIOMotorDatabase, principal: Principal, language: str
) -> Dict[str, Any]:
    students = await _resolve_students(db, principal)
    if principal.role in {"student", "parent"} and not students:
        return _not_linked("timetable", language)

    assignments: List[Dict[str, Any]] = []
    target_labels: List[str] = []

    if students:
        for student in students:
            institution_id = student.get("institution_id")
            target_ids: List[str] = []
            grade = student.get("grade_level")
            section = student.get("section")
            academic_year = student.get("academic_year")
            if grade and section and academic_year:
                classes = await db["classes"].find(
                    {
                        "institution_id": institution_id,
                        "grade_level": grade,
                        "section": section,
                        "academic_year": academic_year,
                    }
                ).to_list(10)
                target_ids.extend(
                    str(row.get("class_id") or row.get("_id")) for row in classes if row
                )
            if student.get("program_id"):
                target_ids.append(str(student["program_id"]))

            target_ids = list(dict.fromkeys(target_ids))
            if not target_ids:
                continue

            rows = await db["teacher_assignments"].find(
                {"institution_id": institution_id, "target_id": {"$in": target_ids}}
            ).to_list(50)
            for row in rows:
                assignments.append(row)
                if row.get("target_label"):
                    target_labels.append(str(row["target_label"]))
    elif principal.role == "teacher":
        assignments = await db["teacher_assignments"].find(
            {"teacher_id": principal.subject}
        ).to_list(100)
        target_labels = [str(row.get("target_label")) for row in assignments if row.get("target_label")]
    elif _is_staff(principal):
        institution_id = _scope_institution_id(principal)
        if institution_id == "":
            return _no_scope(language, "timetable")
        query: Dict[str, Any] = {"institution_id": institution_id} if institution_id else {}
        assignments = await db["teacher_assignments"].find(query).to_list(500)
        target_labels = [str(row.get("target_label")) for row in assignments if row.get("target_label")]
    else:
        return _not_permitted("timetable", language)

    seen: set[str] = set()
    rows_payload: List[Dict[str, Any]] = []
    for row in assignments:
        key = str(row.get("assignment_id") or row.get("_id") or "")
        if key and key in seen:
            continue
        seen.add(key)
        rows_payload.append(
            {
                "subject": row.get("subject_name", ""),
                "faculty": row.get("teacher_name", ""),
                "class": row.get("target_label", ""),
                "kind": row.get("target_type", ""),
            }
        )

    if not rows_payload:
        return _result(
            reply=_t(
                language,
                "No timetable or subject assignments have been published for you yet. "
                "I could not find a dated period schedule, and I will not invent times.",
                "आपके लिए अभी कोई टाइम टेबल या विषय असाइनमेंट प्रकाशित नहीं हुआ है। "
                "मुझे तिथि-आधारित समय सारणी नहीं मिली, और मैं समय नहीं गढ़ूंगा।",
                "ଆପଣଙ୍କ ପାଇଁ ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି ଟାଇମ୍ ଟେବୁଲ୍ କିମ୍ବା ବିଷୟ ଅସାଇନମେଣ୍ଟ ପ୍ରକାଶିତ ହୋଇନାହିଁ। "
                "ମୁଁ ତାରିଖ ଆଧାରିତ ସମୟ ସାରଣୀ ପାଇଲି ନାହିଁ, ଏବଂ ସମୟ ତିଆରି କରିବି ନାହିଁ।",
            ),
            actions=_timetable_actions(principal),
            source="ChhatraLekha academic setup",
            confidence=0.9,
            intent="timetable",
            language=language,
            grounded=False,
            data={"kind": "assignments", "assignments": []},
            citations=[
                {
                    "label": "No published timetable found",
                    "collection": "teacher_assignments",
                    "scope": _student_scope_label(principal) if students else "institution",
                }
            ],
            followups=["What subjects are assigned to my class?", "How is my attendance?"],
        )

    subjects = list(dict.fromkeys(row["subject"] for row in rows_payload if row["subject"]))
    reply = _t(
        language,
        "A dated period timetable has not been published yet, so I will not invent times. "
        "These are the subject and faculty assignments I can see: "
        + ", ".join(subjects[:8])
        + ".",
        "तिथि-आधारित समय सारणी अभी प्रकाशित नहीं हुई है, इसलिए मैं समय नहीं गढ़ूंगा। "
        "ये विषय और शिक्षक असाइनमेंट मुझे दिखाई देते हैं: "
        + ", ".join(subjects[:8])
        + "।",
        "ତାରିଖ ଆଧାରିତ ସମୟ ସାରଣୀ ଏପର୍ଯ୍ୟନ୍ତ ପ୍ରକାଶିତ ହୋଇନାହିଁ, ତେଣୁ ମୁଁ ସମୟ ତିଆରି କରିବି ନାହିଁ। "
        "ଏହି ବିଷୟ ଏବଂ ଶିକ୍ଷକ ଅସାଇନମେଣ୍ଟ ମୁଁ ଦେଖିପାରୁଛି: "
        + ", ".join(subjects[:8])
        + "।",
    )

    return _result(
        reply=reply,
        actions=_timetable_actions(principal),
        source="ChhatraLekha academic setup",
        confidence=0.9,
        intent="timetable",
        language=language,
        grounded=True,
        data={"kind": "assignments", "assignments": rows_payload[:15]},
        citations=[
            {
                "label": "Teaching assignments (no dated periods published)",
                "collection": "teacher_assignments",
                "scope": _student_scope_label(principal) if students else "institution",
            }
        ],
        followups=["How is my attendance?", "Show my latest results"],
    )


def _timetable_actions(principal: Principal) -> List[Dict[str, str]]:
    if principal.role == "student":
        return [{"label": "My timetable", "url": "/me/timetable"}]
    if principal.role == "parent":
        return [{"label": "Parent portal", "url": "/parent"}]
    if principal.role == "teacher":
        return [{"label": "Teacher workspace", "url": "/teacher"}]
    return [{"label": "Academic setup", "url": "/academic"}]


async def _handle_notices(
    db: AsyncIOMotorDatabase, principal: Principal, language: str
) -> Dict[str, Any]:
    students = await _resolve_students(db, principal)
    if principal.role in {"student", "parent"} and not students:
        return _not_linked("notices", language)

    institution_ids = {
        student.get("institution_id")
        for student in students
        if student.get("institution_id")
    }
    if principal.institution_id:
        institution_ids.add(principal.institution_id)

    target_ids: set[str] = set()
    for student in students:
        if student.get("program_id"):
            target_ids.add(str(student["program_id"]))
        if student.get("grade_level") and student.get("section") and student.get("academic_year"):
            class_id = (
                f"CLS-{student.get('institution_id')}-"
                f"{str(student['grade_level']).replace(' ', '_').upper()}-"
                f"{str(student['section']).upper()}-"
                f"{str(student['academic_year']).replace('/', '-')}"
            )
            target_ids.add(class_id)

    if _is_national(principal):
        query: Dict[str, Any] = {}
    else:
        if not institution_ids:
            return _no_scope(language, "notices")
        query = {"institution_id": {"$in": list(institution_ids)}}

    notices = await db["announcements"].find(query).sort("published_at", -1).to_list(50)
    visible: List[Dict[str, Any]] = []
    for notice in notices:
        scope = str(notice.get("target_scope", "ALL"))
        target_role = notice.get("target_role")
        target_id = notice.get("target_id")
        if scope != "ALL":
            if target_role and target_role != principal.role:
                continue
            if target_id and target_ids and target_id not in target_ids:
                continue
        visible.append(
            {
                "title": notice.get("title", ""),
                "priority": notice.get("priority", "NORMAL"),
                "published_at": _iso(notice.get("published_at")),
                "target": notice.get("target_label") or scope,
                "snippet": str(notice.get("content", ""))[:180],
            }
        )
        if len(visible) >= 5:
            break

    if not visible:
        return _result(
            reply=_t(
                language,
                "No notices have been published for you yet. When your institution posts one, "
                "it will appear here.",
                "आपके लिए अभी कोई सूचना प्रकाशित नहीं हुई है। संस्थान द्वारा सूचना जारी करने पर वह यहां दिखेगी।",
                "ଆପଣଙ୍କ ପାଇଁ ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି ସୂଚନା ପ୍ରକାଶିତ ହୋଇନାହିଁ। ଅନୁଷ୍ଠାନ ସୂଚନା ଦେଲେ ଏହା ଏଠାରେ ଦେଖାଯିବ।",
            ),
            actions=[{"label": "Announcements", "url": "/announcements"}],
            source="ChhatraLekha notice board",
            confidence=0.9,
            intent="notices",
            language=language,
            grounded=False,
            data={"kind": "notices", "notices": []},
            citations=[
                {
                    "label": "Notice board (none in scope)",
                    "collection": "announcements",
                    "scope": "institution",
                }
            ],
            followups=["What is my attendance?", "Show my latest results"],
        )

    top = visible[0]
    return _result(
        reply=_t(
            language,
            f"You have {len(visible)} recent notice(s). The latest is "
            f"\"{top['title']}\" ({top['priority']}).",
            f"आपके लिए {len(visible)} हालिया सूचना(एं) हैं। नवीनतम \"{top['title']}\" "
            f"({top['priority']}) है।",
            f"ଆପଣଙ୍କ ପାଇଁ {len(visible)} ଟି ସାମ୍ପ୍ରତିକ ସୂଚନା ଅଛି। ସର୍ବଶେଷ \"{top['title']}\" "
            f"({top['priority']})।",
        ),
        actions=[{"label": "Announcements", "url": "/announcements"}],
        source="ChhatraLekha notice board",
        confidence=0.95,
        intent="notices",
        language=language,
        grounded=True,
        data={"kind": "notices", "notices": visible},
        citations=[
            {
                "label": "Targeted announcements",
                "collection": "announcements",
                "scope": "your institution and class",
            }
        ],
        followups=["Show my latest results", "How is my attendance?"],
    )


async def _handle_id_card(
    db: AsyncIOMotorDatabase, principal: Principal, language: str
) -> Dict[str, Any]:
    if principal.role not in {"student", "parent"}:
        return _not_permitted("id_card", language)

    students = await _resolve_students(db, principal)
    if not students:
        return _result(
            reply=_t(
                language,
                "Your account is not linked to a student record yet, so there is no APAAR card "
                "for me to show. The student portal explains how to claim your record with a "
                "one-time code from your institution.",
                "आपका खाता अभी किसी छात्र रिकॉर्ड से जुड़ा नहीं है, इसलिए दिखाने के लिए कोई अपार कार्ड नहीं है। "
                "छात्र पोर्टल बताता है कि संस्थान से मिले वन-टाइम कोड से रिकॉर्ड कैसे जोड़ें।",
                "ଆପଣଙ୍କ ଖାତା ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି ଛାତ୍ର ରେକର୍ଡ ସହ ଯୋଡ଼ାଯାଇନାହିଁ, ତେଣୁ ଦେଖାଇବାକୁ କୌଣସି ଅପାର୍ କାର୍ଡ ନାହିଁ। "
                "ଛାତ୍ର ପୋର୍ଟାଲ୍ ଅନୁଷ୍ଠାନରୁ ମିଳିଥିବା ୱାନ୍-ଟାଇମ୍ କୋଡ୍ ସହ ରେକର୍ଡ ଯୋଡ଼ିବା ବିଷୟରେ କୁହେ।",
            ),
            actions=[{"label": "Student portal", "url": "/me"}, {"label": "Help centre", "url": "/help"}],
            source="ChhatraLekha student portal",
            confidence=0.9,
            intent="id_card",
            language=language,
            grounded=False,
            followups=["How do I claim my student record?", "What is an APAAR ID?"],
        )

    payloads: List[Dict[str, Any]] = []
    for student in students:
        institution = await db["institutions"].find_one(
            {"institution_id": student.get("institution_id")}
        ) or {}
        programme = await db["programmes"].find_one(
            {"program_id": student.get("program_id")}
        ) or {}
        payloads.append(
            {
                "student_name": student.get("student_name", ""),
                "apaar_masked": _mask_apaar(student.get("apaar_id")),
                "record_status": student.get("record_status", "UNKNOWN"),
                "institution": institution.get("name", student.get("institution_id", "")),
                "programme": programme.get("program_name", student.get("program_id", "")),
                "academic_year": student.get("academic_year", ""),
            }
        )

    return _result(
        reply=_t(
            language,
            "Your APAAR ID ends in " + payloads[0]["apaar_masked"].split("-")[-1]
            + f", and your record status is {payloads[0]['record_status']}. "
            "Open the digital ID card to see the full credential and its expiring QR token. "
            "I do not expose the full APAAR ID in chat.",
            "आपका अपार आईडी " + payloads[0]["apaar_masked"].split("-")[-1]
            + f" पर समाप्त होता है, और आपकी रिकॉर्ड स्थिति {payloads[0]['record_status']} है। "
            "पूरा क्रेडेंशियल और उसका समय-सीमित क्यूआर टोकन देखने के लिए डिजिटल आईडी कार्ड खोलें। "
            "मैं चैट में पूरा अपार आईडी नहीं दिखाता।",
            "ଆପଣଙ୍କ ଅପାର୍ ଆଇଡି " + payloads[0]["apaar_masked"].split("-")[-1]
            + f" ରେ ଶେଷ ହେଉଛି, ଏବଂ ଆପଣଙ୍କ ରେକର୍ଡ ସ୍ଥିତି {payloads[0]['record_status']}। "
            "ପୂର୍ଣ୍ଣ ପ୍ରମାଣପତ୍ର ଏବଂ ସମୟସୀମିତ QR ଟୋକେନ୍ ଦେଖିବାକୁ ଡିଜିଟାଲ୍ ଆଇଡି କାର୍ଡ ଖୋଲନ୍ତୁ। "
            "ମୁଁ ଚାଟରେ ପୂର୍ଣ୍ଣ ଅପାର୍ ଆଇଡି ଦେଖାଏ ନାହିଁ।",
        ),
        actions=[
            {"label": "Open digital ID card", "url": "/me/id-card"},
            {"label": "Credential wallet", "url": "/wallet"},
        ],
        source="ChhatraLekha student record",
        confidence=0.95,
        intent="id_card",
        language=language,
        grounded=True,
        data={"kind": "id_card", "students": payloads},
        citations=[
            {
                "label": "Student record (APAAR masked)",
                "collection": "students",
                "scope": _student_scope_label(principal),
            }
        ],
        followups=["How do I share a verified credential?", "Show my latest results"],
    )


async def _handle_anomalies(
    db: AsyncIOMotorDatabase, principal: Principal, language: str
) -> Dict[str, Any]:
    if not _is_staff(principal):
        return _not_permitted("anomalies", language)

    institution_id = _scope_institution_id(principal)
    if institution_id == "":
        return _no_scope(language, "anomalies")

    query: Dict[str, Any] = {"institution_id": institution_id} if institution_id else {}
    anomalies = await db["anomalies"].find(query).to_list(5000)
    if not anomalies:
        return _result(
            reply=_t(
                language,
                "No anomalies are currently flagged in your scope. That is a real zero, not a guess.",
                "आपके दायरे में अभी कोई विसंगति चिह्नित नहीं है। यह वास्तविक शून्य है, अनुमान नहीं।",
                "ଆପଣଙ୍କ ପରିସରରେ ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି ଅନିୟମିତତା ଚିହ୍ନଟ ହୋଇନାହିଁ। ଏହା ପ୍ରକୃତ ଶୂନ୍ୟ, ଅନୁମାନ ନୁହେଁ।",
            ),
            actions=[{"label": "Anomaly inspector", "url": "/anomalies"}],
            source="ChhatraLekha anomaly engine",
            confidence=0.95,
            intent="anomalies",
            language=language,
            grounded=True,
            data={"kind": "anomalies", "total": 0, "by_severity": {}, "top_types": []},
            citations=[
                {
                    "label": "Anomaly register",
                    "collection": "anomalies",
                    "scope": "institution" if institution_id else "national",
                }
            ],
            followups=["Show campus statistics", "How does anomaly detection work?"],
        )

    by_severity: Dict[str, int] = {}
    by_type: Dict[str, int] = {}
    for anomaly in anomalies:
        severity = str(anomaly.get("severity", "UNKNOWN"))
        anomaly_type = str(anomaly.get("anomaly_type", "UNKNOWN"))
        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_type[anomaly_type] = by_type.get(anomaly_type, 0) + 1

    top_types = sorted(by_type.items(), key=lambda item: item[1], reverse=True)[:5]
    critical = by_severity.get("CRITICAL", 0)
    reply = _t(
        language,
        f"There are {len(anomalies)} flagged anomal(ies) in your scope, {critical} of them critical. "
        "The most common types are "
        + ", ".join(f"{name} ({count})" for name, count in top_types)
        + ".",
        f"आपके दायरे में {len(anomalies)} विसंगति(यां) चिह्नित हैं, जिनमें {critical} गंभीर हैं। "
        "सबसे सामान्य प्रकार हैं "
        + ", ".join(f"{name} ({count})" for name, count in top_types)
        + "।",
        f"ଆପଣଙ୍କ ପରିସରରେ {len(anomalies)} ଟି ଅନିୟମିତତା ଚିହ୍ନଟ ହୋଇଛି, ସେଥିମଧ୍ୟରୁ {critical} ଟି ଗୁରୁତର। "
        "ସର୍ବାଧିକ ସାଧାରଣ ପ୍ରକାରଗୁଡ଼ିକ ହେଉଛି "
        + ", ".join(f"{name} ({count})" for name, count in top_types)
        + "।",
    )

    return _result(
        reply=reply,
        actions=[{"label": "Anomaly inspector", "url": "/anomalies"}],
        source="ChhatraLekha anomaly engine",
        confidence=0.95,
        intent="anomalies",
        language=language,
        grounded=True,
        data={
            "kind": "anomalies",
            "total": len(anomalies),
            "by_severity": by_severity,
            "top_types": [{"type": name, "count": count} for name, count in top_types],
        },
        citations=[
            {
                "label": "Anomaly register",
                "collection": "anomalies",
                "scope": "institution" if institution_id else "national",
            }
        ],
        followups=["Show campus statistics", "How do I review an anomaly case?"],
    )


async def _handle_campus_stats(
    db: AsyncIOMotorDatabase, principal: Principal, language: str
) -> Dict[str, Any]:
    if not _is_staff(principal):
        return _not_permitted("campus_stats", language)

    institution_id = _scope_institution_id(principal)
    if institution_id == "":
        return _no_scope(language, "campus_stats")

    query: Dict[str, Any] = {"institution_id": institution_id} if institution_id else {}
    students = await db["students"].count_documents(query)
    active = await db["students"].count_documents({**query, "record_status": "ACTIVE"})
    programmes = await db["programmes"].count_documents(query)
    anomalies = await db["anomalies"].count_documents(query)
    sessions = await db["attendance_sessions"].count_documents(query)
    records = await db["attendance_records"].find(query, {"status": 1}).to_list(20000)
    present = sum(1 for row in records if row.get("status") in {"PRESENT", "LATE"})
    rate = round(present / len(records) * 100, 1) if records else None

    scope_label = "your institution" if institution_id else "all institutions"

    return _result(
        reply=_t(
            language,
            f"In {scope_label} there are {students} student record(s), {active} active, "
            f"{programmes} programme(s), {sessions} attendance session(s) and {anomalies} flagged "
            f"anomal(ies). The recorded attendance rate is "
            + (f"{rate}%." if rate is not None else "not available yet."),
            f"{scope_label} में {students} छात्र रिकॉर्ड, {active} सक्रिय, {programmes} कार्यक्रम, "
            f"{sessions} उपस्थिति सत्र और {anomalies} चिह्नित विसंगतियां हैं। दर्ज उपस्थिति दर "
            + (f"{rate}% है।" if rate is not None else "अभी उपलब्ध नहीं है।"),
            f"{scope_label} ରେ {students} ଟି ଛାତ୍ର ରେକର୍ଡ, {active} ଟି ସକ୍ରିୟ, {programmes} ଟି କାର୍ଯ୍ୟକ୍ରମ, "
            f"{sessions} ଟି ଉପସ୍ଥାନ ସେସନ୍ ଏବଂ {anomalies} ଟି ଚିହ୍ନଟ ଅନିୟମିତତା ଅଛି। ରେକର୍ଡ ହୋଇଥିବା ଉପସ୍ଥାନ ହାର "
            + (f"{rate}%." if rate is not None else "not available yet."),
        ),
        actions=[
            {"label": "Institution dashboard", "url": "/institution"},
            {"label": "Student register", "url": "/students"},
        ],
        source="ChhatraLekha campus register",
        confidence=0.95,
        intent="campus_stats",
        language=language,
        grounded=True,
        data={
            "kind": "campus_stats",
            "students": students,
            "active_students": active,
            "programmes": programmes,
            "anomalies": anomalies,
            "attendance_sessions": sessions,
            "attendance_rate": rate,
        },
        citations=[
            {
                "label": "Student, programme and attendance registers",
                "collection": "students, programmes, attendance_records",
                "scope": "institution aggregate" if institution_id else "national aggregate",
            }
        ],
        followups=["How many anomalies are flagged?", "Show published results summary"],
    )


async def _handle_national_stats(
    db: AsyncIOMotorDatabase, principal: Principal, language: str
) -> Dict[str, Any]:
    if principal.role not in NATIONAL_ROLES:
        return _not_permitted("national_stats", language)

    institutions = await db["institutions"].count_documents({})
    programmes = await db["programmes"].count_documents({})
    students = await db["students"].count_documents({})
    active = await db["students"].count_documents({"record_status": "ACTIVE"})
    anomalies = await db["anomalies"].count_documents({})
    critical = await db["anomalies"].count_documents({"severity": "CRITICAL"})

    return _result(
        reply=_t(
            language,
            f"Nationally there are {institutions} institution(s), {programmes} programme(s), "
            f"{students} student record(s) ({active} active) and {anomalies} flagged anomal(ies), "
            f"{critical} of them critical.",
            f"राष्ट्रीय स्तर पर {institutions} संस्थान, {programmes} कार्यक्रम, {students} छात्र रिकॉर्ड "
            f"({active} सक्रिय) और {anomalies} चिह्नित विसंगतियां हैं, जिनमें {critical} गंभीर हैं।",
            f"ଜାତୀୟ ସ୍ତରରେ {institutions} ଟି ଅନୁଷ୍ଠାନ, {programmes} ଟି କାର୍ଯ୍ୟକ୍ରମ, {students} ଟି ଛାତ୍ର ରେକର୍ଡ "
            f"({active} ଟି ସକ୍ରିୟ) ଏବଂ {anomalies} ଟି ଚିହ୍ନଟ ଅନିୟମିତତା ଅଛି, ସେଥିମଧ୍ୟରୁ {critical} ଟି ଗୁରୁତର।",
        ),
        actions=[
            {"label": "National dashboard", "url": "/dashboard"},
            {"label": "Compliance reports", "url": "/reports"},
        ],
        source="ChhatraLekha national register",
        confidence=0.95,
        intent="national_stats",
        language=language,
        grounded=True,
        data={
            "kind": "national_stats",
            "institutions": institutions,
            "programmes": programmes,
            "students": students,
            "active_students": active,
            "anomalies": anomalies,
            "critical_anomalies": critical,
        },
        citations=[
            {
                "label": "National registry counts",
                "collection": "institutions, programmes, students, anomalies",
                "scope": "all institutions",
            }
        ],
        followups=["How many anomalies are critical?", "Show institution statistics"],
    )


async def build_grounded_response(
    db: AsyncIOMotorDatabase,
    principal: Optional[Principal],
    query: str,
    language: Optional[str] = "en",
) -> Dict[str, Any]:
    """Answer a question from guidance or from the caller's authorised records.

    ``principal`` is the authenticated caller from the session (or ``None``).
    No part of the caller's role, identity or scope is read from the request
    body, which is what makes spoofing a role in the JSON payload useless.
    """
    answer_language = normalize_language(language)
    intent, _ = detect_intent(query)
    role = principal.role if principal else "anonymous"

    if intent in RECORD_INTENTS and principal is None:
        guidance = find_grounded_answer(
            query=query,
            role="student",
            language=answer_language,
            user_context=None,
        )
        sign_in_note = _t(
            answer_language,
            "\n\nSign in to see your own record. I only read what your account is allowed to see.",
            "\n\nअपना रिकॉर्ड देखने के लिए साइन इन करें। मैं केवल वही पढ़ता हूं जिसे आपका खाता देख सकता है।",
            "\n\nନିଜ ରେକର୍ଡ ଦେଖିବାକୁ ସାଇନ୍ ଇନ୍ କରନ୍ତୁ। ମୁଁ କେବଳ ସେହି ପଢ଼େ ଯାହା ଆପଣଙ୍କ ଖାତା ଦେଖିପାରିବ।",
        )
        actions = [{"label": "Sign in", "url": "/login"}] + guidance.get("actions", [])
        return _result(
            reply=guidance["reply"] + sign_in_note,
            actions=actions,
            source=guidance.get("source", "ChhatraLekha knowledge base"),
            confidence=float(guidance.get("confidence", 0.6)),
            intent=intent,
            language=answer_language,
            grounded=False,
            data=None,
            citations=[],
            followups=["What is an APAAR ID?", "How do I claim my student record?"],
        )

    if intent in RECORD_INTENTS and principal is not None:
        if principal.role in {"verifier", "pending"}:
            return _not_permitted(intent, answer_language)
        if _wants_guidance(query, principal.role, intent):
            intent = "help"

    handlers = {
        "attendance": _handle_attendance,
        "results": _handle_results,
        "timetable": _handle_timetable,
        "notices": _handle_notices,
        "id_card": _handle_id_card,
        "anomalies": _handle_anomalies,
        "campus_stats": _handle_campus_stats,
        "national_stats": _handle_national_stats,
    }

    handler = handlers.get(intent)
    if handler is not None:
        return await handler(db, principal, answer_language)  # type: ignore[arg-type]

    # Everything else is documentation. The knowledge base is deliberately
    # small and reviewed, so an unknown question gets an honest redirect.
    guidance = find_grounded_answer(
        query=query,
        role=role if role != "anonymous" else "student",
        language=answer_language,
        user_context=None,
    )
    return _result(
        reply=guidance["reply"],
        actions=guidance.get("actions", []),
        source=guidance.get("source", "ChhatraLekha knowledge base"),
        confidence=float(guidance.get("confidence", 0.6)),
        intent=intent or "help",
        language=answer_language,
        grounded=False,
        data=None,
        citations=[],
        followups=get_quick_prompts_for_role(
            role if role != "anonymous" else "student"
        )[:3],
    )
