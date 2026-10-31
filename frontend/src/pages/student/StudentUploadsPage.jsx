import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '../../hooks/usePageMeta'
import { api, errorMessage } from '../../services/api'
import { Button, Card, Badge, Table, Select } from '../../components/common'

export default function StudentUploadsPage() {
  const { t } = useTranslation()
  usePageMeta({
    title: t('student.uploads.title', { defaultValue: 'Document Upload & OCR' }),
    description: 'Upload academic marksheets and certificates for automated OCR extraction and institutional approval.',
  })

  const [uploads, setUploads] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [latestResult, setLatestResult] = useState(null)

  // Form
  const [file, setFile] = useState(null)
  const [documentType, setDocumentType] = useState('Marksheet')

  const fetchUploads = async () => {
    try {
      setLoading(true)
      setError('')
      const { data } = await api.get('/me/uploads')
      setUploads(Array.isArray(data) ? data : data?.uploads || [])
    } catch (err) {
      setError(errorMessage(err, 'Unable to load upload history.'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUploads()
  }, [])

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file) return
    try {
      setUploading(true)
      setError('')
      const formData = new FormData()
      formData.append('file', file)

      const { data } = await api.post(`/me/uploads?document_type=${encodeURIComponent(documentType)}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setLatestResult(data)
      setFile(null)
      fetchUploads()
    } catch (err) {
      setError(errorMessage(err, 'Document upload or OCR processing failed.'))
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="mx-auto max-w-[1200px] px-5 py-8 space-y-8">
      <div>
        <h1 className="m-0 text-2xl font-black text-brand-deep sm:text-3xl">
          {t('student.uploads.header', { defaultValue: 'Document Upload & OCR Verification' })}
        </h1>
        <p className="m-0 mt-1 text-sm text-muted">
          {t('student.uploads.subHeader', { defaultValue: 'Submit academic marksheets or transcripts. Automated OCR extracts key fields for decision support, followed by mandatory institutional review.' })}
        </p>
      </div>

      {error && (
        <Card className="border-danger/30 bg-danger/5 p-4 text-xs font-semibold text-danger">
          {error}
        </Card>
      )}

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Upload Form */}
        <Card className="p-6 space-y-5">
          <h2 className="m-0 text-lg font-bold text-ink">
            {t('student.uploads.submitNew', { defaultValue: 'Submit Academic Document' })}
          </h2>

          <form onSubmit={handleUpload} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-muted mb-2">
                {t('student.uploads.typeLabel', { defaultValue: 'Document Category' })}
              </label>
              <Select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                options={[
                  { value: 'Marksheet', label: 'Semester Marksheet / Grade Sheet' },
                  { value: 'Provisional Degree', label: 'Provisional Degree Certificate' },
                  { value: 'Migration Certificate', label: 'Migration / Transfer Certificate' },
                ]}
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-muted mb-2">
                {t('student.uploads.fileLabel', { defaultValue: 'Select File (PDF, PNG, JPG)' })}
              </label>
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.txt"
                onChange={(e) => setFile(e.target.files[0] || null)}
                className="w-full text-xs text-ink file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-brand/10 file:text-brand hover:file:bg-brand/20 cursor-pointer"
              />
              <p className="m-0 mt-1 text-[11px] text-muted">Max file size: 10 MB. High-contrast scans yield best OCR accuracy.</p>
            </div>

            <div className="rounded-lg border border-line bg-surface-2 p-3 text-xs text-muted">
              <span className="font-bold text-ink">Human-in-the-Loop Required:</span> Automated OCR serves as decision support. No document becomes a verified credential until approved by an authorised institution official.
            </div>

            <Button type="submit" variant="accent" disabled={uploading || !file} className="w-full">
              {uploading ? t('common.loading', { defaultValue: 'Processing OCR...' }) : t('student.uploads.uploadBtn', { defaultValue: 'Upload & Run Extraction' })}
            </Button>
          </form>
        </Card>

        {/* Latest OCR Extraction Feedback */}
        {latestResult ? (
          <Card className="border-brand/30 bg-surface p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="m-0 text-base font-bold text-brand-deep">
                {t('student.uploads.extractionResults', { defaultValue: 'Extraction & Verification Preview' })}
              </h3>
              <Badge variant="warning">{latestResult.status}</Badge>
            </div>

            <div className="space-y-3 rounded-lg border border-line bg-surface-2 p-4 text-xs">
              <div className="flex justify-between border-b border-line pb-2">
                <span className="text-muted">Document Type:</span>
                <span className="font-bold text-ink">{latestResult.document_type}</span>
              </div>
              <div className="flex justify-between border-b border-line pb-2">
                <span className="text-muted">Extracted Name:</span>
                <span className="font-bold text-ink">{latestResult.extracted_data?.student_name || 'N/A'}</span>
              </div>
              <div className="flex justify-between border-b border-line pb-2">
                <span className="text-muted">Extracted APAAR ID:</span>
                <span className="font-bold text-ink">{latestResult.extracted_data?.apaar_id || 'Not found'}</span>
              </div>
              <div className="flex justify-between border-b border-line pb-2">
                <span className="text-muted">Matched Attributes:</span>
                <span className="font-bold text-success-strong">{(latestResult.matched_fields || []).join(', ') || 'None'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Approval Status:</span>
                <span className="font-bold text-warning-strong">Pending Institution Sign-Off</span>
              </div>
            </div>

            <p className="m-0 text-xs text-muted">
              Your document has been safely queued in your institution&#39;s review inbox. Once reviewed, it will appear in your Academic Wallet.
            </p>
          </Card>
        ) : (
          <Card className="flex flex-col items-center justify-center border-dashed border-line bg-surface-2 p-8 text-center text-muted">
            <span className="rounded bg-brand/10 px-2 py-1 text-xs font-bold text-brand uppercase mb-2">OCR</span>
            <h3 className="m-0 text-base font-bold text-ink">{t('student.uploads.noUploadActive', { defaultValue: 'No Upload in Progress' })}</h3>
            <p className="m-0 mt-1 text-xs max-w-xs">
              Select your academic document above to trigger real-time OCR extraction and field matching against your profile.
            </p>
          </Card>
        )}
      </div>

      {/* Uploads History Table */}
      <div className="space-y-4">
        <h2 className="m-0 text-lg font-black text-brand-deep">
          {t('student.uploads.historyHeader', { defaultValue: 'Submission History & Status' })}
        </h2>

        {loading ? (
          <div className="h-40 rounded-lg bg-surface-2 animate-pulse" />
        ) : uploads.length === 0 ? (
          <Card className="p-8 text-center text-muted text-sm">
            {t('student.uploads.emptyHistory', { defaultValue: 'You have not submitted any documents yet.' })}
          </Card>
        ) : (
          <Table
            headers={['Document', 'Filename', 'Status', 'Matched Fields', 'Reviewer Feedback', 'Date']}
            rows={uploads.map((u, idx) => [
              <span key={`t-${idx}`} className="font-bold text-ink text-xs">{u.document_type}</span>,
              <code key={`f-${idx}`} className="text-xs font-mono">{u.filename}</code>,
              <Badge
                key={`s-${idx}`}
                variant={u.status === 'APPROVED' ? 'success' : u.status === 'REJECTED' ? 'danger' : 'warning'}
              >
                {u.status}
              </Badge>,
              <span key={`m-${idx}`} className="text-xs text-muted">{(u.matched_fields || []).join(', ') || '-'}</span>,
              <span key={`r-${idx}`} className="text-xs text-ink">{u.reviewer_notes || 'Pending evaluation'}</span>,
              new Date(u.created_at).toLocaleDateString(),
            ])}
          />
        )}
      </div>
    </div>
  )
}

