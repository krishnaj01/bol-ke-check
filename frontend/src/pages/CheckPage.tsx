import { Link, useParams } from 'react-router-dom'
import { isTerminal, useCheck, useCheckEvents, useRetryCheck } from '../api/hooks'
import { ProgressView } from '../components/progress/ProgressView'
import { ReportView } from '../components/report/ReportView'
import { ERROR_COPY } from '../lib/constants'
import type { ErrorCode } from '../api/types'

function Message({ title, body, children }: {
  title: string
  body: string
  children?: React.ReactNode
}) {
  return (
    <section className="card mx-auto flex max-w-[34rem] flex-col items-start gap-3 p-6">
      <h1 className="display text-xl">{title}</h1>
      <p className="m-0 text-ink-soft">{body}</p>
      <div className="flex flex-wrap gap-2">
        {children}
        <Link to="/" className="btn no-underline">
          Check another reel
        </Link>
      </div>
    </section>
  )
}

function FailedView({ id, error }: { id: string; error: ErrorCode | null }) {
  const retry = useRetryCheck(id)
  const copy = ERROR_COPY[error ?? 'internal']
  return (
    <Message title={copy.title} body={copy.body}>
      {copy.retry && (
        <button
          type="button"
          className="btn"
          disabled={retry.isPending}
          onClick={() => retry.mutate()}
        >
          Try again
        </button>
      )}
    </Message>
  )
}

export function CheckPage() {
  const { id = '' } = useParams()
  const { data: report, isError } = useCheck(id)
  const running = !report || !isTerminal(report.status)
  useCheckEvents(id, Boolean(report) && running)

  if (isError) {
    return <Message title="Report nahi mila" body="This check does not exist, or it has expired." />
  }
  if (report?.status === 'failed') return <FailedView id={id} error={report.error} />
  if (!report || running || report.risk_score === null) {
    return <ProgressView stage={report?.stage ?? 'queued'} />
  }
  return <ReportView report={report} />
}
