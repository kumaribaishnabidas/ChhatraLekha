import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function ContactPage() {
  usePageMeta({
    title: 'Contact & Feedback',
    description: 'Get in touch regarding the ChhatraLekha prototype, bug reports, or technical inquiries.',
    canonical: '/contact',
  })

  const navigate = useNavigate()
  const contactEmail = import.meta.env.VITE_CONTACT_EMAIL || 'contact@chhatralekha.example'
  const contactAddress = import.meta.env.VITE_CONTACT_ADDRESS || ''

  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!form.name.trim() || !form.email.trim() || !form.message.trim()) {
      setError('Please provide your name, email address, and message.')
      return
    }
    setError('')
    setSubmitting(true)

    // Simulate sending message
    setTimeout(() => {
      setSubmitting(false)
      navigate('/thank-you', { state: { name: form.name, email: form.email } })
    }, 600)
  }

  return (
    <div className="mx-auto max-w-[850px] px-5 py-12 space-y-8">
      <div className="space-y-3">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-brand tracking-tight m-0">
          Contact Us
        </h1>
        <p className="text-base text-muted">
          Have questions regarding the ChhatraLekha verification prototype or need to report a defect? Send us a note below.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2">
          <form onSubmit={handleSubmit} className="border border-line rounded bg-surface p-6 space-y-4">
            {error && (
              <div role="alert" className="p-3 rounded border border-danger/40 bg-danger-surface text-danger-strong text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="name" className="block text-xs font-bold uppercase tracking-wider text-muted mb-1">
                Your Name <span className="text-danger-strong">*</span>
              </label>
              <input
                id="name"
                type="text"
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-brand text-sm"
                placeholder="Jane Doe"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-xs font-bold uppercase tracking-wider text-muted mb-1">
                Email Address <span className="text-danger-strong">*</span>
              </label>
              <input
                id="email"
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-brand text-sm"
                placeholder="jane@example.com"
              />
            </div>

            <div>
              <label htmlFor="subject" className="block text-xs font-bold uppercase tracking-wider text-muted mb-1">
                Subject
              </label>
              <input
                id="subject"
                type="text"
                value={form.subject}
                onChange={(e) => setForm({ ...form, subject: e.target.value })}
                className="w-full px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-brand text-sm"
                placeholder="Inquiry / Technical feedback"
              />
            </div>

            <div>
              <label htmlFor="message" className="block text-xs font-bold uppercase tracking-wider text-muted mb-1">
                Message <span className="text-danger-strong">*</span>
              </label>
              <textarea
                id="message"
                required
                rows={5}
                value={form.message}
                onChange={(e) => setForm({ ...form, message: e.target.value })}
                className="w-full px-3 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-brand text-sm"
                placeholder="Describe your inquiry..."
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 px-4 rounded bg-brand text-on-brand font-semibold text-sm hover:opacity-95 transition-opacity disabled:opacity-50"
            >
              {submitting ? 'Transmitting...' : 'Send Message'}
            </button>
          </form>
        </div>

        <div className="space-y-6">
          <div className="p-5 rounded border border-line bg-surface-2 space-y-2">
            <h2 className="text-sm font-bold uppercase tracking-wider text-ink m-0">Direct Email</h2>
            <p className="text-sm font-mono text-muted break-all m-0">
              {contactEmail}
            </p>
          </div>

          {contactAddress && (
            <div className="p-5 rounded border border-line bg-surface-2 space-y-2">
              <h2 className="text-sm font-bold uppercase tracking-wider text-ink m-0">Postal Address</h2>
              <p className="text-sm text-muted m-0 whitespace-pre-line">
                {contactAddress}
              </p>
            </div>
          )}

          <div className="p-5 rounded border border-line bg-surface-2 space-y-2">
            <h2 className="text-sm font-bold uppercase tracking-wider text-ink m-0">Prototype Status</h2>
            <p className="text-xs text-muted m-0">
              Academic verification prototype. Messages are reviewed by the project maintainers.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
