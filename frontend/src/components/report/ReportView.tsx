import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { mediaUrl } from '../../api/client'
import type { Report } from '../../api/types'
import { usePlayerStore } from '../../stores/player'
import { FlagCard } from './FlagCard'
import { ReportHeader } from './ReportHeader'
import { Transcript } from './Transcript'
import { VideoPlayer } from './VideoPlayer'

export function ReportView({ report }: { report: Report }) {
  const { t } = useTranslation()
  const reset = usePlayerStore((state) => state.reset)

  useEffect(() => reset, [reset])

  return (
    <div className="flex flex-col gap-6">
      {report.status === 'partial' && (
        <p className="notice notice-medium m-0">
          <strong>{t('report.partial')}</strong> {t('report.partialBody')}
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
        <h2 className="text-xl">
          {t('report.flags')} <span className="text-ink-faint">({report.flags.length})</span>
        </h2>
        {report.flags.length === 0 ? (
          <div className="card p-6 text-center">
            <p className="m-0 text-xl font-semibold">{t('report.clean')}</p>
            <p className="m-0 text-sm text-ink-soft">{t('report.cleanBody')}</p>
          </div>
        ) : (
          <div className="grid gap-3 lg:grid-cols-2">
            {report.flags.map((flag) => (
              <FlagCard key={flag.id} flag={flag} />
            ))}
          </div>
        )}
      </section>

      <p className="m-0 border-t border-line pt-4 text-xs text-ink-faint">
        <strong>{t('report.disclaimer')}</strong> {t('report.formula')}
      </p>
    </div>
  )
}
