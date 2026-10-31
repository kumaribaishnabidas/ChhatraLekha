import { useTranslation } from 'react-i18next'
import { Card } from '../components/common'
import PageHeader from '../components/layout/PageHeader'

export default function TransparencyPage() {
  const { t } = useTranslation()

  const sustainabilityPillars = [
    {
      title: 'Grants and Public-Interest Funding',
      description: 'Digital inclusion, open-source education, and accessible digital infrastructure research grants.',
    },
    {
      title: 'Corporate Social Responsibility (CSR)',
      description: 'Transparent computing and server infrastructure grants with strictly zero access to student records or administrative operations.',
    },
    {
      title: 'University and Research Partnerships',
      description: 'Evaluation pilots and non-profit educational infrastructure contributions with ethical approvals.',
    },
    {
      title: 'Open-Source Community Contributions',
      description: 'Peer security reviews, translations across 13 Indian languages, documentation, and maintainer stewardship.',
    },
  ]

  const operatingCosts = [
    {
      category: 'Cloud Hosting and Persistent Storage',
      purpose: 'Encrypted MongoDB persistence, multi-region API compute, and daily automated encrypted snapshots.',
    },
    {
      category: 'Communication and Notification Dispatch',
      purpose: 'In-app messaging, email notifications, and webhook delivery infrastructure.',
    },
    {
      category: 'Cryptographic Key Management and Verification',
      purpose: 'Ed25519 digital signature signing key storage and high-availability JWKS verification registries.',
    },
    {
      category: 'Security Audits and Vulnerability Assessments',
      purpose: 'Regular code audits, penetration testing, and dependency vulnerability scans.',
    },
  ]

  const dataPillars = [
    'Privacy before growth: Minimization and strict purpose limitation on every stored record.',
    'Multi-tenant isolation: Complete logical isolation across institutional tenants enforced at API and database layers.',
    'Deny-by-default access control: Explicit role-based permissions verified on every request.',
    'Opaque credential tokens: Public verification endpoints expose only allowlisted metadata; raw identifiers and sensitive personal data are never published.',
    'Student ownership and verified guardian access: Parents can only access records linked through verified institution approvals.',
  ]

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <PageHeader
        title="Public Sustainability & Transparency Charter"
        description="Our commitment to free education services, independent operation, and strict student privacy."
      />

      {/* The Core Public Pledge */}
      <Card className="p-6 mb-8 border-l-4 border-l-brand-primary bg-surface-subtle">
        <h2 className="text-xl font-bold text-text-primary mb-2">Our Public-Benefit Pledge</h2>
        <p className="text-text-secondary leading-relaxed mb-4">
          ChhatraLekha is a public-benefit, multi-tenant education platform designed to connect institutions,
          students, teachers, and parents across India. The platform is completely free to use for all institutions,
          students, and families.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div className="bg-surface p-4 rounded border border-border">
            <h3 className="font-semibold text-text-primary text-sm mb-1">Zero Commercial Ads</h3>
            <p className="text-xs text-text-muted">No advertising in student or parent experiences.</p>
          </div>
          <div className="bg-surface p-4 rounded border border-border">
            <h3 className="font-semibold text-text-primary text-sm mb-1">No Data Monetization</h3>
            <p className="text-xs text-text-muted">We never sell, rent, or profile student data.</p>
          </div>
          <div className="bg-surface p-4 rounded border border-border">
            <h3 className="font-semibold text-text-primary text-sm mb-1">No Paywalls</h3>
            <p className="text-xs text-text-muted">Core academic operations and records are never gated.</p>
          </div>
        </div>
      </Card>

      {/* Operating Sustainability Model */}
      <section className="mb-10">
        <h2 className="text-lg font-bold text-text-primary mb-4">How ChhatraLekha Is Sustained</h2>
        <p className="text-sm text-text-secondary mb-6">
          A free service requires real operating resources for hosting, storage, backups, and security.
          We sustain our mission through transparent, non-commercial avenues that preserve platform independence.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sustainabilityPillars.map((item, idx) => (
            <Card key={idx} className="p-5">
              <h3 className="font-semibold text-text-primary text-base mb-2">{item.title}</h3>
              <p className="text-sm text-text-muted leading-relaxed">{item.description}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Operating Costs */}
      <section className="mb-10">
        <h2 className="text-lg font-bold text-text-primary mb-4">Operating Cost Categories</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm border border-border">
            <thead className="bg-surface-subtle text-text-secondary text-xs uppercase">
              <tr>
                <th className="px-4 py-3 border-b border-border">Cost Category</th>
                <th className="px-4 py-3 border-b border-border">Operational Purpose</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {operatingCosts.map((cost, idx) => (
                <tr key={idx} className="hover:bg-surface-subtle">
                  <td className="px-4 py-3 font-medium text-text-primary">{cost.category}</td>
                  <td className="px-4 py-3 text-text-muted">{cost.purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Data Governance Charter */}
      <section className="mb-10">
        <h2 className="text-lg font-bold text-text-primary mb-4">Student Data Protection Charter</h2>
        <Card className="p-6">
          <ul className="space-y-3">
            {dataPillars.map((pillar, idx) => (
              <li key={idx} className="flex items-start text-sm text-text-secondary">
                <span className="font-bold text-brand-primary mr-2">•</span>
                <span>{pillar}</span>
              </li>
            ))}
          </ul>
          <div className="mt-6 pt-4 border-t border-border flex flex-col md:flex-row justify-between text-xs text-text-muted gap-2">
            <span>Aligned with Indian Digital Personal Data Protection standards.</span>
            <span>Institutions retain full data ownership and export rights.</span>
          </div>
        </Card>
      </section>
    </div>
  )
}
