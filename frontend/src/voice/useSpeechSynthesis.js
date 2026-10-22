import { useCallback, useEffect, useState } from 'react'

/** Text to speech. The structured caller constructs the message; this hook never sees raw IDs. */
export function useSpeechSynthesis(language) {
  const [supported] = useState(() => 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window)
  const [voices, setVoices] = useState([])
  const [notice, setNotice] = useState('')

  useEffect(() => {
    if (!supported) return undefined
    const refresh = () => setVoices(window.speechSynthesis.getVoices())
    refresh()
    window.speechSynthesis.addEventListener?.('voiceschanged', refresh)
    return () => window.speechSynthesis.removeEventListener?.('voiceschanged', refresh)
  }, [supported])

  const stop = useCallback(() => supported && window.speechSynthesis.cancel(), [supported])
  const speak = useCallback((text) => {
    if (!supported) return false
    const base = String(language || 'en').split('-')[0].toLowerCase()
    const voice = voices.find((item) => item.lang.toLowerCase().startsWith(base))
    if (!voice && base !== 'en') { setNotice('noVoice'); return false }
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = language
    if (voice) utterance.voice = voice
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utterance)
    setNotice('')
    return true
  }, [language, supported, voices])
  return { supported, notice, speak, stop }
}
