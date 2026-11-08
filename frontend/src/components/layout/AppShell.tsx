import { Moon, Sun } from 'lucide-react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { useHealth } from '../../api/hooks'
import { SCRIPT_RIBBON } from '../../lib/constants'
import { useThemeStore } from '../../stores/theme'
import { Hi, Wave } from '../ui'

function ThemeToggle() {
  const { theme, toggle } = useThemeStore()
  const next = theme === 'din' ? 'रात' : 'दिन'
  return (
    <button
      type="button"
      className="btn"
      onClick={toggle}
      aria-label={`Switch to ${theme === 'din' ? 'dark' : 'light'} theme`}
    >
      {theme === 'din' ? <Moon size={16} /> : <Sun size={16} />}
      <Hi>{next}</Hi>
    </button>
  )
}

function ScriptRibbon() {
  const items = [...SCRIPT_RIBBON, ...SCRIPT_RIBBON]
  return (
    <div className="ribbon no-print" aria-hidden="true">
      <div className="ribbon-track">
        {items.map((item, index) => (
          <span key={index} lang={item.lang} className={item.script}>
            {item.text}
          </span>
        ))}
      </div>
    </div>
  )
}

export function AppShell() {
  const { data: health } = useHealth()
  return (
    <>
      <header className="page no-print flex flex-wrap items-center justify-between gap-3 py-4">
        <Link to="/" className="flex items-center gap-3 text-ink no-underline">
          <Wave bars={5} />
          <span className="display text-xl" lang="hi">
            बोल के चेक
          </span>
        </Link>
        <nav className="flex items-center gap-2">
          {health?.mock && <span className="badge badge-accent">Demo data · mock Gnani</span>}
          <NavLink to="/about" className="btn no-underline">
            How it works
          </NavLink>
          <ThemeToggle />
        </nav>
      </header>
      <ScriptRibbon />
      <main className="page py-8 md:py-12">
        <Outlet />
      </main>
      <footer className="page no-print border-t border-line py-6 text-xs text-ink-faint">
        Automated pre-check, not legal advice. Built on Gnani Prisma, Evon and Timbre.
      </footer>
    </>
  )
}
