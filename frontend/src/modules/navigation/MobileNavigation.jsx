import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { NavIcon } from './Sidebar'

export function MobileBottomBar({ navItems = [], unreadCount = 0 }) {
  const { t } = useTranslation()
  // Show up to 4 key items + profile
  const primaryItems = navItems.slice(0, 4)

  return (
    <nav
      aria-label="Mobile Bottom Navigation"
      className="lg:hidden fixed bottom-0 inset-x-0 z-40 bg-surface border-t border-line flex items-center justify-around py-1.5 px-2 shadow-md"
    >
      {primaryItems.map((item) => (
        <NavLink
          key={item.to + item.label}
          to={item.to}
          className={({ isActive }) =>
            `flex flex-col items-center justify-center p-1 text-[10px] font-medium transition-colors no-underline relative ${
              isActive ? 'text-brand font-bold' : 'text-muted hover:text-ink'
            }`
          }
        >
          <NavIcon icon={item.icon} className="w-5 h-5 mb-0.5" />
          <span className="truncate max-w-[60px]">{t(item.label)}</span>
          {item.hasBadge && unreadCount > 0 && (
            <span className="absolute top-0 right-2 w-2 h-2 rounded-full bg-accent" />
          )}
        </NavLink>
      ))}

      <NavLink
        to="/profile"
        className={({ isActive }) =>
          `flex flex-col items-center justify-center p-1 text-[10px] font-medium transition-colors no-underline ${
            isActive ? 'text-brand font-bold' : 'text-muted hover:text-ink'
          }`
        }
      >
        <NavIcon icon="profile" className="w-5 h-5 mb-0.5" />
        <span className="truncate max-w-[60px]">{t('nav.profile')}</span>
      </NavLink>
    </nav>
  )
}

