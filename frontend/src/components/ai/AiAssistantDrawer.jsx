import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../hooks/useAuth'
import { api } from '../../services/api'

export default function AiAssistantDrawer({ isOpen, onClose }) {
  const { t, i18n } = useTranslation()
  const { user } = useAuth()
  const navigate = useNavigate()

  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [quickPrompts, setQuickPrompts] = useState([])
  const [isListening, setIsListening] = useState(false)
  const [speakingIndex, setSpeakingIndex] = useState(null)

  const messagesEndRef = useRef(null)
  const recognitionRef = useRef(null)

  const userRole = user?.role || 'student'
  const currentLang = i18n.language || 'en'

  // Load tailored quick prompts for current user role
  useEffect(() => {
    let active = true
    api.get(`/ai/prompts?role=${encodeURIComponent(userRole)}`)
      .then((res) => {
        if (active && res.data?.prompts) {
          setQuickPrompts(res.data.prompts)
        }
      })
      .catch(() => {
        if (active) {
          setQuickPrompts([
            'How do I view my timetable?',
            'How do I check attendance?',
            'What is an APAAR ID?',
            'How do I change language?',
          ])
        }
      })
    return () => {
      active = false
    }
  }, [userRole])

  // Initial welcome message
  useEffect(() => {
    if (messages.length === 0) {
      const welcomeText =
        currentLang === 'hi'
          ? 'नमस्ते! मैं छात्रलेखा एआई सहायक हूं। मैं आपकी कैसे सहायता कर सकता हूं?'
          : currentLang === 'or'
          ? 'ନମସ୍କାର! ମୁଁ ଛାତ୍ରଲେଖା AI ସହାୟକ। ମୁଁ ଆପଣଙ୍କୁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?'
          : 'Hello! I am the ChhatraLekha Multilingual AI Assistant. How can I assist you with your academic records, attendance, or institution administration today?'

      setMessages([
        {
          sender: 'assistant',
          text: welcomeText,
          source: 'ChhatraLekha Knowledge Base',
          actions: [
            { label: 'View ID Card', url: '/me/id-card' },
            { label: 'Platform Guide', url: '/help' },
          ],
        },
      ])
    }
  }, [currentLang, messages.length])

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Cleanup speech synthesis on unmount
  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel()
      }
    }
  }, [])

  const sendMessage = async (queryText) => {
    const text = (queryText || input).trim()
    if (!text || loading) return

    const userMessage = { sender: 'user', text }
    setMessages((prev) => [...prev, userMessage])
    if (!queryText) setInput('')
    setLoading(true)

    try {
      const res = await api.post('/ai/chat', {
        message: text,
        role: userRole,
        language: currentLang,
        user_context: {
          name: user?.display_name || user?.name,
          student_id: user?.apaar_id || user?.user_id,
        },
      })

      const replyData = res.data || {}
      const assistantMessage = {
        sender: 'assistant',
        text: replyData.reply || replyData.answer || 'I am ready to help. Please select from the prompts or ask a question.',
        source: replyData.source || 'ChhatraLekha Platform Guide',
        actions: replyData.actions || [],
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: 'Unable to reach the assistant service right now. You can browse the platform documentation directly.',
          source: 'System Offline',
          actions: [{ label: 'Help Center', url: '/help' }],
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  // Voice dictation using Web Speech API
  const toggleListening = () => {
    if (typeof window === 'undefined') return
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use keyboard text input.')
      return
    }

    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = currentLang === 'hi' ? 'hi-IN' : currentLang === 'or' ? 'or-IN' : 'en-IN'
    recognition.continuous = false
    recognition.interimResults = false

    recognition.onstart = () => {
      setIsListening(true)
    }

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      if (transcript) {
        setInput(transcript)
        sendMessage(transcript)
      }
      setIsListening(false)
    }

    recognition.onerror = () => {
      setIsListening(false)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognitionRef.current = recognition
    recognition.start()
  }

  // Text to Speech playback
  const speakText = (text, index) => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return

    if (speakingIndex === index) {
      window.speechSynthesis.cancel()
      setSpeakingIndex(null)
      return
    }

    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = currentLang === 'hi' ? 'hi-IN' : currentLang === 'or' ? 'or-IN' : 'en-IN'

    utterance.onend = () => {
      setSpeakingIndex(null)
    }
    utterance.onerror = () => {
      setSpeakingIndex(null)
    }

    setSpeakingIndex(index)
    window.speechSynthesis.speak(utterance)
  }

  const handleActionClick = (url) => {
    if (url.startsWith('/')) {
      navigate(url)
      onClose()
    } else {
      window.open(url, '_blank', 'noopener,noreferrer')
    }
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 overflow-hidden flex justify-end bg-black/40"
      role="dialog"
      aria-modal="true"
      aria-label="ChhatraLekha AI Assistant"
    >
      <div
        className="w-full max-w-md bg-surface h-full shadow-md flex flex-col border-l border-line transform transition-transform duration-200"
      >
        {/* Header */}
        <div className="px-4 py-3 bg-brand-deep text-white flex items-center justify-between border-b border-navy-deep">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center text-on-accent font-bold">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <div>
              <h2 className="m-0 text-sm font-bold text-white">ChhatraLekha Assistant</h2>
              <p className="m-0 text-[10px] text-white/70">
                Multilingual AI Helper ({currentLang.toUpperCase()})
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded text-white/80 hover:text-white hover:bg-white/10 cursor-pointer"
            aria-label="Close assistant"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-surface-2">
          {messages.map((m, idx) => {
            const isUser = m.sender === 'user'
            return (
              <div
                key={idx}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg p-3 text-xs leading-relaxed ${
                    isUser
                      ? 'bg-brand text-on-brand shadow-xs'
                      : 'bg-surface text-ink border border-line shadow-xs'
                  }`}
                >
                  <p className="m-0 whitespace-pre-wrap">{m.text}</p>

                  {!isUser && (
                    <div className="mt-2 pt-2 border-t border-line/60 flex items-center justify-between gap-2">
                      <span className="text-[10px] text-muted truncate">
                        {m.source}
                      </span>
                      <button
                        type="button"
                        onClick={() => speakText(m.text, idx)}
                        className="text-muted hover:text-brand cursor-pointer p-1 rounded"
                        title={speakingIndex === idx ? 'Stop speaking' : 'Listen to reply'}
                        aria-label="Listen to answer"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          {speakingIndex === idx ? (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                          ) : (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                          )}
                        </svg>
                      </button>
                    </div>
                  )}
                </div>

                {/* Suggested Action Chips */}
                {!isUser && m.actions && m.actions.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {m.actions.map((act, actIdx) => (
                      <button
                        key={actIdx}
                        type="button"
                        onClick={() => handleActionClick(act.url)}
                        className="rounded-full bg-surface border border-line px-2.5 py-1 text-[11px] font-semibold text-brand hover:border-brand cursor-pointer shadow-xs"
                      >
                        {act.label} &rarr;
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )
          })}

          {loading && (
            <div className="flex items-center gap-2 text-muted text-xs p-2">
              <span className="w-2 h-2 rounded-full bg-brand animate-ping" />
              <span>Assistant is retrieving verified guidance...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Prompts Bar */}
        {quickPrompts.length > 0 && (
          <div className="px-3 py-2 bg-surface border-t border-line overflow-x-auto whitespace-nowrap space-x-1.5">
            <span className="text-[10px] font-bold text-muted uppercase tracking-wider block mb-1">
              Suggested Questions
            </span>
            <div className="flex gap-1.5">
              {quickPrompts.slice(0, 4).map((p, pIdx) => (
                <button
                  key={pIdx}
                  type="button"
                  disabled={loading}
                  onClick={() => sendMessage(p)}
                  className="rounded-full bg-surface-2 border border-line px-2.5 py-1 text-[11px] text-ink hover:border-brand cursor-pointer truncate max-w-[200px]"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Text and Voice Input Box */}
        <div className="p-3 bg-surface border-t border-line">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              sendMessage()
            }}
            className="flex items-center gap-2"
          >
            <button
              type="button"
              onClick={toggleListening}
              className={`p-2 rounded-lg border transition-colors cursor-pointer flex-shrink-0 ${
                isListening
                  ? 'bg-danger text-on-danger border-danger animate-pulse'
                  : 'bg-surface text-ink border-line hover:border-brand'
              }`}
              title={isListening ? 'Stop listening' : 'Speak your question'}
              aria-label="Voice input"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                />
              </svg>
            </button>

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about timetable, attendance, ID card, rules..."
              disabled={loading}
              className="flex-1 rounded-lg border border-line bg-surface-2 px-3 py-2 text-xs text-ink focus:outline-none focus:border-brand"
            />

            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="p-2 rounded-lg bg-brand text-on-brand font-semibold hover:bg-brand-deep cursor-pointer disabled:opacity-50 flex-shrink-0"
              aria-label="Send message"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
