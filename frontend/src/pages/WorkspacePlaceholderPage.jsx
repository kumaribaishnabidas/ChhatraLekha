import { Link } from 'react-router-dom'

export default function WorkspacePlaceholderPage({
  title = 'Module Workspace',
  moduleName = 'Educational Service',
  stageNotice = 'Scheduled for complete workflow rollout in the upcoming development phase.',
  features = [],
}) {
  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
      <div className="flex items-center justify-between border-b border-line pb-4">
        <div>
          <h1 className="m-0 text-xl font-bold text-ink">{title}</h1>
          <p className="m-0 text-xs text-muted mt-0.5">
            ChhatraLekha Unified Education Infrastructure - {moduleName}
          </p>
        </div>
        <span className="px-2.5 py-1 rounded bg-surface-2 border border-line text-xs font-semibold text-brand">
          Stage Roadmap
        </span>
      </div>

      <div className="rounded-lg border border-line bg-surface p-6 shadow-xs space-y-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded bg-brand/10 text-brand flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <div className="space-y-1">
            <h3 className="m-0 text-sm font-bold text-ink">{moduleName} Architecture Specifications Ready</h3>
            <p className="m-0 text-xs text-muted leading-relaxed">
              {stageNotice} The architectural boundaries, API routes, and entity relationship models are documented in the Stage 0 specification.
            </p>
          </div>
        </div>

        {features.length > 0 && (
          <div className="space-y-2 pt-2">
            <h4 className="m-0 text-xs font-bold text-ink uppercase tracking-wider">Planned Capabilities</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              {features.map((feat, idx) => (
                <div key={idx} className="p-2.5 rounded border border-line bg-surface-2 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand" />
                  <span className="text-ink font-medium">{feat}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="pt-4 border-t border-line flex flex-wrap gap-3">
          <Link
            to="/profile"
            className="px-3.5 py-1.5 rounded bg-brand text-white text-xs font-semibold shadow-xs hover:bg-brand-deep no-underline"
          >
            Manage User Profile
          </Link>
          <Link
            to="/me"
            className="px-3.5 py-1.5 rounded bg-surface border border-line text-xs font-semibold text-ink hover:bg-surface-2 no-underline"
          >
            Return to Dashboard
          </Link>
        </div>
      </div>
    </div>
  )
}
