import { useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import type { Flag, Segment } from '../../api/types'
import { formatClock } from '../../lib/format'
import { flagsInSegment, highlightParts } from '../../lib/highlight'
import { usePlayerStore } from '../../stores/player'

export function Transcript({ segments, flags }: { segments: Segment[]; flags: Flag[] }) {
  const { t } = useTranslation()
  const containerRef = useRef<HTMLDivElement>(null)
  const seek = usePlayerStore((state) => state.seek)
  const activeId = usePlayerStore(
    (state) =>
      segments.find(
        (segment) => state.currentTime >= segment.start_sec && state.currentTime < segment.end_sec,
      )?.id,
  )

  useEffect(() => {
    const container = containerRef.current
    const line = container?.querySelector<HTMLElement>('[data-active="true"]')
    if (container && line) {
      container.scrollTo({ top: line.offsetTop - container.clientHeight / 3, behavior: 'smooth' })
    }
  }, [activeId])

  return (
    <section className="card flex flex-col overflow-hidden">
      <header className="border-b border-line px-4 py-3">
        <h2 className="text-lg">{t('report.transcript')}</h2>
        <p className="m-0 text-xs text-ink-faint">{t('report.heardBy')}</p>
      </header>
      <div ref={containerRef} className="transcript relative py-1">
        {segments.map((segment) => (
          <button
            key={segment.id}
            type="button"
            className="transcript-line"
            data-active={segment.id === activeId}
            onClick={() => seek(segment.start_sec)}
          >
            <span className="time pt-0.5">{formatClock(segment.start_sec)}</span>
            <span>
              {highlightParts(segment.text, flagsInSegment(segment, flags)).map((part, index) =>
                part.severity ? (
                  <mark key={index} className="flag-mark" data-severity={part.severity}>
                    {part.text}
                  </mark>
                ) : (
                  <span key={index}>{part.text}</span>
                ),
              )}
            </span>
          </button>
        ))}
      </div>
    </section>
  )
}
