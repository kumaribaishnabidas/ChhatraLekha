import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '../../hooks/usePageMeta'
import { api, errorMessage } from '../../services/api'
import { Button, Card, Badge, Table } from '../../components/common'

export default function StudentSharePage() {
  const { t } = useTranslation()
  usePageMeta({
    title: t('student.share.title', { defaultValue: 'Manage Share Links' }),
    description: 'Create time-limited verification share links with granular field control and instant revocation.',
  })

  const [shares, setShares] = useState([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const [latestShare, setLatestShare] = useState(null)
  const [copied, setCopied] = useState(false)

  // Form state
  const [expiryHours, setExpiryHours] = useState(24)
  const [fields, setFields] = useState({
    institution: true,
    programme: true,
    academic_year: true,
    status: true,
    student_name: false,
  })

  const fetchShares = async () => {
    try {
      setLoading(true)
      setError('')
      const { data } = await api.get('/me/shares')
      setShares(Array.isArray(data) ? data : data?.shares || [])
    } catch (err) {
      setError(errorMessage(err, 'Unable to load share links.'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchShares()
  }, [])

  const handleFieldToggle = (key) => {
    setFields((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const handleCreateShare = async (e) => {
    e.preventDefault()
    try {
      setCreating(true)
      setError('')
      const allowed = Object.keys(fields).filter((k) => fields[k])
      const { data } = await api.post('/me/shares', {
        expiry_hours: Number(expiryHours),
        allowed_fields: allowed,
        include_name: fields.student_name,
      })
      setLatestShare(data)
      fetchShares()
    } catch (err) {
      setError(errorMessage(err, 'Failed to create share link.'))
    } finally {
      setCreating(false)
    }
  }

  const handleRevoke = async (tokenId) => {
    try {
      await api.post(`/me/shares/${tokenId}/revoke`)
      if (latestShare?.token_id === tokenId) {
        setLatestShare(null)
      }
      fetchShares()
    } catch (err) {
      setError(errorMessage(err, 'Failed to revoke token.'))
    }
  }

  const copyUrl = (url) => {
    navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="mx-auto max-w-[1200px] px-5 py-8 space-y-8">
      <div>
        <h1 className="m-0 text-2xl font-black text-brand-deep sm:text-3xl">
          {t('student.share.header', { defaultValue: 'Self-Service Verification Shares' })}
        </h1>
        <p className="m-0 mt-1 text-sm text-muted">
          {t('student.share.subHeader', { defaultValue: 'Create private, time-limited verification links and QR codes. You control which fields are visible.' })}
        </p>
      </div>

      {error && (
        <Card className="border-danger/30 bg-danger/5 p-4 text-xs font-semibold text-danger">
          {error}
        </Card>
      )}

      {/* Share Creator Form */}
      <div className="grid gap-8 lg:grid-cols-2">
        <Card className="p-6 space-y-5">
          <h2 className="m-0 text-lg font-bold text-ink">
            {t('student.share.createNew', { defaultValue: 'Create New Verification Link' })}
          </h2>

          <form onSubmit={handleCreateShare} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-muted mb-2">
                {t('student.share.expiryLabel', { defaultValue: 'Link Validity Duration' })}
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: 1, label: '1 Hour' },
                  { value: 24, label: '24 Hours (1 Day)' },
                  { value: 168, label: '7 Days' },
                ].map((item) => (
                  <button
                    key={item.value}
                    type="button"
                    onClick={() => setExpiryHours(item.value)}
                    className={`rounded-lg border p-2.5 text-xs font-bold transition-colors cursor-pointer ${
                      expiryHours === item.value
                        ? 'border-brand bg-brand text-on-brand'
                        : 'border-line bg-surface text-ink hover:bg-surface-2'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-muted mb-2">
                {t('student.share.fieldsLabel', { defaultValue: 'Information Disclosed to Verifier' })}
              </label>
              <div className="space-y-2 rounded-lg border border-line bg-surface-2 p-3 text-xs">
                {[
                  { key: 'institution', label: 'Institution Name', desc: 'College/University affiliation' },
                  { key: 'programme', label: 'Degree Programme', desc: 'Branch and course code' },
                  { key: 'academic_year', label: 'Academic Year', desc: 'Enrolment academic session' },
                  { key: 'status', label: 'Record Status', desc: 'Current active enrolment standing' },
                  { key: 'student_name', label: 'Student Name (Optional)', desc: 'Off by default for enhanced privacy' },
                ].map((field) => (
                  <label key={field.key} className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={fields[field.key]}
                      onChange={() => handleFieldToggle(field.key)}
                      className="mt-0.5 h-4 w-4 rounded border-line text-brand focus:ring-brand"
                    />
                    <div>
                      <span className="font-bold text-ink block">{field.label}</span>
                      <span className="text-muted block text-[11px]">{field.desc}</span>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className="rounded-lg border border-line bg-surface p-3 text-xs text-muted">
              <span className="font-bold text-ink">Strict Privacy Guarantee:</span> Raw APAAR IDs, Date of Birth, and contact info are NEVER included or accessible through public share links.
            </div>

            <Button type="submit" variant="accent" disabled={creating} className="w-full">
              {creating ? t('common.loading', { defaultValue: 'Generating...' }) : t('student.share.generateBtn', { defaultValue: 'Generate Verification Link' })}
            </Button>
          </form>
        </Card>

        {/* Latest Generated Share Card */}
        {latestShare ? (
          <Card className="border-success/30 bg-success/5 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="m-0 text-base font-bold text-success-strong">
                {t('student.share.activeShareReady', { defaultValue: 'Share Link Ready' })}
              </h3>
              <Badge variant="success">Active</Badge>
            </div>

            <div className="flex flex-col items-center justify-center p-4 bg-white rounded-lg border border-line space-y-3">
              <img
                src={`https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=${encodeURIComponent(latestShare.share_url)}`}
                alt="Verification QR Code"
                className="h-32 w-32 rounded"
                loading="lazy"
              />
              <p className="m-0 text-[11px] text-muted text-center max-w-[260px]">
                Scan to verify credential proof on any device without exposing sensitive data.
              </p>
            </div>

            <div className="space-y-1">
              <p className="m-0 text-xs font-bold text-ink">{t('student.share.urlLabel', { defaultValue: 'Public Verification URL' })}</p>
              <div className="flex items-center gap-2">
                <input
                  readOnly
                  value={latestShare.share_url}
                  className="w-full rounded border border-line bg-surface px-3 py-1.5 text-xs font-mono text-ink"
                />
                <Button variant="secondary" onClick={() => copyUrl(latestShare.share_url)}>
                  {copied ? 'Copied' : 'Copy'}
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-line text-xs">
              <span className="text-muted">
                Expires: {new Date(latestShare.expires_at).toLocaleString()}
              </span>
              <button
                type="button"
                onClick={() => handleRevoke(latestShare.token_id)}
                className="text-xs font-bold text-danger hover:underline cursor-pointer bg-transparent border-0"
              >
                Revoke Now
              </button>
            </div>
          </Card>
        ) : (
          <Card className="flex flex-col items-center justify-center border-dashed border-line bg-surface-2 p-8 text-center text-muted">
            <span className="rounded bg-brand/10 px-2 py-1 text-xs font-bold text-brand uppercase mb-2">Share</span>
            <h3 className="m-0 text-base font-bold text-ink">{t('student.share.noActiveShare', { defaultValue: 'No Fresh Link Generated' })}</h3>
            <p className="m-0 mt-1 text-xs max-w-xs">
              Select your validity duration and information disclosure preferences, then click Generate to create a shareable verification link.
            </p>
          </Card>
        )}
      </div>

      {/* Share History & Revocation Table */}
      <div className="space-y-4">
        <h2 className="m-0 text-lg font-black text-brand-deep">
          {t('student.share.historyHeader', { defaultValue: 'Share Link History & Access Control' })}
        </h2>

        {loading ? (
          <div className="h-40 rounded-lg bg-surface-2 animate-pulse" />
        ) : shares.length === 0 ? (
          <Card className="p-8 text-center text-muted text-sm">
            {t('student.share.emptyHistory', { defaultValue: 'You have not created any share links yet.' })}
          </Card>
        ) : (
          <Table
            headers={['Token ID', 'Status', 'Allowed Fields', 'Issued', 'Expires', 'Actions']}
            rows={shares.map((s) => [
              <code key="id" className="font-mono text-xs">{s.token_id}</code>,
              <Badge key="status" variant={s.status === 'ACTIVE' ? 'success' : s.status === 'REVOKED' ? 'danger' : 'neutral'}>
                {s.status}
              </Badge>,
              <div key="fields" className="flex flex-wrap gap-1">
                {(s.allowed_fields || []).map((f) => (
                  <span key={f} className="rounded bg-surface-2 border border-line px-1.5 py-0.5 text-[10px] text-muted">
                    {f}
                  </span>
                ))}
              </div>,
              new Date(s.issued_at).toLocaleDateString(),
              new Date(s.expires_at).toLocaleDateString(),
              s.status === 'ACTIVE' ? (
                <button
                  key="action"
                  type="button"
                  onClick={() => handleRevoke(s.token_id)}
                  className="rounded border border-danger/40 bg-danger/10 px-2.5 py-1 text-xs font-bold text-danger hover:bg-danger/20 cursor-pointer"
                >
                  Revoke
                </button>
              ) : (
                <span key="action" className="text-xs text-muted">Closed</span>
              ),
            ])}
          />
        )}
      </div>
    </div>
  )
}

