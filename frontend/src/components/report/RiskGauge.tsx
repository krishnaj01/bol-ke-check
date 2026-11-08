import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { RiskLevel } from '../../api/types'

export function RiskGauge({ score, level }: { score: number; level: RiskLevel }) {
  const { t } = useTranslation()
  const [shown, setShown] = useState(0)

  useEffect(() => {
    const frame = requestAnimationFrame(() => setShown(score))
    return () => cancelAnimationFrame(frame)
  }, [score])

  return (
    <div className="gauge flex flex-col items-center" data-level={level}>
      <svg viewBox="0 0 200 112" className="w-44" role="img" aria-label={`${score} / 100`}>
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
      <span className="mt-1 text-sm font-semibold">{t(`level.${level}`)}</span>
    </div>
  )
}
