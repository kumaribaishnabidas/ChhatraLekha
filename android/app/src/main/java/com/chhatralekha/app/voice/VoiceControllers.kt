package com.chhatralekha.app.voice

import android.content.Context
import android.content.Intent
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import java.util.Locale

/** Device-only speech helpers. They persist neither audio nor transcripts. */
object VoiceControllers {
    fun recognitionIntent(locale: Locale): Intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
        putExtra(RecognizerIntent.EXTRA_LANGUAGE, locale.toLanguageTag())
        putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
        putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
    }

    fun recognitionAvailable(context: Context): Boolean = SpeechRecognizer.isRecognitionAvailable(context)

    /** Returns false when device language data is unavailable; caller can open
     * ACTION_INSTALL_TTS_DATA / system TTS settings after explaining why. */
    fun createTts(context: Context, locale: Locale, onReady: (TextToSpeech?, Boolean) -> Unit) {
        lateinit var tts: TextToSpeech
        tts = TextToSpeech(context.applicationContext) { status ->
            if (status != TextToSpeech.SUCCESS) return@TextToSpeech onReady(null, false)
            val result = tts.setLanguage(locale)
            onReady(tts, result != TextToSpeech.LANG_MISSING_DATA && result != TextToSpeech.LANG_NOT_SUPPORTED)
        }
    }
}
