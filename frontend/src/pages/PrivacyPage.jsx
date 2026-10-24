import { usePageMeta } from '../hooks/usePageMeta'

export default function PrivacyPage() {
  usePageMeta({
    title: 'Privacy Policy',
    description: 'Privacy policy for the EduSynC prototype, detailing synthetic data processing, token hashing, and audit logging.',
    canonical: '/privacy',
  })

  return (
    <div className="mx-auto max-w-[850px] px-5 py-12 space-y-8">
      <div className="space-y-3">
        <div className="inline-block px-3 py-1 rounded bg-warning-surface text-warning-strong border border-warning/40 text-xs font-semibold">
          Draft for the prototype &middot; Needs legal review
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-brand tracking-tight m-0">
          Privacy Policy
        </h1>
        <p className="text-sm text-muted">Last updated: October 2026</p>
      </div>

      <div className="space-y-6 text-sm sm:text-base leading-relaxed text-ink border-t border-line pt-6">
        <section className="space-y-2">
          <h2 className="text-lg font-bold text-ink">1. Nature of the System</h2>
          <p className="text-muted">
            EduSynC is a software verification prototype. All citizen records, student enrollments, institution profiles, and anomaly markers stored within the system database are synthetic data generated for architectural validation.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-ink">2. What We Store</h2>
          <ul className="list-disc pl-5 space-y-1 text-muted">
            <li><strong>Synthetic Student Records:</strong> Synthetic names, simulated APAAR identifiers, enrollment dates, course codes, and quota categories.</li>
            <li><strong>Verification Tokens:</strong> Cryptographic SHA-256 digests of issued verification tokens. Raw plaintext tokens are generated once and never persisted in database collections or application logs.</li>
            <li><strong>Immutable Audit Trail:</strong> Cryptographically hash-chained audit events recording administrative operations (correction previews, seat updates, token revocations) with IP addresses and actor identifiers.</li>
          </ul>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-ink">3. What We Never Disclose</h2>
          <p className="text-muted">
            Public verification links (accessed via QR badges or <code className="font-mono text-xs">/verify/t/:token</code>) strictly restrict response payloads to an allowlist of non-confidential attributes: record status, institution name, programme name, academic year, and signature verdict. The student's 12-digit APAAR ID, birth date, contact email, and telephone number are never disclosed publicly.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-ink">4. Cookies and Local Storage</h2>
          <p className="text-muted">
            We use strictly necessary browser storage to maintain session state (JWT authentication tokens), theme preferences (light, dark, or system), and UI language selections. We do not use third-party advertising cookies or cross-site tracking pixels.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-ink">5. Voice Recognition Privacy (Opt-in)</h2>
          <p className="text-muted">
            Voice command input is strictly opt-in and operates through the native browser Web Speech API. Depending on the browser engine (e.g. Google Chrome), voice audio may be converted to text by the browser vendor's speech service. EduSynC servers never record, capture, or store microphone audio streams.
          </p>
        </section>
      </div>
    </div>
  )
}
