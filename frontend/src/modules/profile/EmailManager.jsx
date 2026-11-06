import { useState } from 'react'
import { api } from '../../services/api'

export default function EmailManager({
  profile,
  onProfileUpdated,
}) {
  const [activeType, setActiveType] = useState('PERSONAL')
  const [emailInput, setEmailInput] = useState('')
  const [verificationCode, setVerificationCode] = useState('')
  const [step, setStep] = useState('IDLE') // 'IDLE' | 'AWAITING_CODE'
  const [statusMessage, setStatusMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleRequestVerification = async (e) => {
    e.preventDefault()
    if (!emailInput.trim()) return

    setIsSubmitting(true)
    setErrorMessage('')
    setStatusMessage('')
    try {
      const resp = await api.post('/profile/email', {
        email: emailInput.trim(),
        email_type: activeType,
      })
      setStep('AWAITING_CODE')
      setStatusMessage(resp.data.message || 'Verification code sent. Enter the 6-digit code below.')
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to initiate email verification.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleConfirmCode = async (e) => {
    e.preventDefault()
    if (!verificationCode.trim()) return

    setIsSubmitting(true)
    setErrorMessage('')
    setStatusMessage('')
    try {
      const resp = await api.post('/profile/verify-email', {
        email: emailInput.trim(),
        code: verificationCode.trim(),
      })
      setStatusMessage(resp.data.message || 'Email successfully verified!')
      setStep('IDLE')
      setEmailInput('')
      setVerificationCode('')
      if (onProfileUpdated) {
        onProfileUpdated()
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Invalid or expired verification code.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Informational Notice */}
      <div className="p-3.5 rounded-lg bg-surface-2 border border-line text-xs text-muted leading-relaxed">
        <strong className="text-ink">Email Privacy & Policy Guarantee:</strong> ChhatraLekha manages verified identity bindings only. The platform never creates, hosts, or operates external institutional mailboxes.
      </div>

      {statusMessage && (
        <div className="p-3 rounded-lg bg-surface-2 border border-brand text-brand font-medium text-xs">
          {statusMessage}
        </div>
      )}

      {errorMessage && (
        <div className="p-3 rounded-lg bg-danger/10 border border-danger/30 text-danger font-medium text-xs">
          {errorMessage}
        </div>
      )}

      {/* Cards for Personal vs Institutional Email */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Personal Email Card */}
        <div className="p-4 rounded-lg bg-surface border border-line space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-ink">Personal Email Address</span>
            <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
              profile?.personal_email_verified
                ? 'bg-brand/15 text-brand border border-brand/30'
                : 'bg-warning-surface text-warning-strong border border-warning/40'
            }`}>
              {profile?.personal_email_verified ? 'VERIFIED' : 'UNVERIFIED'}
            </span>
          </div>

          <p className="m-0 text-sm font-semibold text-ink break-all">
            {profile?.personal_email || profile?.email || 'No personal email configured'}
          </p>
          <p className="m-0 text-[11px] text-muted">
            Used for account authentication, password recovery, and multi-factor security alerts.
          </p>

          <button
            type="button"
            onClick={() => {
              setActiveType('PERSONAL')
              setStep('IDLE')
              setEmailInput(profile?.personal_email || '')
            }}
            className="px-2.5 py-1 rounded border border-line bg-surface text-xs font-semibold text-ink hover:bg-surface-2 cursor-pointer shadow-xs"
          >
            Update Personal Email
          </button>
        </div>

        {/* Institutional Email Card */}
        <div className="p-4 rounded-lg bg-surface border border-line space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-ink">Institution-Issued Email</span>
            <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
              profile?.institution_email_verified
                ? 'bg-brand/15 text-brand border border-brand/30'
                : 'bg-surface-2 text-muted border border-line'
            }`}>
              {profile?.institution_email_verified ? 'VERIFIED' : 'NOT LINKED'}
            </span>
          </div>

          <p className="m-0 text-sm font-semibold text-ink break-all">
            {profile?.institution_email || 'No institutional email registered'}
          </p>
          <p className="m-0 text-[11px] text-muted">
            Issued by your school or college for official campus announcements and academic records.
          </p>

          <button
            type="button"
            onClick={() => {
              setActiveType('INSTITUTIONAL')
              setStep('IDLE')
              setEmailInput(profile?.institution_email || '')
            }}
            className="px-2.5 py-1 rounded border border-line bg-surface text-xs font-semibold text-ink hover:bg-surface-2 cursor-pointer shadow-xs"
          >
            Bind Institutional Email
          </button>
        </div>
      </div>

      {/* Verification / Input Section */}
      <div className="p-4 rounded-lg bg-surface border border-line space-y-4">
        <h3 className="m-0 text-xs font-bold text-ink uppercase tracking-wider">
          {step === 'AWAITING_CODE'
            ? `Confirm 6-Digit Code for ${emailInput}`
            : `Register or Change ${activeType === 'PERSONAL' ? 'Personal' : 'Institutional'} Email`}
        </h3>

        {step === 'IDLE' ? (
          <form onSubmit={handleRequestVerification} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-muted mb-1">
                Enter Email Address
              </label>
              <input
                type="email"
                required
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                placeholder="name@domain.edu.in"
                className="w-full px-3 py-2 rounded-lg border border-line bg-surface text-ink text-xs focus:outline-hidden focus:border-brand"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !emailInput.trim()}
              className={`px-4 py-2 rounded-lg bg-brand text-on-brand text-xs font-bold transition-opacity shadow-xs ${
                isSubmitting || !emailInput.trim() ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:bg-brand-deep'
              }`}
            >
              {isSubmitting ? 'Requesting Code...' : 'Send 6-Digit Verification Code'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleConfirmCode} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-muted mb-1">
                Enter 6-Digit Confirmation Code
              </label>
              <input
                type="text"
                required
                maxLength={6}
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                placeholder="123456"
                className="w-48 px-3 py-2 rounded-lg border border-line bg-surface text-ink font-mono text-center text-sm font-bold tracking-widest focus:outline-hidden focus:border-brand"
              />
            </div>

            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={isSubmitting || verificationCode.length !== 6}
                className={`px-4 py-2 rounded-lg bg-brand text-on-brand text-xs font-bold transition-opacity shadow-xs ${
                  isSubmitting || verificationCode.length !== 6 ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:bg-brand-deep'
                }`}
              >
                {isSubmitting ? 'Verifying...' : 'Confirm & Bind Email'}
              </button>

              <button
                type="button"
                onClick={() => setStep('IDLE')}
                className="text-xs text-muted hover:text-ink cursor-pointer bg-transparent border-0"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
