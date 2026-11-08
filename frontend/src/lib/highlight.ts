import type { Flag, Segment, Severity } from '../api/types'

export interface TextPart {
  text: string
  severity: Severity | null
}

const RANK: Record<Severity, number> = { high: 3, medium: 2, low: 1 }

export const isPlaceholderQuote = (flag: Flag) => flag.quote.startsWith('(')

export const flagsInSegment = (segment: Segment, flags: Flag[]) =>
  flags.filter((flag) => !isPlaceholderQuote(flag) && flag.start_sec === segment.start_sec)

export function highlightParts(text: string, flags: Flag[]): TextPart[] {
  const lower = text.toLowerCase()
  const ranges = flags
    .map((flag) => {
      const start = lower.indexOf(flag.quote.toLowerCase())
      return { start, end: start + flag.quote.length, severity: flag.severity }
    })
    .filter((range) => range.start >= 0)
    .sort((a, b) => a.start - b.start || RANK[b.severity] - RANK[a.severity])

  const parts: TextPart[] = []
  let cursor = 0
  for (const range of ranges) {
    if (range.start < cursor) continue
    if (range.start > cursor) parts.push({ text: text.slice(cursor, range.start), severity: null })
    parts.push({ text: text.slice(range.start, range.end), severity: range.severity })
    cursor = range.end
  }
  if (cursor < text.length) parts.push({ text: text.slice(cursor), severity: null })
  return parts
}
