import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '../hooks/usePageMeta'
import { Badge, Card } from '../components/common'

const STACK_BADGES = [
  'React',
  'Vite',
  'Tailwind CSS',
  'FastAPI',
  'MongoDB',
  'Kotlin',
  'Jetpack Compose',
]

export default function AboutPage() {
  const { t } = useTranslation()

  usePageMeta({
    title: t('about.headline'),
    description: t('about.intro'),
    canonical: '/about',
  })

  const steps = [
    { title: t('about.step1Title'), desc: t('about.step1Desc') },
    { title: t('about.step2Title'), desc: t('about.step2Desc') },
    { title: t('about.step3Title'), desc: t('about.step3Desc') },
    { title: t('about.step4Title'), desc: t('about.step4Desc') },
    { title: t('about.step5Title'), desc: t('about.step5Desc') },
  ]

  const features = [
    { title: t('about.offer1Title'), desc: t('about.offer1Desc') },
    { title: t('about.offer2Title'), desc: t('about.offer2Desc') },
    { title: t('about.offer3Title'), desc: t('about.offer3Desc') },
    { title: t('about.offer4Title'), desc: t('about.offer4Desc') },
    { title: t('about.offer5Title'), desc: t('about.offer5Desc') },
    { title: t('about.offer6Title'), desc: t('about.offer6Desc') },
  ]

  const privacyPoints = [
    t('about.privacy1'),
    t('about.privacy2'),
    t('about.privacy3'),
    t('about.privacy4'),
    t('about.privacy5'),
  ]

  const limitations = [
    t('about.not1'),
    t('about.not2'),
    t('about.not3'),
  ]

  return (
    <div className="mx-auto max-w-[1080px] px-4 sm:px-6 py-10 space-y-12">
      {/* 1. Hero Section */}
      <section className="bg-surface-2 border border-line rounded-lg p-6 sm:p-10 space-y-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-accent-strong">
            {t('about.label')} &bull; Academic Record Verification
          </span>
          <span className="text-xs text-muted">| About ChhatraLekha</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-brand tracking-tight m-0">
          {t('about.headline')}
        </h1>
        <p className="text-base sm:text-lg text-muted leading-relaxed max-w-3xl m-0">
          {t('about.intro')}
        </p>
        <div className="flex flex-wrap gap-3 pt-2">
          <Link to="/verify" className="btn btn-navy">
            {t('about.verifyButton')}
          </Link>
          <Link to="/dashboard" className="btn btn-outline">
            {t('about.exploreButton')}
          </Link>
        </div>
      </section>

      {/* 2. Prototype Notice */}
      <aside
        role="note"
        aria-label="Prototype Notice"
        className="p-4 rounded-lg border border-warning/40 bg-warning-surface text-warning-strong text-sm leading-relaxed"
      >
        <strong>{t('common.status')}: </strong>
        {t('about.notice')}
      </aside>

      {/* 3. The Problem */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-ink m-0">{t('about.problemTitle')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <Card className="p-5 space-y-2" title={t('about.problem1Title')}>
            <p className="text-sm text-muted leading-relaxed m-0">
              {t('about.problem1Desc')}
            </p>
          </Card>
          <Card className="p-5 space-y-2" title={t('about.problem2Title')}>
            <p className="text-sm text-muted leading-relaxed m-0">
              {t('about.problem2Desc')}
            </p>
          </Card>
          <Card className="p-5 space-y-2" title={t('about.problem3Title')}>
            <p className="text-sm text-muted leading-relaxed m-0">
              {t('about.problem3Desc')}
            </p>
          </Card>
        </div>
      </section>

      {/* 4. How ChhatraLekha Works */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-ink m-0">{t('about.howTitle')}</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {steps.map((step, index) => (
            <div
              key={index}
              className="bg-surface border border-line rounded-lg p-4 flex flex-col gap-2"
            >
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-brand text-on-brand flex items-center justify-center text-xs font-bold shrink-0">
                  {index + 1}
                </span>
                <span className="font-bold text-sm text-ink">{step.title}</span>
              </div>
              <p className="text-xs text-muted leading-relaxed m-0">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 5. What It Offers */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-ink m-0">{t('about.offersTitle')}</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((feature, index) => (
            <Card key={index} className="p-5 space-y-2" title={feature.title}>
              <p className="text-sm text-muted leading-relaxed m-0">{feature.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* 6. Privacy and Security Band */}
      <section className="bg-brand text-on-brand rounded-lg p-6 sm:p-8 space-y-4 shadow-md">
        <h2 className="text-xl font-bold text-white m-0">{t('about.privacyTitle')}</h2>
        <ul className="space-y-3 text-sm text-white/90 leading-relaxed list-disc pl-5 m-0">
          {privacyPoints.map((point, index) => (
            <li key={index}>{point}</li>
          ))}
        </ul>
      </section>

      {/* 7. Built With */}
      <section className="space-y-3">
        <h2 className="text-lg font-bold text-ink m-0">{t('about.stackTitle')}</h2>
        <div className="flex flex-wrap gap-2">
          {STACK_BADGES.map((tech) => (
            <Badge
              key={tech}
              className="bg-surface-2 text-ink border border-line px-3 py-1 text-xs"
            >
              {tech}
            </Badge>
          ))}
        </div>
      </section>

      {/* 8. What It Is Not */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-ink m-0">{t('about.notTitle')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {limitations.map((item, index) => (
            <div
              key={index}
              className="bg-surface-2 border border-line rounded-lg p-4 text-xs sm:text-sm text-muted leading-relaxed"
            >
              {item}
            </div>
          ))}
        </div>
      </section>

      {/* 9. Contact CTA */}
      <Card className="p-6 sm:p-8 text-center space-y-4 bg-surface-2 border-line">
        <h2 className="text-xl font-bold text-ink m-0">{t('about.contactTitle')}</h2>
        <p className="text-sm text-muted max-w-md mx-auto m-0">
          {t('about.contactLead')}
        </p>
        <div>
          <Link to="/contact" className="btn btn-navy">
            {t('about.contactButton')}
          </Link>
        </div>
      </Card>
    </div>
  )
}
