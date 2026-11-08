import { Moon, Sun } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { useHealth } from '../../api/hooks'
import { LINKS } from '../../lib/constants'
import { useLocaleStore } from '../../stores/locale'
import type { Locale } from '../../stores/locale'
import { useThemeStore } from '../../stores/theme'
import { Segmented, Wave } from '../ui'

const LOCALE_OPTIONS: { value: Locale; label: string; lang: string }[] = [
  { value: 'en', label: 'EN', lang: 'en' },
  { value: 'hi', label: 'हिंदी', lang: 'hi' },
]

function Brand() {
  const { t } = useTranslation()
  return (
    <Link to="/" className="brand">
      <span className="brand-mark">
        <Wave bars={5} />
      </span>
      {t('brand')}
    </Link>
  )
}

function ThemeToggle() {
  const { t } = useTranslation()
  const { theme, toggle } = useThemeStore()
  const label = t(theme === 'light' ? 'header.toDark' : 'header.toLight')
  return (
    <button type="button" className="btn btn-icon" onClick={toggle} aria-label={label} title={label}>
      {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
    </button>
  )
}

function SiteHeader() {
  const { t } = useTranslation()
  const { locale, setLocale } = useLocaleStore()
  const { data: health } = useHealth()
  return (
    <header className="site-header no-print">
      <div className="page site-header-inner flex-wrap py-2">
        <Brand />
        <nav className="order-last flex w-full gap-1 md:order-none md:w-auto">
          <NavLink to="/" end className="nav-link">
            {t('nav.check')}
          </NavLink>
          <NavLink to="/about" className="nav-link">
            {t('nav.about')}
          </NavLink>
        </nav>
        <div className="ml-auto flex items-center gap-2">
          {health?.mock && <span className="badge badge-accent">{t('header.demo')}</span>}
          <Segmented
            label={t('header.siteLanguage')}
            options={LOCALE_OPTIONS}
            value={locale}
            onChange={setLocale}
          />
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}

function SiteFooter() {
  const { t } = useTranslation()
  const external = { target: '_blank', rel: 'noreferrer' }
  return (
    <footer className="site-footer no-print">
      <div className="page grid gap-8 py-10 sm:grid-cols-2 md:grid-cols-[2fr_1fr_1fr]">
        <div className="flex flex-col items-start gap-2">
          <Brand />
          <p className="m-0 max-w-[24rem] text-sm text-ink-soft">{t('footer.tagline')}</p>
          <p className="m-0 max-w-[24rem] text-xs text-ink-faint">{t('footer.builtOn')}</p>
        </div>
        <div>
          <p className="footer-title">{t('footer.product')}</p>
          <Link to="/" className="footer-link">
            {t('nav.check')}
          </Link>
          <Link to="/about" className="footer-link">
            {t('nav.about')}
          </Link>
        </div>
        <div>
          <p className="footer-title">{t('footer.resources')}</p>
          <a href={LINKS.asci} className="footer-link" {...external}>
            {t('footer.ascI')}
          </a>
          <a href={LINKS.asciVideo} className="footer-link" {...external}>
            {t('footer.ascIVideo')}
          </a>
          <a href={LINKS.gnaniDocs} className="footer-link" {...external}>
            {t('footer.gnaniDocs')}
          </a>
        </div>
      </div>
      <div className="border-t border-line">
        <p className="page my-0 py-4 text-xs text-ink-faint">{t('footer.disclaimer')}</p>
      </div>
    </footer>
  )
}

export function AppShell() {
  return (
    <>
      <SiteHeader />
      <main className="page py-8 md:py-12">
        <Outlet />
      </main>
      <SiteFooter />
    </>
  )
}
