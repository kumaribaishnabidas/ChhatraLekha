import { useCallback, useEffect, useRef, useState } from 'react'

/** Browser Web Speech recognition with feature detection and no audio storage. */
export function useSpeechRecognition(language) {
  const recognitionRef = useRef(null)
  const [supported] = useState(() => Boolean(window.SpeechRecognition || window.webkitSpeechRecognition))
  const [state, setState] = useState('idle')
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState('')

  const stop = useCallback(() => recognitionRef.current?.stop(), [])

  const start = useCallback((onResult) => {
    if (!supported) return
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new Recognition()
    recognition.lang = language
    recognition.continuous = false
    recognition.interimResults = true
    recognition.maxAlternatives = 1
    recognitionRef.current = recognition
    setError('')
    setTranscript('')
    setState('listening')
    recognition.onresult = (event) => {
      const text = Array.from(event.results).map((item) => item[0]?.transcript || '').join(' ').trim()
      setTranscript(text)
      if (event.results[event.results.length - 1]?.isFinal) onResult?.(text)
    }
    recognition.onerror = (event) => {
      const names = { 'not-allowed': 'denied', 'service-not-allowed': 'denied', 'no-speech': 'noSpeech', network: 'network', aborted: 'timeout' }
      setError(names[event.error] || 'timeout')
    }
    recognition.onend = () => setState('idle')
    recognition.start()
  }, [language, supported])

  useEffect(() => () => recognitionRef.current?.abort(), [])
  return { supported, state, transcript, error, start, stop }
}
