import type { CheckForm, EvalMetrics, Report, RulePack } from './types'

export const API_BASE: string = import.meta.env.VITE_API_BASE ?? ''

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export const mediaUrl = (path: string) => `${API_BASE}${path}`

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(response.status, body?.detail ?? response.statusText)
  }
  return response.json() as Promise<T>
}

export function createCheck(form: CheckForm): Promise<{ check_id: string }> {
  const body = new FormData()
  body.append('file', form.file)
  body.append('category', form.category)
  body.append('language', form.audioLanguage)
  body.append('paid_collab', String(form.paidCollab))
  body.append('speak_summary', String(form.speakSummary))
  if (form.brand.trim()) body.append('brand', form.brand.trim())
  return request('/api/v1/check', { method: 'POST', body })
}

export const getCheck = (id: string) => request<Report>(`/api/v1/check/${id}`)

export const retryCheck = (id: string) =>
  request<{ check_id: string }>(`/api/v1/check/${id}/retry`, { method: 'POST' })

export const getRules = (category: string) =>
  request<RulePack>(`/api/v1/rules?category=${encodeURIComponent(category)}`)

export const getHealth = () => request<{ status: string; mock: boolean }>('/health')

export async function getEvalMetrics(): Promise<EvalMetrics | null> {
  try {
    return await request<EvalMetrics>('/media/eval/metrics.json')
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null
    throw error
  }
}
