package com.acadentrix.core.voice

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class VoiceIntentMatcherTest {
    @Test fun `matches English navigation`() = assertEquals(VoiceIntentMatcher.Intent.DASHBOARD, VoiceIntentMatcher.match("open dashboard"))
    @Test fun `matches English count`() = assertEquals(VoiceIntentMatcher.Intent.STUDENT_COUNT, VoiceIntentMatcher.match("how many students"))
    @Test fun `matches Hindi navigation`() = assertEquals(VoiceIntentMatcher.Intent.DASHBOARD, VoiceIntentMatcher.match("डैशबोर्ड खोलें", "hi-IN"))
    @Test fun `matches Hindi stop`() = assertEquals(VoiceIntentMatcher.Intent.STOP, VoiceIntentMatcher.match("रुको", "hi-IN"))
    @Test fun `rejects an unknown command`() = assertNull(VoiceIntentMatcher.match("make a correction now"))
}
