import { Link, useLocation } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function ThankYouPage() {
  usePageMeta({
    title: 'Message Transmitted',
    description: 'Confirmation that your inquiry has been received by Team Sentinals.',
    noindex: true,
  })

  const location = useLocation()
  const name = location.state?.name || 'there'

  return (
    <div className="mx-auto max-w-[650px] px-5 py-20 text-center space-y-6">
      <div className="w-16 h-16 rounded-full bg-success-surface text-success-strong border border-success/30 flex items-center justify-center mx-auto text-2xl font-bold">
        &check;
      </div>

      <div className="space-y-2">
        <h1 className="text-3xl font-extrabold text-brand tracking-tight m-0">
          Thank you, {name}!
        </h1>
        <p className="text-muted text-base leading-relaxed">
          Your inquiry has been successfully transmitted to Team Sentinals. We review technical feedback and issue reports regularly during SIH 2026 evaluation.
        </p>
      </div>

      <div className="pt-4 flex justify-center gap-4">
        <Link
          to="/"
          className="px-5 py-2.5 rounded border border-line bg-surface-2 text-ink text-sm font-semibold hover:bg-surface-3 no-underline"
        >
          Return to Overview
        </Link>
        <Link
          to="/login"
          className="px-5 py-2.5 rounded bg-brand text-on-brand text-sm font-semibold hover:opacity-95 no-underline shadow-sm"
        >
          Try Live Demo
        </Link>
      </div>
    </div>
  )
}
