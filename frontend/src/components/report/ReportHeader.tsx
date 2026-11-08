import { Download, Pause, Printer, Volume2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { mediaUrl } from '../../api/client'
import type { Report } from '../../api/types'
import { downloadJson, formatClock } from '../../lib/format'
import { RiskGauge } from './RiskGauge'

function SummaryAudio({ src }: { src: string }) {
  const { t } = useTranslation()
  const audioRef = useRef<HTMLAudioElement>(null)
  const [playing, setPlaying] = useState(false)

  useEffect(() => {
    const audio = audioRef.current
    return () => audio?.pause()
  }, [])

  return (
    <>
      <audio
        ref={audioRef}
        src={mediaUrl(src)}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
      />
      <button
        type="button"
        className="btn"
        onClick={() => (playing ? audioRef.current?.pause() : void audioRef.current?.play())}
      >
        {playing ? <Pause size={16} /> : <Volume2 size={16} />}
        {playing ? t('report.stop') : t('report.listen')}
      </button>
    </>
  )
}

function Fact({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="eyebrow">{label}</dt>
      <dd className="m-0 mt-1 font-semibold">{children}</dd>
    </div>
  )
}

function DisclosureBadge({ report }: { report: Report }) {
  const { t } = useTranslation()
  const disclosure = report.disclosure
  if (!disclosure) return null
  if (!disclosure.required) {
    return <span className="badge badge-outline">{t('report.notPaid')}</span>
  }
  if (!disclosure.found) return <span className="badge badge-high">{t('report.notSaid')}</span>
  return (
    <span className="badge badge-low">
      {t('report.saidAt', { time: formatClock(disclosure.first_at_sec ?? 0) })}
    </span>
  )
}

export function ReportHeader({ report }: { report: Report }) {
  const { t } = useTranslation()
  return (
    <section className="card grid gap-6 p-5 md:grid-cols-[auto_1fr] md:p-6">
      <RiskGauge score={report.risk_score ?? 0} level={report.risk_level ?? 'low'} />
      <div className="flex flex-col justify-between gap-4">
        <dl className="m-0 grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Fact label={t('report.category')}>{t(`category.${report.category}`)}</Fact>
          <Fact label={t('report.spoken')}>{t(`audioLanguage.${report.language}`)}</Fact>
          <Fact label={t('report.duration')}>{formatClock(report.duration_sec ?? 0)}</Fact>
          <Fact label={t('report.disclosure')}>
            <DisclosureBadge report={report} />
          </Fact>
        </dl>
        {report.summary_hi && <p className="m-0 text-sm text-ink-soft">{report.summary_hi}</p>}
        <div className="no-print flex flex-wrap gap-2">
          {report.summary_audio_url && <SummaryAudio src={report.summary_audio_url} />}
          <button
            type="button"
            className="btn"
            onClick={() => downloadJson(`${report.check_id}.json`, report)}
          >
            <Download size={16} /> {t('report.download')}
          </button>
          <button type="button" className="btn" onClick={() => window.print()}>
            <Printer size={16} /> {t('report.print')}
          </button>
        </div>
      </div>
    </section>
  )
}
