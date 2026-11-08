export type Severity = 'high' | 'medium' | 'low'
export type RiskLevel = 'low' | 'medium' | 'high'
export type Status = 'queued' | 'transcribing' | 'reviewing' | 'complete' | 'partial' | 'failed'
export type Stage = 'queued' | 'extract' | 'transcribe' | 'rules' | 'review' | 'summary' | 'done'
export type ErrorCode = 'no_speech' | 'too_long' | 'bad_media' | 'gnani_failed' | 'internal'
export type Category = 'personal_care' | 'food' | 'finance' | 'health' | 'betting' | 'general'

export interface Segment {
  id: string
  start_sec: number
  end_sec: number
  text: string
}

export interface Flag {
  id: string
  rule_id: string
  family: string
  title: string
  layer: 'rule' | 'llm'
  severity: Severity
  start_sec: number
  end_sec: number
  quote: string
  explanation: string
  suggested_rewrite: string
  confidence: number
  verified: boolean
  source: string | null
}

export interface Disclosure {
  required: boolean
  found: boolean
  first_at_sec: number | null
}

export interface Report {
  check_id: string
  category: Category
  risk_score: number | null
  risk_level: RiskLevel | null
  duration_sec: number | null
  disclosure: Disclosure | null
  flags: Flag[]
  segments: Segment[]
  summary_hi: string | null
  summary_audio_url: string | null
  media_url: string | null
  disclaimer: string
  status: Status
  stage: Stage
  error: ErrorCode | null
}

export interface ProgressSnapshot {
  status: Status
  stage: Stage
  error: ErrorCode | null
}

export interface Rule {
  id: string
  category: string
  family: string
  title: string
  severity: Severity
  patterns: string[]
  explanation: string
  suggested_fix: string
  source: string | null
  verified: boolean
}

export interface RulePack {
  category: Category
  families: Record<string, string>
  rules: Rule[]
}

export interface EvalMetrics {
  mode: 'mock' | 'real'
  dataset_version: string
  generated_at: string
  clips: number
  planted: number
  caught: number
  recall: number
  false_alarms: number
  false_alarms_per_clip: number
  disclosure_accuracy: number | null
  layer_split: { rule: number; llm: number }
  median_latency_sec: number | null
}

export interface CheckForm {
  file: File
  category: Category
  paidCollab: boolean
  brand: string
  speakSummary: boolean
}
