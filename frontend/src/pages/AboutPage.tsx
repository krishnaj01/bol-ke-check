import { useState } from 'react'
import { useEvalMetrics, useRules } from '../api/hooks'
import type { Category, EvalMetrics } from '../api/types'
import { Hi, SeverityBadge } from '../components/ui'
import { CATEGORIES, SCORE_FORMULA } from '../lib/constants'
import { formatPercent } from '../lib/format'

const PIPELINE = [
  { name: 'Your reel', role: 'Upload in the browser' },
  { name: 'FastAPI', role: 'Runs the background job' },
  { name: 'ffmpeg', role: 'Mono 16 kHz audio' },
  { name: 'Voice detection', role: 'Timestamped speech segments' },
  { name: 'Gnani Prisma', role: 'Hinglish speech to text', gnani: true },
  { name: 'Rule engine', role: 'Fixed phrase and disclosure checks' },
  { name: 'Gnani Evon', role: 'Subtle claims and safer rewrites', gnani: true },
  { name: 'Risk score', role: 'A published formula' },
  { name: 'Gnani Timbre', role: 'Hindi spoken summary', gnani: true },
]

function RulePacks() {
  const [category, setCategory] = useState<Category>('personal_care')
  const { data, isLoading, isError } = useRules(category)
  return (
    <section className="flex flex-col gap-3">
      <h2 className="display text-xl">
        <Hi>नियम</Hi> · Rule packs
      </h2>
      <p className="notice notice-medium m-0">
        Every rule shows &ldquo;Pending review&rdquo; until its ASCI clause has been checked and
        added as a source.
      </p>
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((item) => (
          <button
            key={item.id}
            type="button"
            className="chip"
            aria-pressed={category === item.id}
            onClick={() => setCategory(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
      {isError && <p className="notice notice-high m-0">Could not load the rules.</p>}
      {isLoading && <p className="m-0 text-ink-faint">Loading rules…</p>}
      <div className="grid gap-3 md:grid-cols-2">
        {data?.rules.map((rule) => (
          <article key={rule.id} className="card flex flex-col gap-2 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="mono-time text-ink-faint">{rule.id}</span>
              <SeverityBadge severity={rule.severity} />
              {!rule.verified && <span className="badge badge-outline">Pending review</span>}
            </div>
            <h3 className="text-base font-semibold">{rule.title}</h3>
            <p className="m-0 text-sm text-ink-soft">{rule.explanation}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

function MetricsTable({ metrics }: { metrics: EvalMetrics }) {
  const rows: [string, string][] = [
    ['Clips', String(metrics.clips)],
    ['Recall', `${metrics.caught} of ${metrics.planted} (${formatPercent(metrics.recall)})`],
    ['False alarms', `${metrics.false_alarms} (${metrics.false_alarms_per_clip.toFixed(2)} per clip)`],
    [
      'Disclosure accuracy',
      metrics.disclosure_accuracy === null ? 'n/a' : formatPercent(metrics.disclosure_accuracy),
    ],
    ['Caught by rules / Evon', `${metrics.layer_split.rule} / ${metrics.layer_split.llm}`],
    [
      'Median latency',
      metrics.median_latency_sec === null ? 'n/a' : `${metrics.median_latency_sec.toFixed(1)} s`,
    ],
  ]
  return (
    <div className="card overflow-x-auto p-2">
      <table className="table">
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label}>
              <th scope="row">{label}</th>
              <td>{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Evaluation() {
  const { data: metrics, isLoading } = useEvalMetrics()
  return (
    <section className="flex flex-col gap-3">
      <h2 className="display text-xl">
        <Hi>जाँच के नतीजे</Hi> · Evaluation
      </h2>
      {isLoading && <p className="m-0 text-ink-faint">Loading…</p>}
      {!isLoading && !metrics && (
        <p className="notice notice-neutral m-0">
          No evaluation has been run yet. Results will appear here after the first run on clips the
          rules were not written from.
        </p>
      )}
      {metrics && metrics.partial_clips > 0 && (
        <p className="notice notice-medium m-0">
          {metrics.partial_clips} of {metrics.clips} clips ran without Gnani Evon, so these results
          partly reflect the rule layer alone.
        </p>
      )}
      {metrics && <MetricsTable metrics={metrics} />}
    </section>
  )
}

export function AboutPage() {
  return (
    <div className="flex flex-col gap-10">
      <header className="flex max-w-[44rem] flex-col gap-3">
        <h1 className="display text-2xl" lang="hi">
          यह काम कैसे करता है
        </h1>
        <p className="m-0 text-lg text-ink-soft">
          Fixed rules catch the clear-cut phrases. Gnani Evon judges what rules cannot. Every flag
          records which layer raised it, so nothing is a black box.
        </p>
      </header>

      <section className="flex flex-col gap-3">
        <h2 className="display text-xl">
          <Hi>रास्ता</Hi> · The pipeline
        </h2>
        <ol className="pipeline m-0 list-none p-0">
          {PIPELINE.map((node, index) => (
            <li key={node.name} className="pipeline-node" data-gnani={Boolean(node.gnani)}>
              <span className="mono-time text-ink-faint">{index + 1}</span>
              <p className="m-0 font-semibold">{node.name}</p>
              <p className="m-0 text-sm text-ink-soft">{node.role}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="display text-xl">
          <Hi>स्कोर</Hi> · How the score works
        </h2>
        <p className="m-0 text-ink-soft">{SCORE_FORMULA}</p>
      </section>

      <RulePacks />
      <Evaluation />

      <section className="notice notice-neutral">
        <strong>Disclaimer.</strong> Bol Ke Check is an automated pre-check. It flags risk and
        suggests safer wording. It is not legal clearance, and it is not affiliated with ASCI.
      </section>
    </div>
  )
}
