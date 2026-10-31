import { useState } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'

const FAQS = [
  {
    q: 'What is APAAR?',
    a: 'APAAR stands for Automated Permanent Academic Account Registry. It is a 12-digit lifelong academic identifier issued under the Ministry of Education\'s "One Nation, One Student ID" initiative to track degrees, credits, and academic milestones seamlessly across institutions.',
  },
  {
    q: 'What is ChhatraLekha, and is this an official government registry?',
    a: 'ChhatraLekha is an independent educational platform prototype for schools and colleges across India. It is not an official government service. Verification performed on this prototype is checked against its own demonstration database, not the national registry.',
  },
  {
    q: 'What does a public verification token disclose, and what is kept private?',
    a: 'When an employer or third party verifies a credential using a QR badge or link, the response is strictly an allowlist: record status, institution name, programme name, academic year, issue date, and cryptographic verdict. The raw 12-digit APAAR ID, student date of birth, contact phone/email, and full academic dossier are never revealed.',
  },
  {
    q: 'How does the Academic Record Change Impact Detector work?',
    a: 'Whenever an administrator proposes a correction (e.g. changing an academic year, programme, or quota), the engine runs rules CIA-A through CIA-F in preview mode without saving any changes. It previews side-effects on seat counts, dependent tasks, and issued verification tokens. Applying the correction saves a versioned snapshot and flags stale tokens.',
  },
  {
    q: 'Can the platform work offline?',
    a: 'Yes. The Android application (ChhatraLekha Android) is fully offline-first. It packages Room database storage and an in-house dependency-free ISO/IEC 18004 QR encoder/decoder with Reed-Solomon error correction, allowing field inspectors to verify credentials without internet access.',
  },
  {
    q: 'Is real student data processed on this site?',
    a: 'No. The platform strictly uses deterministically generated synthetic demo data. No real personal records, Aadhaar numbers, or authentic government IDs are ever stored or transmitted.',
  },
]

export default function FaqPage() {
  usePageMeta({
    title: 'Frequently Asked Questions',
    description: 'Frequently asked questions regarding APAAR ID verification, ChhatraLekha prototype, privacy policies, and change impact detection.',
    canonical: '/faq',
  })

  const [openIndex, setOpenIndex] = useState(0)

  return (
    <div className="mx-auto max-w-[850px] px-5 py-12 space-y-8">
      <div className="space-y-3">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-brand tracking-tight m-0">
          Frequently Asked Questions
        </h1>
        <p className="text-base text-muted">
          Clear answers about APAAR, verification tokens, data privacy, and the ChhatraLekha architecture.
        </p>
      </div>

      <div className="space-y-3">
        {FAQS.map((faq, idx) => {
          const isOpen = openIndex === idx
          return (
            <div
              key={faq.q}
              className="border border-line rounded bg-surface overflow-hidden transition-colors"
            >
              <button
                type="button"
                onClick={() => setOpenIndex(isOpen ? -1 : idx)}
                className="w-full text-left px-5 py-4 flex items-center justify-between gap-4 font-bold text-ink hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
                aria-expanded={isOpen}
              >
                <span>{faq.q}</span>
                <span className="text-muted font-mono text-lg">{isOpen ? '−' : '+'}</span>
              </button>
              {isOpen && (
                <div className="px-5 pb-5 text-sm text-muted leading-relaxed border-t border-line/50 pt-3">
                  {faq.a}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
