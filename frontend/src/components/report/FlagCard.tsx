import { Check, Copy } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Flag } from '../../api/types'
import { formatClock, formatPercent } from '../../lib/format'
import { isPlaceholderQuote } from '../../lib/highlight'
import { usePlayerStore } from '../../stores/player'
import { SeverityBadge } from '../ui'

function CopyButton({ text }: { text: string }) {
  const { t } = useTranslation()
  const [copied, setCopied] = useState(false)

  async function copy() {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <button type="button" className="btn no-print" onClick={() => void copy()}>
      {copied ? <Check size={14} /> : <Copy size={14} />}
      {copied ? t('report.copied') : t('report.copy')}
    </button>
  )
}

export function FlagCard({ flag }: { flag: Flag }) {
  const { t } = useTranslation()
  const seek = usePlayerStore((state) => state.seek)
  return (
    <article className="card flag-card flex flex-col gap-3 p-4" data-severity={flag.severity}>
      <header className="flex flex-wrap items-center gap-2">
        <button type="button" className="btn no-print" onClick={() => seek(flag.start_sec)}>
          <span className="time">{formatClock(flag.start_sec)}</span>
        </button>
        <SeverityBadge severity={flag.severity} />
        <span className="badge badge-accent">
          {flag.layer === 'rule'
            ? t('report.rule')
            : t('report.evon', { percent: formatPercent(flag.confidence) })}
        </span>
        {!flag.verified && <span className="badge badge-outline">{t('report.pending')}</span>}
      </header>

      <h3 className="text-base">{flag.title}</h3>
      {!isPlaceholderQuote(flag) && <p className="quote m-0">&ldquo;{flag.quote}&rdquo;</p>}
      <p className="m-0 text-sm text-ink-soft">{flag.explanation}</p>

      <div className="rewrite flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="eyebrow m-0">{t('report.saferLine')}</p>
          <p className="m-0 mt-1 text-sm">{flag.suggested_rewrite}</p>
        </div>
        <CopyButton text={flag.suggested_rewrite} />
      </div>
    </article>
  )
}
