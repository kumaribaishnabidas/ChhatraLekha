import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function AboutPage() {
  usePageMeta({
    title: 'About the Platform',
    description: 'Overview of the ChhatraLekha APAAR Verification architecture, technical specifications, and system design.',
    canonical: '/about',
  })

  return (
    <div className="mx-auto max-w-[900px] px-5 py-12 space-y-10">
      <div className="space-y-3">
        <div className="text-xs font-bold uppercase tracking-wider text-accent-strong">
          Academic Record Verification
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-brand tracking-tight m-0">
          About ChhatraLekha
        </h1>
        <p className="text-base text-muted leading-relaxed">
          The Automated Permanent Academic Account Registry (APAAR) was established under the Ministry of Education's <em>One Nation, One Student ID</em> initiative to act as an all-India lifelong academic identifier.
        </p>
      </div>

      <div className="p-4 rounded border border-warning/40 bg-warning-surface text-warning-strong text-sm">
        <strong>Notice:</strong> ChhatraLekha is an academic verification prototype. Verification performed through this site is checked against this prototype's synthetic database and is not official APAAR or AICTE verification.
      </div>

      <div className="space-y-6 text-sm sm:text-base leading-relaxed text-ink">
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-ink">The Operational Challenge</h2>
          <p>
            In practice, institutional student onboarding and regulatory seat reconciliation have traditionally been processed manually or through siloed batch uploads. This operational gap creates recurring vulnerabilities:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-muted">
            <li>Syntactically malformed identifiers and placeholder entries.</li>
            <li>Institutions quietly filling student admissions beyond sanctioned course intake ceilings.</li>
            <li>Abuse of supernumerary quota reservations (NRI, OCI, Foreign National, TFW).</li>
            <li>Duplicate simultaneous enrollments of the same APAAR ID across different institutions or degree programmes.</li>
            <li>Inability of third-party verifiers to check academic records offline or without exposing private student identities.</li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-ink">The Solution Architecture</h2>
          <p>
            ChhatraLekha provides a unified platform comprising a modern web portal (React 19 + Tailwind CSS 4), an asynchronous high-performance backend (FastAPI + Motor async MongoDB), and an offline-first native Android client (Kotlin + Jetpack Compose + Room).
          </p>
          <p>
            Crucially, the validation rules, cryptographic seal structure, and anomaly algorithms are specified identically in both Python and Kotlin. A credential verified on an offline Android device and a credential checked on the central web portal will always reach the exact same verdict.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-ink">Synthetic Data &amp; Security Principles</h2>
          <p>
            This system enforces complete privacy: no real citizen identification numbers, real names, or live Aadhaar-linked records are ever stored or processed. The platform operates entirely on deterministically generated synthetic data for demonstration and testing.
          </p>
        </section>

        <section className="space-y-3 pt-4 border-t border-line">
          <h2 className="text-xl font-bold text-ink">Project Information</h2>
          <p className="text-muted">
            Built as an academic record reconciliation and fraud prevention platform. For queries regarding the system architecture or technical reports, visit our <Link to="/contact" className="text-brand font-medium">contact page</Link>.
          </p>
        </section>
      </div>
    </div>
  )
}
