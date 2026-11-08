import { Check } from 'lucide-react'
import type { Stage } from '../../api/types'
import { STAGES } from '../../lib/constants'
import { Hi, Wave } from '../ui'

function stateOf(index: number, current: number): 'done' | 'active' | 'waiting' {
  if (index < current) return 'done'
  return index === current ? 'active' : 'waiting'
}

export function ProgressView({ stage }: { stage: Stage }) {
  const current = stage === 'done' ? STAGES.length : STAGES.findIndex((s) => s.id === stage)
  return (
    <section className="mx-auto flex max-w-[36rem] flex-col gap-6">
      <div>
        <p className="eyebrow m-0">Checking your reel</p>
        <h1 className="display mt-1 text-2xl" lang="hi">
          ज़रा रुकिए, सुन रहे हैं…
        </h1>
      </div>
      <ol className="card m-0 list-none px-5 py-2" aria-live="polite">
        {STAGES.map((item, index) => {
          const state = stateOf(index, current)
          return (
            <li key={item.id} className="stage" data-state={state}>
              <span className="stage-dot">
                {state === 'done' ? <Check size={14} /> : index + 1}
              </span>
              <span className="flex items-center justify-between gap-3">
                <span>
                  <span className="block font-semibold">{item.label}</span>
                  <span className="block text-sm">
                    <Hi>{item.hindi}</Hi>
                  </span>
                </span>
                {state === 'active' && <Wave bars={8} live />}
              </span>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
