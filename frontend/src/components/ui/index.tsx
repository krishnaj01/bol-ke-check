import type { CSSProperties, ReactNode } from 'react'
import { SEVERITY_LABEL } from '../../lib/constants'
import type { Severity } from '../../api/types'

export const Hi = ({ children }: { children: ReactNode }) => <span lang="hi">{children}</span>

export function Switch({
  checked,
  onChange,
  label,
}: {
  checked: boolean
  onChange: (value: boolean) => void
  label: string
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      className="switch"
      onClick={() => onChange(!checked)}
    />
  )
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  const { label, hindi } = SEVERITY_LABEL[severity]
  return (
    <span className={`badge badge-${severity}`}>
      <Hi>{hindi}</Hi> · {label}
    </span>
  )
}

const BARS = [0.35, 0.7, 1, 0.55, 0.85, 0.4, 0.95, 0.6, 0.3, 0.75, 0.5, 0.9]

export function Wave({ bars = 6, live = false }: { bars?: number; live?: boolean }) {
  return (
    <span className="wave" data-live={live} aria-hidden="true">
      {BARS.slice(0, bars).map((height, index) => (
        <i key={index} style={{ '--bar': height, '--i': index } as CSSProperties} />
      ))}
    </span>
  )
}
