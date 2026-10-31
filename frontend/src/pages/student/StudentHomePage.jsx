import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '../../hooks/usePageMeta'
import { api, errorMessage } from '../../services/api'
import { Button, Card, Badge, Input } from '../../components/common'

export default function StudentHomePage() {
  const { t } = useTranslation()
  usePageMeta({
    title: t('student.home.title', { defaultValue: 'Student Academic Identity' }),
    description: 'ChhatraLekha Student Portal - Manage your trusted academic identity, credentials, and verification shares.',
  })

  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [claimCode, setClaimCode] = useState('')
  const [claimLoading, setClaimLoading] = useState(false)
  const [claimError, setClaimError] = useState('')
  const [claimSuccess, setClaimSuccess] = useState('')

  const fetchProfile = async () => {
    try {
      setLoading(true)
      setError('')
      const { data } = await api.get('/me/profile')
      setProfile(data)
    } catch (err) {
      setError(errorMessage(err, 'Unable to load profile.'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProfile()
  }, [])

  const handleClaim = async (e) => {
    e.preventDefault()
    if (!claimCode.trim()) return
    try {
      setClaimLoading(true)
      setClaimError('')
      setClaimSuccess('')
      await api.post('/me/claim', { claim_code: claimCode.trim() })
      setClaimSuccess(t('student.home.claimSuccess', { defaultValue: 'Account successfully linked to your academic record!' }))
      setClaimCode('')
      fetchProfile()
    } catch (err) {
      setClaimError(errorMessage(err, 'Invalid or expired claim code.'))
    } finally {
      setClaimLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-[1200px] px-5 py-8 space-y-6">
        <div className="h-40 rounded-lg bg-surface-2 animate-pulse" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 rounded-lg bg-surface-2 animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-[1200px] px-5 py-8 space-y-8">
      {/* Student Identity Hero Header */}
      <Card className="relative overflow-hidden border-brand/20 bg-surface p-6 sm:p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-lg bg-brand text-2xl font-bold text-on-brand">
              {profile?.student_name ? profile.student_name.charAt(0).toUpperCase() : 'S'}
            </div>
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="m-0 text-2xl font-black text-brand-deep sm:text-3xl">
                  {profile?.student_name || t('student.home.welcome', { defaultValue: 'Student Portal' })}
                </h1>
                <Badge variant={profile?.record_status === 'ACTIVE' ? 'success' : 'neutral'}>
                  {profile?.record_status || 'PENDING'}
                </Badge>
              </div>
              <p className="m-0 text-sm font-semibold text-ink">
                {profile?.program_name || profile?.program_id || 'Degree Programme'} · {profile?.institution_name || profile?.institution_id}
              </p>
              <div className="flex flex-wrap gap-4 pt-1 text-xs text-muted">
                <span>{t('student.home.studentId', { defaultValue: 'ID' })}: <strong className="text-ink">{profile?.student_id || 'N/A'}</strong></span>
                <span>{t('student.home.apaarId', { defaultValue: 'APAAR ID' })}: <strong className="text-ink">{profile?.apaar_id_masked || '•••• •••• ••••'}</strong></span>
                <span>{t('student.home.rollNo', { defaultValue: 'Roll No' })}: <strong className="text-ink">{profile?.student_institute_roll_no || 'N/A'}</strong></span>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="hidden xl:block rounded bg-white p-1 border border-line shadow-xs">
              <img
                src="/brand/chhatralekha-logo.png"
                alt="ChhatraLekha"
                className="h-9 w-auto object-contain block"
              />
            </div>
            <Link to="/me/id-card" className="no-underline">
              <Button variant="accent">
                {t('student.home.viewCard', { defaultValue: 'Digital ID Card' })}
              </Button>
            </Link>
            <Link to="/me/share" className="no-underline">
              <Button variant="secondary">
                {t('student.home.shareProof', { defaultValue: 'Create Share Link' })}
              </Button>
            </Link>
          </div>
        </div>
      </Card>

      {/* Unlinked Claim Code Notice / Form */}
      {error && (
        <Card className="border-warning/30 bg-warning/5 p-6">
          <div className="space-y-4">
            <div>
              <h2 className="m-0 text-lg font-bold text-ink">
                {t('student.home.linkRecordTitle', { defaultValue: 'Link Your Academic Record' })}
              </h2>
              <p className="m-0 mt-1 text-sm text-muted">
                {t('student.home.linkRecordDesc', { defaultValue: 'Enter the one-time claim code provided by your institution administrator to link your account to your official student profile.' })}
              </p>
            </div>
            <form onSubmit={handleClaim} className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <div className="w-full sm:w-80">
                <Input
                  placeholder="CL-XXXX-XXXX"
                  value={claimCode}
                  onChange={(e) => setClaimCode(e.target.value)}
                  disabled={claimLoading}
                />
              </div>
              <Button type="submit" disabled={claimLoading || !claimCode.trim()}>
                {claimLoading ? t('common.loading', { defaultValue: 'Verifying...' }) : t('student.home.claimBtn', { defaultValue: 'Link Record' })}
              </Button>
            </form>
            {claimError && <p className="m-0 text-xs font-semibold text-danger">{claimError}</p>}
            {claimSuccess && <p className="m-0 text-xs font-semibold text-success-strong">{claimSuccess}</p>}
          </div>
        </Card>
      )}

      {/* Feature Navigation Hub */}
      <div className="space-y-4">
        <h2 className="m-0 text-lg font-black text-brand-deep">
          {t('student.home.portalHub', { defaultValue: 'Academic Identity Hub' })}
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Link to="/me/id-card" className="no-underline">
            <Card className="h-full p-5 transition-transform hover:-translate-y-1">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand/10 text-brand text-xs font-black">ID</span>
                <div>
                  <h3 className="m-0 text-base font-bold text-ink">{t('nav.idCard', { defaultValue: 'Digital ID Card' })}</h3>
                  <p className="m-0 text-xs text-muted">{t('student.home.hubCardDesc', { defaultValue: 'Printable digital badge with opaque QR verification token' })}</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/me/share" className="no-underline">
            <Card className="h-full p-5 transition-transform hover:-translate-y-1">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10 text-accent-strong text-xs font-black">SHARE</span>
                <div>
                  <h3 className="m-0 text-base font-bold text-ink">{t('nav.shares', { defaultValue: 'Share Proof' })}</h3>
                  <p className="m-0 text-xs text-muted">{t('student.home.hubShareDesc', { defaultValue: 'Create time-limited share links and revoke them anytime' })}</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/wallet" className="no-underline">
            <Card className="h-full p-5 transition-transform hover:-translate-y-1">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-success-surface text-success-strong text-xs font-black">DOCS</span>
                <div>
                  <h3 className="m-0 text-base font-bold text-ink">{t('nav.wallet', { defaultValue: 'Academic Wallet' })}</h3>
                  <p className="m-0 text-xs text-muted">{t('student.home.hubWalletDesc', { defaultValue: 'Verifiable degree, bonafide certificates, and transcripts' })}</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/me/consent" className="no-underline">
            <Card className="h-full p-5 transition-transform hover:-translate-y-1">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand/10 text-brand text-xs font-black">RULE</span>
                <div>
                  <h3 className="m-0 text-base font-bold text-ink">{t('nav.consent', { defaultValue: 'Consent Centre' })}</h3>
                  <p className="m-0 text-xs text-muted">{t('student.home.hubConsentDesc', { defaultValue: 'Control who verifies your records with full audit history' })}</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/me/uploads" className="no-underline">
            <Card className="h-full p-5 transition-transform hover:-translate-y-1">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10 text-accent-strong text-xs font-black">OCR</span>
                <div>
                  <h3 className="m-0 text-base font-bold text-ink">{t('nav.uploads', { defaultValue: 'Document OCR' })}</h3>
                  <p className="m-0 text-xs text-muted">{t('student.home.hubUploadDesc', { defaultValue: 'Upload marksheets for automated field extraction and review' })}</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/me/results" className="no-underline">
            <Card className="h-full p-5 transition-transform hover:-translate-y-1">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-success-surface text-success-strong text-xs font-black">DATA</span>
                <div>
                  <h3 className="m-0 text-base font-bold text-ink">{t('nav.results', { defaultValue: 'Results & Analytics' })}</h3>
                  <p className="m-0 text-xs text-muted">{t('student.home.hubResultsDesc', { defaultValue: 'Semester SGPA, cumulative CGPA, and subject credits' })}</p>
                </div>
              </div>
            </Card>
          </Link>
        </div>
      </div>

      {/* Privacy Guarantee Footer Note */}
      <Card className="border-line bg-surface-2 p-5">
        <div className="flex items-start gap-3">
          <span className="rounded bg-brand/10 px-2 py-0.5 text-xs font-bold text-brand uppercase">Privacy</span>
          <div className="space-y-1 text-xs text-muted">
            <p className="m-0 font-bold text-ink">
              {t('student.home.privacyHeader', { defaultValue: 'Student Privacy by Design' })}
            </p>
            <p className="m-0">
              {t('student.home.privacyBody', { defaultValue: 'Your APAAR ID and personal details are never exposed on public URLs or printed in raw QR codes. Every verification link uses an opaque, revocable cryptographic token.' })}
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}

