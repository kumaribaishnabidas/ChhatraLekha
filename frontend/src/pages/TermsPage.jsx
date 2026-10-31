import { Link } from 'react-router-dom'
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
        <h1 className="text-3xl sm:text-5xl font-black text-brand tracking-tight m-0">
          Terms of Service
        </h1>
        <p className="text-sm text-muted m-0">Last updated: October 2026 &middot; Subject to institutional counsel review before live production deployment</p>
      </div>

      <div className="space-y-8 text-sm sm:text-base leading-relaxed text-ink border-t border-line pt-6">
        <section className="space-y-2">
          <h2 className="text-lg font-bold text-brand-deep m-0">1. Acceptance of Prototype Conditions</h2>
          <p className="text-muted m-0">
            By accessing or interacting with the ChhatraLekha portal, mobile application, or APIs, you acknowledge that this software is an educational prototype and reference implementation. You agree to use it in accordance with these Terms and applicable laws of India.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-brand-deep m-0">2. Free Access Model &amp; Non-Commercial Pledge</h2>
          <p className="text-muted m-0">
            ChhatraLekha is provided as a public-benefit educational service. It is completely free for all students, parents, teachers, schools, polytechnics, and colleges. There are no subscription tiers, hidden fees, advertising sponsorships, or commercial sales of student records.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-brand-deep m-0">3. Independent Educational Prototype Status</h2>
          <p className="text-muted m-0">
            ChhatraLekha is an independent educational platform prototype for schools and colleges across India. It is not an official portal of the Ministry of Education, AICTE, CBSE, state education boards, DigiLocker, or the Government of India. Verifications, QR badges, and certificates issued by this prototype are verified against its demonstration and participating institutional databases, not the central national registry.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-brand-deep m-0">4. User Responsibilities &amp; Acceptable Use</h2>
          <ul className="list-disc pl-5 space-y-1.5 text-muted m-0">
            <li><strong>Institutional Integrity:</strong> Institutional administrators and educators must provide accurate enrollment details, seat allocations, and program codes.</li>
            <li><strong>Protection of Minors:</strong> Users agree not to attempt unauthorized access to minor student dossiers or circumvent guardian consent boundaries.</li>
            <li><strong>System Security:</strong> Users agree not to conduct automated denial-of-service probing, SQL/NoSQL injection, or exploit testing on demonstration infrastructure.</li>
          </ul>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-brand-deep m-0">5. Intellectual Property &amp; Open Architecture</h2>
          <p className="text-muted m-0">
            The ChhatraLekha software architecture, cryptographic seal specifications, and open-source components are maintained for academic research, transparency, and interoperability. Institutions retain exclusive intellectual property and ownership over their respective student registers and marks.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-brand-deep m-0">6. Disclaimer of Warranties &amp; Limitation of Liability</h2>
          <p className="text-muted m-0">
            The platform is provided on an "as is" and "as available" basis without warranties of any kind, whether express, statutory, or implied. To the maximum extent permitted under Indian law, the project maintainers shall not be liable for incidental, special, or consequential damages resulting from the use or inability to use this prototype.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-brand-deep m-0">7. Governing Law &amp; Jurisdiction</h2>
          <p className="text-muted m-0">
            These terms shall be governed by and construed in accordance with the laws of India, including the Information Technology Act 2000 and the Digital Personal Data Protection Act 2023.
          </p>
        </section>
      </div>

      <div className="pt-4 border-t border-line flex flex-wrap gap-4 text-xs text-muted">
        <Link to="/privacy" className="text-brand underline hover:text-brand-deep">Privacy Policy</Link>
        <Link to="/contact" className="text-brand underline hover:text-brand-deep">Contact Desk</Link>
        <Link to="/transparency" className="text-brand underline hover:text-brand-deep">Public Benefit Charter</Link>
      </div>
    </div>
  )
}
