import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '../hooks/usePageMeta'
import { api } from '../services/api'
import {
  Card,
  Badge,
  Button,
  StatusChip,
  Modal,
  Spinner,
  ErrorState,
} from '../components/common'

export default function StudentWalletPage() {
  const { t } = useTranslation()

  usePageMeta({
    title: t('wallet.title'),
    description: t('wallet.lead'),
    canonical: '/wallet',
  })

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [wallet, setWallet] = useState(null)
  const [showFullApaar, setShowFullApaar] = useState(false)
  const [ocrModalOpen, setOcrModalOpen] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [ocrResult, setOcrResult] = useState(null)
  const [consentUpdating, setConsentUpdating] = useState(false)

  const fetchWallet = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await api.get('/students/me/wallet')
      setWallet(res.data)
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load wallet.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWallet()
  }, [])

  const handleToggleConsent = async (purpose, currentAllowed) => {
    if (!wallet?.student?.apaar_id) return
    try {
      setConsentUpdating(true)
      await api.post('/consent', {
        apaar_id: wallet.student.apaar_id,
        purpose,
        status: currentAllowed ? 'WITHDRAWN' : 'GRANTED',
        channel: 'WEB_PORTAL',
      })
      await fetchWallet()
    } catch (err) {
      alert(err?.response?.data?.detail || 'Could not update consent.')
    } finally {
      setConsentUpdating(false)
    }
  }

  const handleOcrUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    try {
      setUploading(true)
      setOcrResult(null)
      const formData = new FormData()
      formData.append('file', file)
      const res = await api.post('/students/upload-document?document_type=Marksheet', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setOcrResult(res.data)
    } catch (err) {
      alert(err?.response?.data?.detail || 'OCR extraction failed.')
    } finally {
      setUploading(false)
    }
  }

  if (loading) {
    return <div className="flex justify-center p-12"><Spinner label={t('common.loading')} /></div>
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchWallet} />
  }

  const student = wallet?.student || {}
  const rawApaar = student.apaar_id || '984210357890'
  const maskedApaar = `****-****-${rawApaar.slice(-4)}`
  const verificationUrl = wallet?.verification_token?.token_url || `/verify/t/${rawApaar}`

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-brand tracking-tight m-0">{t('wallet.title')}</h1>
        <p className="text-base text-muted leading-relaxed mt-1 m-0">{t('wallet.lead')}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-8 items-start">
        {/* Left Column: Digital Student ID Card */}
        <section className="space-y-6">
          <div className="rounded-lg border border-line bg-surface-2 p-6 shadow-md space-y-5">
            {/* ID Card Top Header */}
            <div className="flex items-center justify-between border-b border-line pb-4">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-wider text-accent-strong m-0">
                  National Academic Registry
                </p>
                <h2 className="text-xl font-black text-brand m-0">ChhatraLekha Student ID</h2>
              </div>
              <StatusChip status={student.record_status || 'ACTIVE'}>
                {student.record_status || 'Active'}
              </StatusChip>
            </div>

            {/* Student Info & QR */}
            <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-6 items-center">
              <div className="space-y-3">
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-muted">
                    {t('common.student')}
                  </span>
                  <p className="text-lg font-bold text-ink m-0">{student.student_name}</p>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-muted">
                      {t('common.programme')}
                    </span>
                    <p className="font-semibold text-ink m-0">{student.program_id}</p>
                  </div>
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-muted">
                      {t('students.roll')}
                    </span>
                    <p className="font-semibold text-ink m-0">{student.roll_number || 'N/A'}</p>
                  </div>
                </div>

                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-muted">
                    {t('common.institution')}
                  </span>
                  <p className="text-sm font-semibold text-ink m-0">{student.institution_id}</p>
                </div>

                <div className="pt-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-muted">
                      {t('wallet.toggleApaar')}:
                    </span>
                    <span className="font-mono font-bold text-sm text-brand-deep">
                      {showFullApaar ? rawApaar : maskedApaar}
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowFullApaar(!showFullApaar)}
                      className="text-xs text-brand hover:underline cursor-pointer font-semibold"
                    >
                      {showFullApaar ? 'Hide' : 'Show'}
                    </button>
                  </div>
                </div>
              </div>

              {/* QR Code */}
              <div className="flex flex-col items-center justify-center p-3 rounded-lg border border-line bg-surface text-center">
                <img
                  src={`https://api.qrserver.com/v1/create-qr-code/?size=130x130&data=${encodeURIComponent(verificationUrl)}`}
                  alt="Student Verification QR"
                  className="w-28 h-28 object-contain"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none'
                  }}
                />
                <span className="text-[10px] font-semibold text-muted mt-2 max-w-[120px]">
                  Opaque Token
                </span>
              </div>
            </div>

            {/* Privacy note */}
            <div className="rounded bg-surface p-3 text-xs text-muted border border-line leading-relaxed">
              {t('wallet.qrNotice')}
            </div>
          </div>

          {/* Credentials Archive */}
          <Card title={t('wallet.credentials')} actions={
            <Button variant="secondary" onClick={() => setOcrModalOpen(true)}>
              {t('wallet.ocrUpload')}
            </Button>
          }>
            <div className="space-y-3">
              {wallet?.credentials?.map((cred) => (
                <div
                  key={cred.id}
                  className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-lg border border-line bg-surface-2"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-ink">{cred.type}</span>
                      <StatusChip status={cred.status}>{cred.status}</StatusChip>
                    </div>
                    <p className="text-xs text-muted m-0">
                      Issued by {cred.issuer} &bull; Programme {cred.programme} &bull; {cred.issued_date}
                    </p>
                  </div>
                  <a
                    href={cred.download_url}
                    download
                    className="btn btn-navy text-xs no-underline inline-flex items-center"
                  >
                    {t('wallet.downloadCertificate')}
                  </a>
                </div>
              ))}
            </div>
          </Card>
        </section>

        {/* Right Column: Consent Management */}
        <section className="space-y-6">
          <Card title={t('wallet.consent')} subtitle={t('wallet.consentLead')}>
            <div className="space-y-4">
              {wallet?.consents?.map((c) => (
                <div
                  key={c.purpose}
                  className="p-4 rounded-lg border border-line bg-surface-2 flex items-start justify-between gap-4"
                >
                  <div className="space-y-1">
                    <p className="text-sm font-bold text-ink m-0">{c.purpose_label}</p>
                    <p className="text-xs text-muted m-0">{c.reason}</p>
                    <span className={`inline-block text-[11px] font-semibold ${c.allowed ? 'text-success-strong' : 'text-muted'}`}>
                      Status: {c.status}
                    </span>
                  </div>
                  <button
                    type="button"
                    disabled={consentUpdating}
                    onClick={() => handleToggleConsent(c.purpose, c.allowed)}
                    className={`btn text-xs px-3 py-1.5 shrink-0 ${
                      c.allowed ? 'btn-navy' : 'btn-outline'
                    }`}
                  >
                    {c.allowed ? 'Revoke' : 'Grant'}
                  </button>
                </div>
              ))}
            </div>
          </Card>
        </section>
      </div>

      {/* OCR Document Verification Modal */}
      <Modal
        open={ocrModalOpen}
        onClose={() => setOcrModalOpen(false)}
        title={t('wallet.ocrUpload')}
        footer={
          <Button variant="secondary" onClick={() => setOcrModalOpen(false)}>
            {t('common.close')}
          </Button>
        }
      >
        <div className="space-y-4">
          <p className="text-sm text-muted m-0">{t('wallet.ocrPrompt')}</p>

          <div className="rounded-lg border-2 border-dashed border-line p-6 text-center bg-surface-2">
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={handleOcrUpload}
              disabled={uploading}
              className="text-xs text-ink cursor-pointer file:btn file:btn-navy file:mr-3 file:text-xs"
            />
          </div>

          {uploading && (
            <div className="flex justify-center p-4">
              <Spinner label={t('wallet.ocrExtracting')} />
            </div>
          )}

          {ocrResult && (
            <div className="space-y-3 rounded-lg border border-line bg-surface p-4 text-xs">
              <div className="flex items-center justify-between border-b border-line pb-2">
                <span className="font-bold text-sm text-ink">{ocrResult.document_type}</span>
                <Badge className={ocrResult.validations?.apaar_checksum_valid ? 'bg-success-surface text-success-strong' : 'bg-warning-surface text-warning-strong'}>
                  {ocrResult.verdict}
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-muted block">Student Name:</span>
                  <span className="font-semibold text-ink">{ocrResult.student_name}</span>
                </div>
                <div>
                  <span className="text-muted block">APAAR ID:</span>
                  <span className="font-mono font-semibold text-ink">{ocrResult.apaar_id}</span>
                </div>
                <div>
                  <span className="text-muted block">Programme:</span>
                  <span className="font-semibold text-ink">{ocrResult.program_code}</span>
                </div>
                <div>
                  <span className="text-muted block">Score / CGPA:</span>
                  <span className="font-semibold text-ink">{ocrResult.score}</span>
                </div>
              </div>

              <div className="p-2.5 rounded bg-warning-surface text-warning-strong text-[11px] leading-relaxed border border-warning/30">
                <strong>Notice:</strong> {t('wallet.ocrReviewNotice')}
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}
