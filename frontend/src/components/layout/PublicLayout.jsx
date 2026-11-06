import { useState, useEffect } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import ThemeToggle from '../common/ThemeToggle'
import LanguageSwitcher from '../common/LanguageSwitcher'

export default function PublicLayout() {
  const { t } = useTranslation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [showScrollTop, setShowScrollTop] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 300)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen flex flex-col bg-canvas text-ink transition-colors">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-4 focus:py-2 focus:bg-brand focus:text-on-brand focus:rounded focus:outline-none focus:ring-2 focus:ring-accent"
      >
        Skip to main content
      </a>

      {/* Section A: Navigation Bar */}
      <header className="sticky top-0 z-40 bg-surface border-b border-line shadow-xs">
        <div className="mx-auto max-w-[1200px] px-5 py-3 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-3 no-underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand">
            <img
              src="/brand/chhatralekha-logo.png"
              alt="ChhatraLekha - Authenticate, Verify, Empower"
              className="h-10 sm:h-12 w-auto max-w-[200px] object-contain block"
              onError={(e) => {
                e.currentTarget.style.display = 'none'
              }}
            />
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-6" aria-label="Main Navigation">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `text-sm font-medium transition-colors no-underline ${
                  isActive ? 'text-brand font-bold' : 'text-muted hover:text-ink'
                }`
              }
            >
              Home
            </NavLink>
            <a
              href="/#features"
              className="text-sm font-medium text-muted hover:text-ink transition-colors no-underline"
            >
              Features
            </a>
            <a
              href="/#for-students"
              className="text-sm font-medium text-muted hover:text-ink transition-colors no-underline"
            >
              For Students
            </a>
            <a
              href="/#for-institutions"
              className="text-sm font-medium text-muted hover:text-ink transition-colors no-underline"
            >
              For Institutions
            </a>
            <NavLink
              to="/about"
              className={({ isActive }) =>
                `text-sm font-medium transition-colors no-underline ${
                  isActive ? 'text-brand font-bold' : 'text-muted hover:text-ink'
                }`
              }
            >
              About
            </NavLink>
            <a
              href="/#faq"
              className="text-sm font-medium text-muted hover:text-ink transition-colors no-underline"
            >
              FAQ
            </a>
          </nav>

          {/* Action CTAs & Controls */}
          <div className="hidden sm:flex items-center gap-3">
            <ThemeToggle />
            <LanguageSwitcher />
            <Link
              to="/login"
              className="px-3.5 py-2 text-sm font-semibold rounded border border-line bg-surface text-brand hover:border-brand transition-colors no-underline"
            >
              Sign In
            </Link>
            <Link
              to="/signup"
              className="px-4 py-2 text-sm font-bold rounded bg-accent text-on-accent hover:bg-accent-strong transition-colors no-underline shadow-xs"
            >
              Get Started
            </Link>
          </div>

          {/* Mobile hamburger button */}
          <div className="flex sm:hidden items-center gap-2">
            <ThemeToggle />
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded border border-line text-ink hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
              aria-expanded={mobileMenuOpen}
              aria-label="Toggle navigation menu"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile menu dropdown */}
        {mobileMenuOpen && (
          <div className="sm:hidden border-t border-line bg-surface px-5 py-4 space-y-3">
            <nav className="flex flex-col space-y-2" aria-label="Mobile Navigation">
              <Link
                to="/"
                onClick={() => setMobileMenuOpen(false)}
                className="py-2 text-sm font-medium text-ink hover:text-brand"
              >
                Home
              </Link>
              <a
                href="/#features"
                onClick={() => setMobileMenuOpen(false)}
                className="py-2 text-sm font-medium text-ink hover:text-brand"
              >
                Features
              </a>
              <a
                href="/#for-students"
                onClick={() => setMobileMenuOpen(false)}
                className="py-2 text-sm font-medium text-ink hover:text-brand"
              >
                For Students
              </a>
              <a
                href="/#for-institutions"
                onClick={() => setMobileMenuOpen(false)}
                className="py-2 text-sm font-medium text-ink hover:text-brand"
              >
                For Institutions
              </a>
              <Link
                to="/about"
                onClick={() => setMobileMenuOpen(false)}
                className="py-2 text-sm font-medium text-ink hover:text-brand"
              >
                About Platform
              </Link>
              <a
                href="/#faq"
                onClick={() => setMobileMenuOpen(false)}
                className="py-2 text-sm font-medium text-ink hover:text-brand"
              >
                Frequently Asked Questions
              </a>
              <div className="pt-3 border-t border-line flex flex-col gap-2.5">
                <LanguageSwitcher />
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <Link
                    to="/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="w-full text-center py-2 px-3 text-sm font-semibold rounded border border-line bg-surface text-brand"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/signup"
                    onClick={() => setMobileMenuOpen(false)}
                    className="w-full text-center py-2 px-3 text-sm font-bold rounded bg-accent text-on-accent"
                  >
                    Get Started
                  </Link>
                </div>
              </div>
            </nav>
          </div>
        )}
      </header>

      {/* Main Content Area */}
      <main id="main-content" className="flex-1">
        <Outlet />
      </main>

      {/* Back to top button */}
      {showScrollTop && (
        <button
          type="button"
          onClick={scrollToTop}
          aria-label="Scroll back to top"
          className="fixed bottom-6 right-6 z-30 p-3 rounded bg-surface border border-line text-ink shadow-xs hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
          </svg>
        </button>
      )}

      {/* Section J: Public Footer */}
      <footer className="border-t border-line bg-surface mt-12 py-12">
        <div className="mx-auto max-w-[1200px] px-5">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div className="md:col-span-2 space-y-3">
              <div className="flex items-center gap-3">
                <img
                  src="/brand/chhatralekha-logo.png"
                  alt="ChhatraLekha - Authenticate, Verify, Empower"
                  className="h-10 w-auto object-contain rounded bg-white p-1 border border-line"
                />
                <span className="text-xs px-2.5 py-0.5 rounded border border-accent/40 bg-accent/10 text-accent-strong font-bold uppercase tracking-wider">
                  Pilot Platform
                </span>
              </div>
              <p className="text-sm text-muted max-w-[50ch] leading-relaxed m-0">
                ChhatraLekha is a unified, multilingual digital academic identity and operations platform for schools, polytechnics, colleges, and universities across India. Connecting learners, families, educators, and institutions.
              </p>
              <p className="text-xs text-muted/80 m-0">
                Notice: Educational platform demonstration with synthetic records. Verifies against this prototype database under strict DPDP Act privacy guidelines.
              </p>
            </div>

            <div>
              <h3 className="text-sm font-bold text-ink uppercase tracking-wider mb-3">Navigation</h3>
              <ul className="space-y-2 text-sm list-none p-0 m-0">
                <li><Link to="/about" className="text-muted hover:text-brand no-underline">About Platform</Link></li>
                <li><Link to="/early-access" className="text-muted hover:text-brand no-underline">Early Access Pilot</Link></li>
                <li><Link to="/help" className="text-muted hover:text-brand no-underline">Help &amp; Support</Link></li>
                <li><Link to="/faq" className="text-muted hover:text-brand no-underline">Frequently Asked Questions</Link></li>
                <li><Link to="/contact" className="text-muted hover:text-brand no-underline">Contact &amp; Issue Report</Link></li>
                <li><Link to="/login" className="text-muted hover:text-brand no-underline">Sign In / Demo Portal</Link></li>
              </ul>
            </div>

            <div>
              <h3 className="text-sm font-bold text-ink uppercase tracking-wider mb-3">Legal &amp; Inclusion</h3>
              <ul className="space-y-2 text-sm list-none p-0 m-0">
                <li><Link to="/privacy" className="text-muted hover:text-brand no-underline">Privacy Policy (Draft)</Link></li>
                <li><Link to="/terms" className="text-muted hover:text-brand no-underline">Terms of Service (Draft)</Link></li>
                <li><Link to="/transparency" className="text-muted hover:text-brand no-underline">Transparency Charter</Link></li>
                <li><Link to="/accessibility" className="text-muted hover:text-brand no-underline">Accessibility Statement</Link></li>
              </ul>
            </div>
          </div>

          <div className="pt-6 border-t border-line flex flex-col sm:flex-row items-center justify-between text-xs text-muted gap-3">
            <p className="m-0">
              &copy; {new Date().getFullYear()} ChhatraLekha. All rights reserved. Authenticate &middot; Verify &middot; Empower.
            </p>
            <p className="m-0 text-muted/80">
              Zero tracking cookies &middot; DPDP Privacy Compliant &middot; 22 Indian Languages Supported
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
