import { Download, Pause, Printer, Volume2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { mediaUrl } from '../../api/client'
import type { Disclosure, Report } from '../../api/types'
import { categoryLabel } from '../../lib/constants'
import { downloadJson, formatClock } from '../../lib/format'
import { Hi } from '../ui'
import { RiskGauge } from './RiskGauge'

function disclosureText(disclosure: Disclosure): { text: string; badge: string } {
  if (!disclosure.required) {
    return { text: 'Not marked as paid', badge: 'badge-outline' }
  }
  if (!disclosure.found) return { text: 'Not said out loud', badge: 'badge-high' }
  return { text: `Said at ${formatClock(disclosure.first_at_sec ?? 0)}`, badge: 'badge-low' }
}

function SummaryAudio({ src }: { src: string }) {
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
        <Hi>{playing ? 'रोकें' : 'सुनिए'}</Hi> · Gnani Timbre
      </button>
    </>
  )
}

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="eyebrow">{label}</dt>
      <dd className="m-0 mt-1 font-semibold">{children}</dd>
    </div>
  )
}

export function ReportHeader({ report }: { report: Report }) {
  const disclosure = report.disclosure && disclosureText(report.disclosure)
  return (
    <section className="card grid gap-6 p-5 md:grid-cols-[auto_1fr] md:p-6">
      <RiskGauge score={report.risk_score ?? 0} level={report.risk_level ?? 'low'} />
      <div className="flex flex-col justify-between gap-4">
        <dl className="m-0 grid grid-cols-2 gap-4 sm:grid-cols-3">
          <Fact label="Category">{categoryLabel(report.category)}</Fact>
          <Fact label="Duration">{formatClock(report.duration_sec ?? 0)}</Fact>
          <Fact label="Disclosure">
            {disclosure && <span className={`badge ${disclosure.badge}`}>{disclosure.text}</span>}
          </Fact>
        </dl>
        {report.summary_hi && <p className="m-0 text-ink-soft">{report.summary_hi}</p>}
        <div className="no-print flex flex-wrap gap-2">
          {report.summary_audio_url && <SummaryAudio src={report.summary_audio_url} />}
          <button
            type="button"
            className="btn"
            onClick={() => downloadJson(`${report.check_id}.json`, report)}
          >
            <Download size={16} /> Download JSON
          </button>
          <button type="button" className="btn" onClick={() => window.print()}>
            <Printer size={16} /> Print
          </button>
        </div>
      </div>
    </section>
  )
}
