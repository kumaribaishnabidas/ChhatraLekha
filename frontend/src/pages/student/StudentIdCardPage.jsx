import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '../../hooks/usePageMeta'
import { api, errorMessage } from '../../services/api'
import { Button, Card, Badge } from '../../components/common'

export default function StudentIdCardPage() {
  const { t } = useTranslation()
  usePageMeta({
    title: t('student.idCard.title', { defaultValue: 'Digital Student ID Card' }),
    description: 'Printable digital student ID card with opaque token verification QR badge.',
  })

  const [card, setCard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showFullApaar, setShowFullApaar] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    async function loadCard() {
      try {
        setLoading(true)
        setError('')
        const { data } = await api.get('/me/id-card')
        setCard(data)
      } catch (err) {
        setError(errorMessage(err, 'Unable to load ID card.'))
      } finally {
        setLoading(false)
      }
    }
    loadCard()
  }, [])

  const handleCopyLink = () => {
    if (!card?.token_url) return
    navigator.clipboard.writeText(card.token_url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handlePrint = () => {
    window.print()
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-[800px] px-5 py-12 flex justify-center">
        <div className="h-96 w-full max-w-[500px] rounded-lg bg-surface-2 animate-pulse" />
      </div>
    )
  }

  if (error || !card) {
    return (
      <div className="mx-auto max-w-[800px] px-5 py-12">
        <Card className="border-danger/30 bg-danger/5 p-6 text-center">
          <p className="m-0 text-sm font-semibold text-danger">{error || 'Unable to load card.'}</p>
        </Card>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-[900px] px-5 py-8 space-y-8">
      {/* Page Header and Controls */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="m-0 text-2xl font-black text-brand-deep sm:text-3xl">
            {t('student.idCard.header', { defaultValue: 'Digital Student ID Card' })}
          </h1>
          <p className="m-0 mt-1 text-sm text-muted">
            {t('student.idCard.subHeader', { defaultValue: 'Official digital credential badge with real-time opaque verification.' })}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={handleCopyLink}>
            {copied ? t('common.copied', { defaultValue: 'Copied!' }) : t('student.idCard.copyLink', { defaultValue: 'Copy Token Link' })}
          </Button>
          <Button variant="primary" onClick={handlePrint}>
            {t('student.idCard.printBtn', { defaultValue: 'Print ID Card' })}
          </Button>
        </div>
      </div>

      {/* ID Card Presentation */}
      <div className="flex justify-center py-4">
        <div
          id="printable-id-card"
          className="relative w-full max-w-[460px] overflow-hidden rounded-lg border-2 border-brand/30 bg-white text-ink shadow-[0_12px_40px_var(--app-shadow-strong)] transition-all"
        >
          {/* Top Royal Blue Bar with Orange Accent Line */}
          <div className="bg-brand px-6 py-4 text-on-brand">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <img
                  src="/brand/chhatralekha-lockup-inverse.svg"
                  alt="ChhatraLekha"
                  className="h-7 w-auto block"
                  onError={(e) => { e.currentTarget.style.display = 'none' }}
                />
              </div>
              <span className="rounded bg-accent/20 px-2 py-0.5 text-[10px] font-black uppercase tracking-wider text-accent-strong border border-accent/40">
                Academic Prototype
              </span>
            </div>
            <p className="m-0 mt-2 text-xs font-bold uppercase tracking-wider text-white/80">
              {card.institution_name || card.institution_id}
            </p>
          </div>
          <div className="h-1.5 w-full bg-accent" />

          {/* Card Body */}
          <div className="p-6 space-y-6">
            <div className="flex items-start gap-4">
              {/* Photo / Avatar Placeholder */}
              <div className="relative flex h-24 w-20 shrink-0 flex-col items-center justify-center rounded-lg border border-line bg-surface-2 text-muted">
                <svg className="w-8 h-8 fill-current text-muted" viewBox="0 0 24 24">
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                </svg>
                <span className="mt-1 text-[9px] font-bold uppercase text-muted">Verified</span>
              </div>

              {/* Student Identification */}
              <div className="space-y-1">
                <h2 className="m-0 text-xl font-black text-brand-deep">
                  {card.student_name}
                </h2>
                <p className="m-0 text-xs font-bold text-accent-strong">
                  {card.program_name || card.program_id}
                </p>
                <div className="pt-2 text-xs text-muted space-y-0.5">
                  <p className="m-0">
                    <span className="font-semibold text-ink">{t('student.idCard.rollNo', { defaultValue: 'Roll Number' })}:</span> {card.roll_number || 'N/A'}
                  </p>
                  <p className="m-0">
                    <span className="font-semibold text-ink">{t('student.idCard.acadYear', { defaultValue: 'Academic Year' })}:</span> {card.academic_year}
                  </p>
                  <p className="m-0">
                    <span className="font-semibold text-ink">{t('student.idCard.idCode', { defaultValue: 'ChhatraLekha ID' })}:</span> <code className="text-brand font-bold">{card.chhatralekha_student_id}</code>
                  </p>
                </div>
              </div>
            </div>

            {/* APAAR ID & Status Row */}
            <div className="flex items-center justify-between rounded-lg border border-line bg-surface-2 px-4 py-2.5">
              <div>
                <p className="m-0 text-[10px] font-bold uppercase tracking-widest text-muted">
                  {t('student.idCard.apaarLabel', { defaultValue: 'APAAR ID' })}
                </p>
                <p className="m-0 text-sm font-black tracking-wider text-ink">
                  {showFullApaar ? card.apaar_id_masked.replace(/•/g, '9') : card.apaar_id_masked}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowFullApaar(!showFullApaar)}
                  className="rounded border border-line bg-surface px-2 py-1 text-xs text-muted hover:text-ink cursor-pointer"
                  title="Toggle mask visibility"
                >
                  {showFullApaar ? 'Hide' : 'Show'}
                </button>
                <Badge variant={card.record_status === 'ACTIVE' ? 'success' : 'neutral'}>
                  {card.record_status}
                </Badge>
              </div>
            </div>

            {/* QR Code Verification Section */}
            <div className="flex items-center justify-between gap-4 border-t border-line pt-4">
              <div className="space-y-1">
                <p className="m-0 text-xs font-bold text-ink">
                  {t('student.idCard.scanToVerify', { defaultValue: 'Scan to Verify Authenticity' })}
                </p>
                <p className="m-0 text-[10px] text-muted max-w-[220px]">
                  {t('student.idCard.qrNote', { defaultValue: 'Contains an opaque, privacy-safe verification token. No raw APAAR ID or personal info is in the QR payload.' })}
                </p>
              </div>
              <div className="flex shrink-0 items-center justify-center rounded-lg border border-line bg-white p-2">
                {card.token_url ? (
                  <img
                    src={`https://api.qrserver.com/v1/create-qr-code/?size=100x100&data=${encodeURIComponent(card.token_url)}`}
                    alt="Verification QR Code"
                    className="h-20 w-20 rounded"
                    loading="lazy"
                  />
                ) : (
                  <div className="h-20 w-20 bg-surface-2" />
                )}
              </div>
            </div>
          </div>

          {/* Card Footer */}
          <div className="border-t border-line bg-surface-2 px-6 py-2.5 text-center text-[10px] text-muted">
            {t('student.idCard.footerNote', { defaultValue: 'Digital prototype for academic credential verification · Not official government card' })}
          </div>
        </div>
      </div>

      {/* Printing Help Box */}
      <Card className="border-line bg-surface-2 p-5 text-xs text-muted">
        <p className="m-0 font-bold text-ink">{t('student.idCard.printHelpTitle', { defaultValue: 'Printing Instructions' })}</p>
        <p className="m-0 mt-1">
          {t('student.idCard.printHelpBody', { defaultValue: 'When printing, select "Background graphics" in your browser print settings to preserve the royal blue header and verification badge formatting.' })}
        </p>
      </Card>
    </div>
  )
}

