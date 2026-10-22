package com.acadentrix.core.voice

/** Fixed, deterministic, non-destructive voice command catalogue. */
object VoiceIntentMatcher {
    enum class Intent { DASHBOARD, INSTITUTIONS, STUDENTS, ANOMALIES, REPORTS, IMPACT, VERIFY, STUDENT_COUNT, ANOMALY_COUNT, OPEN_TASKS, HIGH_ANOMALIES, HELP, STOP, DARK_THEME, LIGHT_THEME }

    private val english = listOf(
        Intent.DASHBOARD to Regex("\\b(open|show|go to) (the )?dashboard\\b", RegexOption.IGNORE_CASE),
        Intent.INSTITUTIONS to Regex("\\b(open|show|go to) institutions?\\b", RegexOption.IGNORE_CASE),
        Intent.STUDENTS to Regex("\\b(open|show|go to) (students?|register)\\b", RegexOption.IGNORE_CASE),
        Intent.ANOMALIES to Regex("\\b(open|show|go to) anomal", RegexOption.IGNORE_CASE),
        Intent.REPORTS to Regex("\\b(open|show|go to) reports?\\b", RegexOption.IGNORE_CASE),
        Intent.IMPACT to Regex("\\b(open|show|go to) (change )?impact\\b", RegexOption.IGNORE_CASE),
        Intent.VERIFY to Regex("\\b(verify record|open verification)\\b", RegexOption.IGNORE_CASE),
        Intent.STUDENT_COUNT to Regex("\\b(how many|number of) students?\\b", RegexOption.IGNORE_CASE),
        Intent.ANOMALY_COUNT to Regex("\\b(how many|number of) anomalies?\\b", RegexOption.IGNORE_CASE),
        Intent.OPEN_TASKS to Regex("\\b(open )?(review )?tasks?\\b", RegexOption.IGNORE_CASE),
        Intent.HIGH_ANOMALIES to Regex("\\bhigh( severity)? anomalies?\\b", RegexOption.IGNORE_CASE),
        Intent.DARK_THEME to Regex("\\b(dark mode|dark theme)\\b", RegexOption.IGNORE_CASE),
        Intent.LIGHT_THEME to Regex("\\b(light mode|light theme)\\b", RegexOption.IGNORE_CASE),
        Intent.HELP to Regex("\\b(help|what can i ask)\\b", RegexOption.IGNORE_CASE),
        Intent.STOP to Regex("\\b(stop|be quiet)\\b", RegexOption.IGNORE_CASE)
    )
    private val hindi = listOf(
        Intent.DASHBOARD to Regex("(डैशबोर्ड|dashboard)"), Intent.STUDENTS to Regex("(विद्यार्थी|छात्र)"),
        Intent.ANOMALIES to Regex("(विसंगति|विसंगतियाँ)"), Intent.VERIFY to Regex("(सत्यापित करें|रिकॉर्ड सत्यापित)"),
        Intent.STUDENT_COUNT to Regex("(कितने छात्र|कितने विद्यार्थी)"), Intent.STOP to Regex("(रुको|बंद करो)"),
        Intent.HELP to Regex("(मदद|क्या पूछ सकता)"), Intent.DARK_THEME to Regex("(डार्क मोड|गहरा मोड)")
    )

    fun match(text: String, language: String = "en"): Intent? {
        val commands = if (language.lowercase().startsWith("hi")) hindi + english else english
        val matched = commands.filter { it.second.containsMatchIn(text.trim().lowercase()) }.map { it.first }.distinct()
        return matched.singleOrNull()
    }
}
