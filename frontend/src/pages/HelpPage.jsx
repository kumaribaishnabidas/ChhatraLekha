import { useState } from 'react'
import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { Card, Button } from '../components/common'

const TOPICS = [
  {
    id: 'students',
    title: 'Students & Families',
    description: 'Claim codes, digital student ID cards, offline QR badges, and consent permissions.',
    items: [
      {
        q: 'How do I claim my student account?',
        a: 'Your school or college administrator generates a single-use claim code (e.g. CL-XXXX-XXXX) valid for 7 days. Sign in to ChhatraLekha, enter your claim code in the Student Portal, and your digital academic identity will be immediately linked.',
      },
      {
        q: 'How does time-bound QR verification protect my personal data?',
        a: 'When an employer or verifying authority scans your QR badge, they receive an opaque verification token. The public verification page displays only your academic status, institution, and certificate validity verdict. Your birth date, phone, and contact details are never disclosed.',
      },
      {
        q: 'How can parents and guardians monitor attendance and results?',
        a: 'Parents sign in to the Parent Portal. Under Section 9 of the DPDP Act 2023, parents can review attendance trends, examination report cards, and school notices without unnecessary data tracking.',
      },
    ],
  },
  {
    id: 'institutions',
    title: 'Institutions & Teachers',
    description: 'Academic setup, CSV student intake, attendance recording, and transfer certificates.',
    items: [
      {
        q: 'How do I onboard students via CSV in bulk?',
        a: 'Navigate to Admissions & Ingestion. Download the canonical template, fill in student records with APAAR IDs or roll numbers, and submit. The system provides a live pre-commit validation preview highlighting any format or capacity issues before writing to the register.',
      },
      {
        q: 'How are student transfer certificates (TC) issued?',
        a: 'Under School Workflows, select the student and choose Issue Transfer Certificate. The platform mints an official TC carrying an Ed25519 cryptographic seal and a verifiable QR token that any receiving school can authenticate.',
      },
      {
        q: 'How does teacher workspace attendance work?',
        a: 'Teachers open the Teacher Workspace, select their class section, mark present/absent states, and submit. Records synchronize in real-time with the central student register and mobile sync queue.',
      },
    ],
  },
  {
    id: 'verifiers',
    title: 'Verifiers & Employers',
    description: 'Scanning credentials, digital seal verification, and offline cryptographic checks.',
    items: [
      {
        q: 'How do I verify a graduate or student credential?',
        a: 'Scan the QR code printed on the certificate or student badge, or open the link directly. The verification engine checks cryptographic signatures and returns an instant PASS, EXPIRED, or REVOKED verdict.',
      },
      {
        q: 'Can credentials be verified offline?',
        a: 'Yes. With the ChhatraLekha Android application, verifiers can inspect credentials offline using built-in public key cryptography without requiring active cellular network connectivity.',
      },
    ],
  },
]

export default function HelpPage() {
  usePageMeta({
    title: 'Help & Support Center',
    description: 'Comprehensive guides, troubleshooting steps, and support contacts for ChhatraLekha students, parents, teachers, and institutions.',
    canonical: '/help',
  })

  const [activeTab, setActiveTab] = useState('students')
  const [searchQuery, setSearchQuery] = useState('')

  const activeTopic = TOPICS.find((t) => t.id === activeTab) || TOPICS[0]

  const filteredItems = activeTopic.items.filter(
    (item) =>
      item.q.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.a.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="mx-auto max-w-[950px] px-5 py-12 space-y-10">
      <div className="space-y-3">
        <h1 className="text-3xl sm:text-5xl font-black text-brand tracking-tight m-0">
          Help &amp; Support Center
        </h1>
        <p className="text-base sm:text-lg text-muted max-w-2xl leading-relaxed m-0">
          Step-by-step guidance for students, guardians, educators, and credential verifiers.
        </p>
      </div>

      <div className="relative">
        <label htmlFor="search-help" className="sr-only">Search help topics</label>
        <input
          id="search-help"
          type="search"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by topic, e.g. claim code, attendance, QR verification..."
          className="w-full px-4 py-3 rounded-lg border border-line bg-surface text-ink text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-brand shadow-sm"
        />
      </div>

      <div className="flex flex-wrap gap-2 border-b border-line pb-3">
        {TOPICS.map((topic) => (
          <button
            key={topic.id}
            type="button"
            onClick={() => {
              setActiveTab(topic.id)
              setSearchQuery('')
            }}
            className={`px-4 py-2 rounded-full text-xs sm:text-sm font-semibold transition-colors cursor-pointer ${
              activeTab === topic.id
                ? 'bg-brand text-on-brand'
                : 'bg-surface-2 text-muted hover:text-ink'
            }`}
          >
            {topic.title}
          </button>
        ))}
      </div>

      <div className="space-y-4">
        <div className="space-y-1">
          <h2 className="text-xl font-bold text-ink m-0">{activeTopic.title}</h2>
          <p className="text-sm text-muted m-0">{activeTopic.description}</p>
        </div>

        {filteredItems.length === 0 ? (
          <Card className="p-8 text-center text-muted">
            <p className="m-0 text-sm">No matching guides found for "{searchQuery}".</p>
            <Button
              variant="outline"
              className="mt-3 text-xs"
              onClick={() => setSearchQuery('')}
            >
              Clear search
            </Button>
          </Card>
        ) : (
          filteredItems.map((item) => (
            <Card key={item.q} className="p-5 space-y-2 bg-surface">
              <h3 className="text-base font-bold text-brand-deep m-0">{item.q}</h3>
              <p className="text-sm text-muted leading-relaxed m-0">{item.a}</p>
            </Card>
          ))
        )}
      </div>

      <Card className="p-6 sm:p-8 bg-surface-2 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div className="space-y-1 max-w-xl">
          <h2 className="text-lg font-bold text-ink m-0">Need personalized technical assistance?</h2>
          <p className="text-sm text-muted m-0 leading-relaxed">
            Our grievance officer and support team respond to inquiries from institutions, students, and verifiers.
          </p>
        </div>
        <div className="flex flex-wrap gap-3 shrink-0">
          <Link to="/contact" className="no-underline">
            <Button variant="primary">Contact Support</Button>
          </Link>
          <Link to="/faq" className="no-underline">
            <Button variant="outline">Browse All FAQs</Button>
          </Link>
        </div>
      </Card>
    </div>
  )
}

