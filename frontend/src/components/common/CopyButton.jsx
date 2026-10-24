import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useToast } from '../../context/ToastContext'

/**
 * Safely copies text to the clipboard.
 * Crucially, if the input is a raw 12-digit APAAR ID, it masks all digits except
 * the last 4, preventing accidental exposure of synthetic or real identifiers.
 */
export function sanitizeCopyPayload(text) {
  if (!text) return ''
  const trimmed = String(text).trim()
  // Check for raw 12-digit number (with or without dashes)
  const plainDigits = trimmed.replace(/\D/g, '')
  if (plainDigits.length === 12 && (/^\d{12}$/.test(trimmed) || /^\d{4}-\d{4}-\d{4}$/.test(trimmed))) {
    return `****-****-${plainDigits.slice(8)}`
  }
  return trimmed
}

export default function CopyButton({
  text,
  label,
  copiedLabel,
  className = 'btn btn-outline text-xs px-2.5 py-1',
  ariaLabel,
}) {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const [copied, setCopied] = useState(false)

  const defaultLabel = label || t('common.copy', 'Copy')
  const defaultCopied = copiedLabel || t('common.copied', 'Copied')

  async function handleCopy() {
    const payload = sanitizeCopyPayload(text)
    if (!payload) return
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(payload)
      } else {
        const textarea = document.createElement('textarea')
        textarea.value = payload
        textarea.style.position = 'fixed'
        textarea.style.opacity = '0'
        document.body.appendChild(textarea)
        textarea.select()
        document.execCommand('copy')
        document.body.removeChild(textarea)
      }
      setCopied(true)
      addToast(defaultCopied)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      addToast(t('common.copyFailed', 'Failed to copy'))
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      aria-label={ariaLabel || (copied ? defaultCopied : defaultLabel)}
      className={`${className} cursor-pointer`}
    >
      <span aria-live="polite">{copied ? defaultCopied : defaultLabel}</span>
    </button>
  )
}
