import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function PrivacyPage() {
  usePageMeta({
    title: 'Privacy Policy',
    description: 'Privacy policy and data governance practices of ChhatraLekha under the Digital Personal Data Protection Act 2023.',
    canonical: '/privacy',
  })

  return (
    <div className="mx-auto max-w-[850px] px-5 py-12 space-y-8">
      <div className="space-y-3">
        <div className="inline-block px-3 py-1 rounded bg-warning-surface text-warning-strong border border-warning/40 text-xs font-semibold">
          Draft for the prototype &middot; Aligned with DPDP Act 2023
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-brand tracking-tight m-0">
          Privacy Policy
        </h1>
        <p className="text-sm text-muted m-0">Last updated: October 2026 &middot; Subject to institutional counsel review before live production deployment</p>
      </div>

      <div className="space-y-8 text-sm sm:text-base leading-relaxed text-ink border-t border-line pt-6">
        <section className="space-y-2">
          <h2 className="text-lg font-bold text-brand-deep m-0">1. Purpose and Scope</h2>
          <p className="text-muted m-0">
            ChhatraLekha is a public-benefit, multi-tenant digital academic identity and operations platform serving schools, colleges, polytechnics, students, parents, and educators across India. This policy details how student and operational data is handled with strict privacy safeguards, zero commercial advertising, and zero data monetization.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-brand-deep m-0">2. Personal Data Processed and Purpose</h2>
          <ul className="list-disc pl-5 space-y-1.5 text-muted m-0">
            <li><strong>Academic Identity Attributes:</strong> Student name, institution roll number, simulated or issued APAAR ID, academic program, grade level, section, and enrollment dates for maintaining institutional registers.</li>
            <li><strong>Minor &amp; Guardian Information:</strong> Guardian name, relationship, and contact details for statutory communications and parental consent verification under Section 9 of the DPDP Act 2023.</li>
            <li><strong>Academic Performance &amp; Attendance:</strong> Class attendance records and assessment marks strictly accessible to the respective student, guardian, teacher, and school leadership.</li>
            <li><strong>Opaque Verification Handles:</strong> High-entropy cryptographic SHA-256 digests of temporary verification tokens. Plaintext tokens expire automatically and cannot be replayed.</li>
            <li><strong>Cryptographic Audit Events:</strong> Hash-chained logs of administrative actions, correction previews, and token issuances for institutional integrity.</li>
          </ul>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-brand-deep m-0">3. Protection of Minors (Children Under 18)</h2>
          <p className="text-muted m-0">
            In compliance with the Indian Digital Personal Data Protection Act 2023, ChhatraLekha enforces enhanced protections for school students who are minors:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-muted m-0">
            <li>No personal data of minors is ever made publicly accessible.</li>
            <li>Parental or lawful guardian consent is mandatory before activating digital student profiles.</li>
            <li>Zero tracking, behavioral profiling, or advertising targeting children.</li>
            <li>Student telephone and email attributes are strictly masked on all external verification views.</li>
          </ul>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-brand-deep m-0">4. Public Verification Allowlist Privacy</h2>
          <p className="text-muted m-0">
            When a third party verifies a credential using a QR badge or link (<code className="font-mono text-xs">/verify/t/:token</code>), the system returns strictly an <strong>allowlist of non-confidential attributes</strong>: credential status, issuing institution name, program or grade, academic session, issue timestamp, and digital signature verdict. The student's 12-digit APAAR ID, birth date, contact address, and contact numbers are never disclosed.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-brand-deep m-0">5. Data Retention &amp; Deletion</h2>
          <p className="text-muted m-0">
            Academic records are retained during a student's active enrollment and for statutory archival periods mandated by the respective education board or university. When a student transfers or withdraws, their status is updated to WITHDRAWN or TRANSFERRED, preventing active enumeration. Institutions retain sole ownership and authority to request data expungement or export.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-brand-deep m-0">6. Third-Party Services &amp; Cookies</h2>
          <p className="text-muted m-0">
            We do not share, lease, or monetize data with third-party advertisers, data brokers, or marketing networks. Browser storage is used solely for strictly necessary session management (JWT tokens), theme preference, and language selection. No third-party tracking pixels or marketing cookies are loaded.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-brand-deep m-0">7. Data Principal Rights &amp; Grievance Redressal</h2>
          <p className="text-muted m-0">
            Under Indian law, data principals (students, parents, and educators) have rights of access, correction of inaccurate records, grievance redressal, and nomination.
          </p>
          <div className="p-4 rounded-lg border border-line bg-surface-2 space-y-1">
            <p className="text-xs font-bold uppercase tracking-wider text-brand m-0">Grievance &amp; Data Protection Officer</p>
            <p className="text-xs text-muted m-0">Office of Grievance Redressal, ChhatraLekha Platform</p>
            <p className="text-xs font-mono text-ink m-0">grievance@chhatralekha.in</p>
            <p className="text-xs text-muted m-0 pt-1">
              Grievances receive an acknowledgment within 48 hours and formal resolution within 30 days.
            </p>
          </div>
        </section>
      </div>

      <div className="pt-4 border-t border-line flex flex-wrap gap-4 text-xs text-muted">
        <Link to="/terms" className="text-brand underline hover:text-brand-deep">Terms of Service</Link>
        <Link to="/contact" className="text-brand underline hover:text-brand-deep">Contact Desk</Link>
        <Link to="/transparency" className="text-brand underline hover:text-brand-deep">Sustainability &amp; Public Benefit Charter</Link>
      </div>
    </div>
  )
}