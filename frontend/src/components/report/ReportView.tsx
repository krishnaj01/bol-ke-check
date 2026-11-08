import { useEffect } from 'react'
import { mediaUrl } from '../../api/client'
import type { Report } from '../../api/types'
import { SCORE_FORMULA } from '../../lib/constants'
import { usePlayerStore } from '../../stores/player'
import { FlagCard } from './FlagCard'
import { ReportHeader } from './ReportHeader'
import { Transcript } from './Transcript'
import { VideoPlayer } from './VideoPlayer'
import { Hi } from '../ui'

export function ReportView({ report }: { report: Report }) {
  const reset = usePlayerStore((state) => state.reset)

  useEffect(() => reset, [reset])

  return (
    <div className="flex flex-col gap-6">
      {report.status === 'partial' && (
        <p className="notice notice-medium m-0">
          <strong>Partial report.</strong> Gnani Evon could not review this transcript, so only the
          rule layer ran. Subtler claims may be missing.
        </p>
      )}

      <ReportHeader report={report} />

      <div className="grid gap-6 lg:grid-cols-2">
        {report.media_url && (
          <VideoPlayer
            src={mediaUrl(report.media_url)}
            duration={report.duration_sec ?? 0}
            flags={report.flags}
          />
        )}
        <Transcript segments={report.segments} flags={report.flags} />
      </div>

      <section className="flex flex-col gap-3">
        <h2 className="display text-xl">
          <Hi>ध्यान देने वाली बातें</Hi>{' '}
          <span className="mono-time text-ink-faint">({report.flags.length})</span>
        </h2>
        {report.flags.length === 0 ? (
          <div className="card p-6 text-center">
            <p className="display m-0 text-xl" lang="hi">
              सब साफ़ है
            </p>
            <p className="m-0 text-sm text-ink-soft">No risky spoken lines were found.</p>
          </div>
        ) : (
          <div className="grid gap-3 lg:grid-cols-2">
            {report.flags.map((flag) => (
              <FlagCard key={flag.id} flag={flag} />
            ))}
          </div>
        )}
      </section>

      <footer className="border-t border-line pt-4 text-sm text-ink-soft">
        <p className="m-0 font-semibold">{report.disclaimer}</p>
        <p className="m-0 mt-1">{SCORE_FORMULA}</p>
      </footer>
    </div>
  )
}
