package com.chhatralekha.core.voice

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class VoiceIntentMatcherTest {
    @Test fun `matches English navigation`() = assertEquals(VoiceIntentMatcher.Intent.DASHBOARD, VoiceIntentMatcher.match("open dashboard"))
    @Test fun `matches English count`() = assertEquals(VoiceIntentMatcher.Intent.STUDENT_COUNT, VoiceIntentMatcher.match("how many students"))
    @Test fun `matches English attendance`() = assertEquals(VoiceIntentMatcher.Intent.ATTENDANCE, VoiceIntentMatcher.match("show my attendance"))
    @Test fun `matches English results`() = assertEquals(VoiceIntentMatcher.Intent.RESULTS, VoiceIntentMatcher.match("check my results"))
    @Test fun `matches Hindi navigation`() = assertEquals(VoiceIntentMatcher.Intent.DASHBOARD, VoiceIntentMatcher.match("डैशबोर्ड खोलें", "hi-IN"))
    @Test fun `matches Hindi attendance`() = assertEquals(VoiceIntentMatcher.Intent.ATTENDANCE, VoiceIntentMatcher.match("मेरी उपस्थिति दिखाओ", "hi-IN"))
    @Test fun `matches Hindi stop`() = assertEquals(VoiceIntentMatcher.Intent.STOP, VoiceIntentMatcher.match("रुको", "hi-IN"))
    @Test fun `matches Odia attendance`() = assertEquals(VoiceIntentMatcher.Intent.ATTENDANCE, VoiceIntentMatcher.match("ମୋର ଆଜିର ଉପସ୍ଥାନ ଦେଖାଅ", "or-IN"))
    @Test fun `matches Odia results`() = assertEquals(VoiceIntentMatcher.Intent.RESULTS, VoiceIntentMatcher.match("ମୋର ପରୀକ୍ଷା ଫଳାଫଳ ଦେଖାଅ", "or-IN"))
    @Test fun `rejects an unknown command`() = assertNull(VoiceIntentMatcher.match("make a correction now"))
}
