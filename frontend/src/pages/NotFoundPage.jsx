import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function NotFoundPage() {
  usePageMeta({
    title: 'Page Not Found (404)',
    description: 'The requested resource was not found on ChhatraLekha.',
    noindex: true,
  })

  return (
    <div className="mx-auto max-w-[650px] px-5 py-24 text-center space-y-6">
      <div className="text-6xl font-black text-brand tracking-tighter">404</div>
      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-ink tracking-tight m-0">Resource Not Found</h1>
        <p className="text-sm text-muted max-w-[45ch] mx-auto">
          The requested path does not exist on this ChhatraLekha deployment. Please verify the URL or navigate to one of the main sections below.
        </p>
      </div>

      <div className="flex flex-wrap justify-center gap-4 pt-4">
        <Link
          to="/"
          className="px-5 py-2.5 rounded bg-brand text-on-brand text-sm font-semibold hover:opacity-95 no-underline shadow-sm"
        >
          Return to Overview
        </Link>
        <Link
          to="/login"
          className="px-5 py-2.5 rounded border border-line bg-surface-2 text-ink text-sm font-semibold hover:bg-surface-3 no-underline"
        >
          Sign In / Demo
        </Link>
        <Link
          to="/faq"
          className="px-5 py-2.5 rounded border border-line bg-surface-2 text-ink text-sm font-semibold hover:bg-surface-3 no-underline"
        >
          View FAQ
        </Link>
      </div>
    </div>
  )
}
