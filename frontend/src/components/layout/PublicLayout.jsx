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

      {/* Public Header */}
      <header className="sticky top-0 z-40 bg-surface border-b border-line">
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
          <nav className="hidden md:flex items-center gap-6" aria-label="Main Navigation">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `text-sm font-medium transition-colors no-underline ${
                  isActive ? 'text-brand font-semibold' : 'text-muted hover:text-ink'
                }`
              }
            >
              Overview
            </NavLink>
            <NavLink
              to="/about"
              className={({ isActive }) =>
                `text-sm font-medium transition-colors no-underline ${
                  isActive ? 'text-brand font-semibold' : 'text-muted hover:text-ink'
                }`
              }
            >
              About
            </NavLink>
            <NavLink
              to="/early-access"
              className={({ isActive }) =>
                `text-sm font-medium transition-colors no-underline ${
                  isActive ? 'text-brand font-semibold' : 'text-muted hover:text-ink'
                }`
              }
            >
              Early Access
            </NavLink>
            <NavLink
              to="/help"
              className={({ isActive }) =>
                `text-sm font-medium transition-colors no-underline ${
                  isActive ? 'text-brand font-semibold' : 'text-muted hover:text-ink'
                }`
              }
            >
              Help
            </NavLink>
            <NavLink
              to="/faq"
              className={({ isActive }) =>
                `text-sm font-medium transition-colors no-underline ${
                  isActive ? 'text-brand font-semibold' : 'text-muted hover:text-ink'
                }`
              }
            >
              FAQ
            </NavLink>
            <NavLink
              to="/contact"
              className={({ isActive }) =>
                `text-sm font-medium transition-colors no-underline ${
                  isActive ? 'text-brand font-semibold' : 'text-muted hover:text-ink'
                }`
              }
            >
              Contact
            </NavLink>
            <NavLink
              to="/transparency"
              className={({ isActive }) =>
                `text-sm font-medium transition-colors no-underline ${
                  isActive ? 'text-brand font-semibold' : 'text-muted hover:text-ink'
                }`
              }
            >
              Transparency
            </NavLink>
          </nav>

          {/* Action CTAs & Controls */}
          <div className="hidden sm:flex items-center gap-3">
            <ThemeToggle />
            <LanguageSwitcher />
            <Link
              to="/login"
              className="px-4 py-2 text-sm font-semibold rounded bg-brand text-on-brand hover:opacity-95 transition-opacity no-underline shadow-sm"
            >
              Sign In / Demo
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
                Overview
              </Link>
              <Link
                to="/about"
                onClick={() => setMobileMenuOpen(false)}
                className="py-2 text-sm font-medium text-ink hover:text-brand"
              >
                About
              </Link>
              <Link
                to="/early-access"
                onClick={() => setMobileMenuOpen(false)}
                className="py-2 text-sm font-medium text-ink hover:text-brand"
              >
                Early Access
              </Link>
              <Link
                to="/help"
                onClick={() => setMobileMenuOpen(false)}
                className="py-2 text-sm font-medium text-ink hover:text-brand"
              >
                Help Center
              </Link>
              <Link
                to="/faq"
                onClick={() => setMobileMenuOpen(false)}
                className="py-2 text-sm font-medium text-ink hover:text-brand"
              >
                FAQ
              </Link>
              <Link
                to="/contact"
                onClick={() => setMobileMenuOpen(false)}
                className="py-2 text-sm font-medium text-ink hover:text-brand"
              >
                Contact
              </Link>
              <div className="pt-2 border-t border-line flex flex-col gap-3">
                <LanguageSwitcher />
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2 px-4 text-sm font-semibold rounded bg-brand text-on-brand"
                >
                  Sign In / Demo
                </Link>
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
          className="fixed bottom-6 right-6 z-30 p-3 rounded bg-surface border border-line text-ink shadow-sm hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
          </svg>
        </button>
      )}

      {/* Public Footer */}
      <footer className="border-t border-line bg-surface mt-12 py-10">
        <div className="mx-auto max-w-[1200px] px-5">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-3">
                <img
                  src="/brand/chhatralekha-logo.png"
                  alt="ChhatraLekha"
                  className="h-10 w-auto object-contain rounded bg-white p-1 border border-line"
                />
                <span className="text-xs px-2 py-0.5 rounded border border-warning/40 bg-warning-surface text-warning-strong font-semibold">
                  Prototype
                </span>
              </div>
              <p className="text-sm text-muted max-w-[50ch] mb-4">
                Unified digital academic identity and operations platform for schools and colleges across India, connecting students, families, teachers, and verified institutions.
              </p>
              <p className="text-xs text-muted/80">
                Notice: Educational prototype demonstration with synthetic records. Not affiliated with government registries.
              </p>
            </div>

            <div>
              <h3 className="text-sm font-bold text-ink uppercase tracking-wider mb-3">Navigation</h3>
              <ul className="space-y-2 text-sm">
                <li><Link to="/about" className="text-muted hover:text-brand no-underline">About Platform</Link></li>
                <li><Link to="/early-access" className="text-muted hover:text-brand no-underline">Early Access Application</Link></li>
                <li><Link to="/help" className="text-muted hover:text-brand no-underline">Help &amp; Support Center</Link></li>
                <li><Link to="/faq" className="text-muted hover:text-brand no-underline">Frequently Asked Questions</Link></li>
                <li><Link to="/contact" className="text-muted hover:text-brand no-underline">Contact &amp; Issue Report</Link></li>
                <li><Link to="/login" className="text-muted hover:text-brand no-underline">Sign In / Live Demo</Link></li>
              </ul>
            </div>

            <div>
              <h3 className="text-sm font-bold text-ink uppercase tracking-wider mb-3">Legal &amp; Policy</h3>
              <ul className="space-y-2 text-sm">
                <li><Link to="/privacy" className="text-muted hover:text-brand no-underline">Privacy Policy (Draft)</Link></li>
                <li><Link to="/terms" className="text-muted hover:text-brand no-underline">Terms of Service (Draft)</Link></li>
                <li><Link to="/transparency" className="text-muted hover:text-brand no-underline">Transparency Charter</Link></li>
              </ul>
            </div>
          </div>

          <div className="pt-6 border-t border-line flex flex-col sm:flex-row items-center justify-between text-xs text-muted gap-3">
            <p className="m-0">
              &copy; {new Date().getFullYear()} ChhatraLekha. All rights reserved.
            </p>
            <p className="m-0 text-muted/80">
              No cookies for tracking &middot; Strict privacy &middot; Offline-first verified
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
