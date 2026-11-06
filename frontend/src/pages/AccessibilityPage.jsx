import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { Card, Badge } from '../components/common'

export default function AccessibilityPage() {
  usePageMeta({
    title: 'Accessibility Statement',
    description: 'ChhatraLekha is committed to digital inclusion across all 22 scheduled Indian languages, assistive technologies, and diverse abilities.',
    canonical: '/accessibility',
  })

  return (
    <div className="mx-auto max-w-[1000px] px-5 py-12 space-y-10">
      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 rounded-full border border-accent/40 bg-accent/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-accent-strong">
          <span className="h-2 w-2 rounded-full bg-accent" aria-hidden="true" />
          Digital Inclusion Charter
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-brand tracking-tight m-0">
          Accessibility Statement
        </h1>
        <p className="text-base sm:text-lg text-muted max-w-2xl leading-relaxed m-0">
          ChhatraLekha is designed to ensure equitable access to educational records for all students, parents, and educators across India, regardless of ability, device, or regional language.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="p-6 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-ink m-0">WCAG 2.1 AA Conformance</h2>
            <Badge variant="success">Standard</Badge>
          </div>
          <p className="text-sm text-muted leading-relaxed m-0">
            Our user interfaces are engineered to comply with the Web Content Accessibility Guidelines (WCAG) 2.1 Level AA standards, ensuring high contrast, clear focus indicators, and semantic HTML elements.
          </p>
        </Card>

        <Card className="p-6 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-ink m-0">22 Scheduled Indian Languages</h2>
            <Badge variant="info">Multilingual</Badge>
          </div>
          <p className="text-sm text-muted leading-relaxed m-0">
            Native typographic font rendering and localization support for all 22 official Indian languages, preventing broken glyphs and supporting right-to-left (RTL) Urdu script.
          </p>
        </Card>

        <Card className="p-6 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-ink m-0">Keyboard Navigation &amp; Focus</h2>
            <Badge variant="neutral">Interactive</Badge>
          </div>
          <p className="text-sm text-muted leading-relaxed m-0">
            Every interactive control, modal, form input, and accordion panel is fully operable via keyboard navigation. Use Tab and Shift-Tab to traverse, and Space/Enter to activate.
          </p>
        </Card>

        <Card className="p-6 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-ink m-0">Voice &amp; Audio Assistance</h2>
            <Badge variant="warning">Assistive</Badge>
          </div>
          <p className="text-sm text-muted leading-relaxed m-0">
            Built-in speech synthesis and voice input support navigation and text-to-speech reading for users with visual impairments or reading difficulties.
          </p>
        </Card>
      </div>

      <Card className="p-6 sm:p-8 space-y-4">
        <h2 className="text-xl font-bold text-ink m-0">Platform Keyboard Shortcuts</h2>
        <p className="text-sm text-muted m-0">
          The following global keyboard shortcuts are supported across all ChhatraLekha pages:
        </p>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Key Combo</th>
                <th>Action</th>
                <th>Context</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><kbd className="px-2 py-0.5 rounded bg-surface-2 border border-line text-xs font-mono">Alt + /</kbd></td>
                <td>Open Keyboard Shortcuts Modal</td>
                <td>Global</td>
              </tr>
              <tr>
                <td><kbd className="px-2 py-0.5 rounded bg-surface-2 border border-line text-xs font-mono">Alt + H</kbd></td>
                <td>Navigate to Home / Overview</td>
                <td>Global</td>
              </tr>
              <tr>
                <td><kbd className="px-2 py-0.5 rounded bg-surface-2 border border-line text-xs font-mono">Alt + D</kbd></td>
                <td>Open Demo Persona Selector</td>
                <td>Landing &amp; Login</td>
              </tr>
              <tr>
                <td><kbd className="px-2 py-0.5 rounded bg-surface-2 border border-line text-xs font-mono">Esc</kbd></td>
                <td>Close Drawer / Modal Dialog</td>
                <td>Global</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>

      <div className="p-6 rounded-lg bg-surface-2 border border-line flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-ink m-0">Need Accessibility Assistance?</h3>
          <p className="text-sm text-muted m-0 mt-1">
            If you encounter any accessibility barriers while using ChhatraLekha, please let our team know.
          </p>
        </div>
        <Link to="/contact" className="btn btn-navy text-sm font-semibold no-underline shrink-0">
          Contact Accessibility Team
        </Link>
      </div>
    </div>
  )
}

