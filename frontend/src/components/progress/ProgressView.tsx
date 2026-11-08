import { Check } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { Stage } from '../../api/types'
import { STAGES } from '../../lib/constants'
import { Wave } from '../ui'

function stateOf(index: number, current: number): 'done' | 'active' | 'waiting' {
  if (index < current) return 'done'
  return index === current ? 'active' : 'waiting'
}

export function ProgressView({ stage }: { stage: Stage }) {
  const { t } = useTranslation()
  const current = stage === 'done' ? STAGES.length : STAGES.indexOf(stage)
  return (
    <section className="mx-auto flex w-full max-w-[36rem] flex-col gap-6">
      <div>
        <p className="eyebrow m-0">{t('stage.eyebrow')}</p>
        <h1 className="mt-1 text-2xl">{t('stage.title')}</h1>
      </div>
      <ol className="card m-0 list-none px-5 py-2" aria-live="polite">
        {STAGES.map((item, index) => {
          const state = stateOf(index, current)
          return (
            <li key={item} className="stage" data-state={state}>
              <span className="stage-dot">
                {state === 'done' ? <Check size={14} /> : index + 1}
              </span>
              <span className="flex items-center justify-between gap-3">
                <span className="font-semibold">{t(`stage.${item}`)}</span>
                {state === 'active' && <Wave bars={8} live />}
              </span>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
