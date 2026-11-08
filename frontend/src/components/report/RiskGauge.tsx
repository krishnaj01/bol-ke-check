import { useEffect, useState } from 'react'
import type { RiskLevel } from '../../api/types'
import { LEVEL_LABEL } from '../../lib/constants'
import { Hi } from '../ui'

export function RiskGauge({ score, level }: { score: number; level: RiskLevel }) {
  const [shown, setShown] = useState(0)

  useEffect(() => {
    const frame = requestAnimationFrame(() => setShown(score))
    return () => cancelAnimationFrame(frame)
  }, [score])

  const { label, hindi } = LEVEL_LABEL[level]
  return (
    <div className="gauge flex flex-col items-center" data-level={level}>
      <svg viewBox="0 0 200 112" className="w-44" role="img" aria-label={`Risk ${score} of 100`}>
        <path className="gauge-track" d="M 16 100 A 84 84 0 0 1 184 100" pathLength={100} />
        <path
          className="gauge-value"
          d="M 16 100 A 84 84 0 0 1 184 100"
          pathLength={100}
          strokeDasharray={100}
          strokeDashoffset={100 - shown}
        />
      </svg>
      <span className="gauge-number -mt-12">{score}</span>
      <span className="mt-1 text-sm font-semibold">
        <Hi>{hindi}</Hi> · {label}
      </span>
    </div>
  )
}
