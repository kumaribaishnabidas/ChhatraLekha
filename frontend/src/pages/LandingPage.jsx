import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { Button, Card } from '../components/common'

const features = [
  ['01', 'Digital ID', 'A portable academic identity that keeps the student record clear, current, and easy to present.'],
  ['02', 'Academic Wallet', 'Keep credentials, certificates, and verification history together in one trusted place.'],
  ['03', 'QR Verification', 'Share a time-bound QR credential without exposing personal data on the public page.'],
  ['04', 'Fraud Detection', 'Surface duplicate enrolments, quota breaches, and suspicious changes before they spread.'],
  ['05', 'Audit Trail', 'Every consent, review, correction, and verification stays traceable for accountable decisions.'],
]

export default function LandingPage() {
  usePageMeta({
    title: 'Authenticate · Verify · Empower',
    description: 'ChhatraLekha is a trusted digital academic identity for every student.',
    canonical: '/',
  })

  return (
    <div className="space-y-16 pb-10">
      <section className="relative overflow-hidden bg-surface-2">
        <div className="mx-auto grid max-w-[1200px] gap-10 px-5 py-14 sm:py-20 lg:grid-cols-[1.15fr_.85fr] lg:items-center">
          <div className="relative z-10 space-y-6">
            <img src="/brand/chhatralekha-logo.png" alt="ChhatraLekha - Authenticate, Verify, Empower" className="h-auto w-full max-w-[420px] object-contain object-left" />
            <div className="inline-flex items-center gap-2 rounded-full border border-accent/40 bg-accent/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-accent-strong">
              <span className="h-2 w-2 rounded-full bg-accent" aria-hidden="true" />
              Trusted digital academic identity
            </div>
            <h1 className="m-0 max-w-[12ch] text-4xl font-black leading-tight text-brand-deep sm:text-6xl">
              One trusted record for every student.
            </h1>
            <p className="m-0 max-w-[60ch] text-base leading-relaxed text-muted sm:text-lg">
              Authenticate academic records, verify credentials, and empower students to share proof of learning with confidence.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link to="/verify/t/demo" className="no-underline"><Button variant="accent">Verify a credential</Button></Link>
              <Link to="/early-access" className="no-underline"><Button variant="secondary">Apply for early access</Button></Link>
              <Link to="/login" className="no-underline"><Button variant="primary">Sign in</Button></Link>
            </div>
            <p className="m-0 text-xs text-muted">Prototype only - not official government or registry verification.</p>
          </div>
          <div className="relative">
            <div className="absolute -right-20 -top-20 h-72 w-72 rounded-full bg-accent/15 blur-3xl" aria-hidden="true" />
            <div className="relative rounded-lg border border-line bg-surface p-6 shadow-[0_24px_70px_var(--app-shadow-strong)]">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <p className="m-0 text-xs font-bold uppercase tracking-widest text-muted">Credential journey</p>
                  <p className="m-0 mt-1 text-lg font-bold text-brand-deep">Upload → Verify → Share</p>
                </div>
                <span className="rounded-full bg-success-surface px-3 py-1 text-xs font-bold text-success-strong">Protected</span>
              </div>
              <div className="grid gap-3">
                {['Upload academic proof', 'Run a trusted verification', 'Share a private QR credential'].map((step, index) => (
                  <div key={step} className="flex items-center gap-3 rounded-lg border border-line bg-surface-2 p-4">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-black text-on-brand">{index + 1}</span>
                    <span className="font-semibold text-ink">{step}</span>
                  </div>
                ))}
              </div>
              <div className="mt-6 rounded-lg bg-brand p-5 text-on-brand">
                <p className="m-0 text-xs font-bold uppercase tracking-widest text-white/70">Privacy by design</p>
                <p className="m-0 mt-2 text-lg font-bold">Public verification shows the credential, not the person.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-[1200px] px-5">
        <div className="mb-6 max-w-2xl">
          <p className="m-0 text-xs font-bold uppercase tracking-widest text-accent-strong">Built for the full academic journey</p>
          <h2 className="m-0 mt-2 text-3xl font-black text-brand-deep">A calmer way to prove what you have earned.</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {features.map(([number, title, description]) => (
            <Card key={title} className="p-5 transition-transform hover:-translate-y-1">
              <span className="text-xs font-black tracking-widest text-accent-strong">{number}</span>
              <h3 className="m-0 mt-8 text-lg">{title}</h3>
              <p className="m-0 mt-2 text-sm leading-relaxed text-muted">{description}</p>
            </Card>
          ))}
        </div>
      </section>

      <section className="bg-brand py-12 text-on-brand">
        <div className="mx-auto grid max-w-[1200px] gap-6 px-5 lg:grid-cols-[1fr_auto] lg:items-center">
          <div>
            <p className="m-0 text-xs font-bold uppercase tracking-widest text-white/70">Trust and security</p>
            <h2 className="m-0 mt-2 text-3xl font-black text-white">Make every academic handoff accountable.</h2>
            <p className="m-0 mt-3 max-w-2xl text-sm leading-relaxed text-white/80">ChhatraLekha keeps consent, verification, and record changes visible to the people responsible for them.</p>
          </div>
          <Link to="/about" className="no-underline"><Button variant="accent">Explore the platform</Button></Link>
        </div>
      </section>

      <section className="mx-auto max-w-[1200px] px-5">
        <Card className="flex flex-col gap-5 bg-surface-2 p-7 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="m-0 text-2xl">Ready to verify with confidence?</h2>
            <p className="m-0 mt-2 text-sm text-muted">Try the prototype with a seeded demo account or scan a sample credential.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to="/early-access" className="no-underline"><Button variant="accent">Request early access</Button></Link>
            <Link to="/login" className="no-underline"><Button>Open the workspace</Button></Link>
            <Link to="/verify/t/demo" className="no-underline"><Button variant="secondary">Try verification</Button></Link>
          </div>
        </Card>
      </section>
    </div>
  )
}
