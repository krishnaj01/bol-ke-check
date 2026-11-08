import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useParams } from 'react-router-dom'
import { isTerminal, useCheck, useCheckEvents, useRetryCheck } from '../api/hooks'
import type { ErrorCode } from '../api/types'
import { ProgressView } from '../components/progress/ProgressView'
import { ReportView } from '../components/report/ReportView'
import { RETRYABLE_ERRORS } from '../lib/constants'

function Message({
  title,
  body,
  children,
}: {
  title: string
  body: string
  children?: ReactNode
}) {
  const { t } = useTranslation()
  return (
    <section className="card mx-auto flex max-w-[34rem] flex-col items-start gap-3 p-6">
      <h1 className="text-xl">{title}</h1>
      <p className="m-0 text-ink-soft">{body}</p>
      <div className="flex flex-wrap gap-2">
        {children}
        <Link to="/" className="btn">
          {t('error.another')}
        </Link>
      </div>
    </section>
  )
}

function FailedView({ id, error }: { id: string; error: ErrorCode | null }) {
  const { t } = useTranslation()
  const retry = useRetryCheck(id)
  const code = error ?? 'internal'
  return (
    <Message title={t(`error.${code}.title`)} body={t(`error.${code}.body`)}>
      {RETRYABLE_ERRORS.includes(code) && (
        <button
          type="button"
          className="btn"
          disabled={retry.isPending}
          onClick={() => retry.mutate()}
        >
          {t('error.retry')}
        </button>
      )}
    </Message>
  )
}

export function CheckPage() {
  const { t } = useTranslation()
  const { id = '' } = useParams()
  const { data: report, isError } = useCheck(id)
  const running = !report || !isTerminal(report.status)
  useCheckEvents(id, Boolean(report) && running)

  if (isError) return <Message title={t('error.notFoundTitle')} body={t('error.notFoundBody')} />
  if (report?.status === 'failed') return <FailedView id={id} error={report.error} />
  if (!report || running || report.risk_score === null) {
    return <ProgressView stage={report?.stage ?? 'queued'} />
  }
  return <ReportView report={report} />
}
