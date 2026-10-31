import { usePageMeta } from '../hooks/usePageMeta'

export default function TermsPage() {
  usePageMeta({
    title: 'Terms of Service',
    description: 'Terms of service and prototype usage conditions for ChhatraLekha.',
    canonical: '/terms',
  })

  return (
    <div className="mx-auto max-w-[850px] px-5 py-12 space-y-8">
      <div className="space-y-3">
        <div className="inline-block px-3 py-1 rounded bg-warning-surface text-warning-strong border border-warning/40 text-xs font-semibold">
          Draft for the prototype &middot; Needs legal review
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-brand tracking-tight m-0">
          Terms of Service
        </h1>
        <p className="text-sm text-muted">Last updated: October 2026</p>
      </div>

      <div className="space-y-6 text-sm sm:text-base leading-relaxed text-ink border-t border-line pt-6">
        <section className="space-y-2">
          <h2 className="text-lg font-bold text-ink">1. Acceptance of Prototype Conditions</h2>
          <p className="text-muted">
            By accessing or interacting with the ChhatraLekha demonstration portal, you acknowledge that this software is an architectural prototype created for technical demonstration and evaluation.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-ink">2. No Official Government or Registry Status</h2>
          <p className="text-muted">
            ChhatraLekha is an independent educational prototype and is not an official portal of the Ministry of Education, AICTE, CBSE, state education boards, or the Government of India. Verifications, QR badges, and downloadable credentials are demonstration proofs issued for prototype verification only.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-ink">3. Acceptable Use</h2>
          <p className="text-muted">
            Users agree not to attempt unauthorized penetration testing, denial-of-service disruptions, injection of malicious payloads into CSV batch imports, or upload of authentic personal confidential information to this demonstration platform.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-ink">4. Disclaimer of Warranties</h2>
          <p className="text-muted">
            The platform is provided on an "as is" and "as available" basis without warranties of uninterrupted availability, commercial fitness, or regulatory certification.
          </p>
        </section>
      </div>
    </div>
  )
}
