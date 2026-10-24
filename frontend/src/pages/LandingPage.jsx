import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function LandingPage() {
  usePageMeta({
    title: 'Overview',
    description: 'APAAR ID Student Data Management & Verification Platform for AICTE-approved institutions.',
    canonical: '/',
  })

  return (
    <div className="space-y-16 py-8">
      {/* Hero Section */}
      <section className="mx-auto max-w-[1200px] px-5">
        <div className="bg-surface border border-line rounded p-8 sm:p-12 shadow-sm relative overflow-hidden">
          <div className="max-w-[70ch] space-y-5">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-accent/15 text-accent-strong border border-accent/30">
              <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
              Academic Credential Management &middot; Tamper-Evident Verification
            </div>

            <h1 className="text-3xl sm:text-5xl font-black text-brand tracking-tight leading-tight">
              Automated Permanent Academic Account Registry Verification
            </h1>

            <p className="text-base sm:text-lg text-muted leading-relaxed">
              EduSynC eliminates academic reconciliation fraud across institutions with a 10-layer anomaly engine, cryptographic tamper-evident seals, and an Academic Record Change Impact Detector.
            </p>

            <div className="p-4 rounded border border-warning/40 bg-warning-surface text-warning-strong text-xs sm:text-sm">
              <strong>Notice:</strong> Verification against this prototype's database, not official APAAR or AICTE verification. Synthetic demo records only.
            </div>

            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Link
                to="/login"
                className="px-6 py-3 rounded bg-brand text-on-brand font-semibold text-sm hover:opacity-95 transition-opacity no-underline shadow-sm"
              >
                Sign In &amp; Try Live Demo
              </Link>
              <Link
                to="/verify/t/demo"
                className="px-6 py-3 rounded border border-line bg-surface-2 text-ink font-semibold text-sm hover:bg-surface-3 transition-colors no-underline"
              >
                Verify a Token Badge
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Synthetic Dataset Metrics */}
      <section className="mx-auto max-w-[1200px] px-5">
        <div className="border border-line rounded bg-surface p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-muted m-0">
              Live Seeded Dataset Statistics (Synthetic Demo Data)
            </h2>
            <span className="text-xs px-2 py-0.5 rounded bg-info-surface text-info-strong font-semibold">
              Deterministic
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded bg-surface-2 border border-line">
              <div className="text-2xl sm:text-3xl font-extrabold text-brand">12</div>
              <div className="text-xs text-muted mt-1">Institutions Registered</div>
            </div>
            <div className="p-4 rounded bg-surface-2 border border-line">
              <div className="text-2xl sm:text-3xl font-extrabold text-brand">60</div>
              <div className="text-xs text-muted mt-1">Sanctioned Programmes</div>
            </div>
            <div className="p-4 rounded bg-surface-2 border border-line">
              <div className="text-2xl sm:text-3xl font-extrabold text-brand">~1,900</div>
              <div className="text-xs text-muted mt-1">Enrolled Students</div>
            </div>
            <div className="p-4 rounded bg-surface-2 border border-line">
              <div className="text-2xl sm:text-3xl font-extrabold text-danger-strong">24</div>
              <div className="text-xs text-muted mt-1">Seeded Active Anomalies</div>
            </div>
          </div>
        </div>
      </section>

      {/* Core Architectural Pillars */}
      <section className="mx-auto max-w-[1200px] px-5 space-y-6">
        <div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-ink tracking-tight m-0">
            Four Layers of Academic Integrity
          </h2>
          <p className="text-muted text-sm mt-1">
            Deterministic rule-based engines running without LLM hallucination or external API dependencies.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded border border-line bg-surface space-y-3">
            <div className="text-xs font-bold uppercase text-accent-strong tracking-wider">Engine 01</div>
            <h3 className="text-lg font-bold text-ink m-0">10-Layer Anomaly Detection</h3>
            <p className="text-sm text-muted leading-relaxed m-0">
              Evaluates incoming student intakes against syntactic Luhn rules, cross-institution duplicate enrollment, duplicate roll numbers, sanctioned seat breaches, and quota ceilings (NRI 5%, OCI/FN 15%, TFW 5%, PMSSS).
            </p>
          </div>

          <div className="p-6 rounded border border-line bg-surface space-y-3">
            <div className="text-xs font-bold uppercase text-accent-strong tracking-wider">Engine 02</div>
            <h3 className="text-lg font-bold text-ink m-0">Academic Record Change Impact Detector</h3>
            <p className="text-sm text-muted leading-relaxed m-0">
              Evaluates proposed corrections against rules CIA-A through CIA-F before writing. Predicts side effects on seat capacity, dependent registrations, and issued credentials without silent edits.
            </p>
          </div>

          <div className="p-6 rounded border border-line bg-surface space-y-3">
            <div className="text-xs font-bold uppercase text-accent-strong tracking-wider">Engine 03</div>
            <h3 className="text-lg font-bold text-ink m-0">Tamper-Evident Cryptographic Seals</h3>
            <p className="text-sm text-muted leading-relaxed m-0">
              Generates cryptographic HMAC-SHA256 and Ed25519 digital signatures derived directly from immutable enrollment facts, verifiable offline on phone or server.
            </p>
          </div>

          <div className="p-6 rounded border border-line bg-surface space-y-3">
            <div className="text-xs font-bold uppercase text-accent-strong tracking-wider">Engine 04</div>
            <h3 className="text-lg font-bold text-ink m-0">Opaque Revocable Verification Tokens</h3>
            <p className="text-sm text-muted leading-relaxed m-0">
              Public QR badges carry high-entropy, expiring, revocable tokens. Verification endpoints disclose an allowlist (status, institution, program) without exposing raw APAAR IDs or date of birth.
            </p>
          </div>
        </div>
      </section>

      {/* Demo Walkthrough CTA */}
      <section className="mx-auto max-w-[1200px] px-5">
        <div className="p-8 rounded bg-surface-2 border border-line flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-ink m-0">Experience the System Firsthand</h2>
            <p className="text-sm text-muted m-0">
              Sign in with pre-seeded test accounts for AICTE Directorate, Institution Admin, or Verifier.
            </p>
          </div>
          <Link
            to="/login"
            className="px-6 py-3 rounded bg-brand text-on-brand font-semibold text-sm hover:opacity-95 transition-opacity whitespace-nowrap no-underline"
          >
            Go to Sign In &rarr;
          </Link>
        </div>
      </section>
    </div>
  )
}
