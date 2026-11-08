import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useEvalMetrics, useRules } from '../api/hooks'
import type { Category, EvalMetrics } from '../api/types'
import { SeverityBadge } from '../components/ui'
import { CATEGORIES, PIPELINE } from '../lib/constants'
import { formatPercent } from '../lib/format'

function RulePacks() {
  const { t } = useTranslation()
  const [category, setCategory] = useState<Category>('personal_care')
  const { data, isLoading, isError } = useRules(category)
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-xl">{t('about.rules')}</h2>
      <p className="notice notice-medium m-0">{t('about.rulesNote')}</p>
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((item) => (
          <button
            key={item}
            type="button"
            className="chip"
            aria-pressed={category === item}
            onClick={() => setCategory(item)}
          >
            {t(`category.${item}`)}
          </button>
        ))}
      </div>
      {isError && <p className="notice notice-high m-0">{t('about.rulesError')}</p>}
      {isLoading && <p className="m-0 text-ink-faint">{t('about.loading')}</p>}
      <div className="grid gap-3 md:grid-cols-2">
        {data?.rules.map((rule) => (
          <article key={rule.id} className="card flex flex-col gap-2 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="time text-ink-faint">{rule.id}</span>
              <SeverityBadge severity={rule.severity} />
              {!rule.verified && <span className="badge badge-outline">{t('report.pending')}</span>}
            </div>
            <h3 className="text-base">{rule.title}</h3>
            <p className="m-0 text-sm text-ink-soft">{rule.explanation}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

function MetricsTable({ metrics }: { metrics: EvalMetrics }) {
  const { t } = useTranslation()
  const rows: [string, string][] = [
    [t('about.clips'), String(metrics.clips)],
    [
      t('about.recall'),
      t('about.recallValue', {
        caught: metrics.caught,
        planted: metrics.planted,
        percent: formatPercent(metrics.recall),
      }),
    ],
    [
      t('about.falseAlarms'),
      t('about.falseAlarmsValue', {
        count: metrics.false_alarms,
        perClip: metrics.false_alarms_per_clip.toFixed(2),
      }),
    ],
    [
      t('about.disclosureAccuracy'),
      metrics.disclosure_accuracy === null ? '—' : formatPercent(metrics.disclosure_accuracy),
    ],
    [t('about.layerSplit'), `${metrics.layer_split.rule} / ${metrics.layer_split.llm}`],
    [
      t('about.latency'),
      metrics.median_latency_sec === null
        ? '—'
        : t('about.seconds', { value: metrics.median_latency_sec.toFixed(1) }),
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
  const { t } = useTranslation()
  const { data: metrics, isLoading } = useEvalMetrics()
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-xl">{t('about.evaluation')}</h2>
      {isLoading && <p className="m-0 text-ink-faint">{t('about.loading')}</p>}
      {!isLoading && !metrics && <p className="notice notice-neutral m-0">{t('about.noEval')}</p>}
      {metrics && metrics.partial_clips > 0 && (
        <p className="notice notice-medium m-0">
          {t('about.partialEval', { partial: metrics.partial_clips, clips: metrics.clips })}
        </p>
      )}
      {metrics && <MetricsTable metrics={metrics} />}
    </section>
  )
}

export function AboutPage() {
  const { t } = useTranslation()
  return (
    <div className="flex flex-col gap-10">
      <header className="flex max-w-[44rem] flex-col gap-3">
        <h1 className="text-2xl">{t('about.title')}</h1>
        <p className="m-0 text-lg text-ink-soft">{t('about.lede')}</p>
      </header>

      <section className="flex flex-col gap-3">
        <h2 className="text-xl">{t('about.pipeline')}</h2>
        <ol className="pipeline m-0 list-none p-0">
          {PIPELINE.map((node, index) => {
            const [name, role] = t(`pipeline.${node.key}`, { returnObjects: true }) as string[]
            return (
              <li key={node.key} className="pipeline-node" data-gnani={Boolean(node.gnani)}>
                <span className="time text-ink-faint">{index + 1}</span>
                <p className="m-0 font-semibold">{name}</p>
                <p className="m-0 text-sm text-ink-soft">{role}</p>
              </li>
            )
          })}
        </ol>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-xl">{t('about.score')}</h2>
        <p className="m-0 text-ink-soft">{t('report.formula')}</p>
      </section>

      <RulePacks />
      <Evaluation />

      <section className="notice notice-neutral">
        <strong>{t('about.disclaimerTitle')}</strong> {t('about.disclaimer')}
      </section>
    </div>
  )
}
