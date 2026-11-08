import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import {
  API_BASE,
  createCheck,
  getCheck,
  getEvalMetrics,
  getHealth,
  getRules,
  retryCheck,
} from './client'
import type { Category, ProgressSnapshot, Report, Status } from './types'

const POLL_FALLBACK_MS = 2000
const TERMINAL: Status[] = ['complete', 'partial', 'failed']

export const isTerminal = (status: Status) => TERMINAL.includes(status)

const checkKey = (id: string) => ['check', id] as const

export function useCheck(id: string) {
  return useQuery({
    queryKey: checkKey(id),
    queryFn: () => getCheck(id),
    retry: false,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status && isTerminal(status) ? false : POLL_FALLBACK_MS
    },
  })
}

export function useCheckEvents(id: string, enabled: boolean) {
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!enabled) return
    const source = new EventSource(`${API_BASE}/api/v1/check/${id}/events`)
    source.addEventListener('progress', (event) => {
      const snapshot = JSON.parse((event as MessageEvent<string>).data) as ProgressSnapshot
      queryClient.setQueryData<Report>(checkKey(id), (old) => old && { ...old, ...snapshot })
      if (isTerminal(snapshot.status)) {
        source.close()
        void queryClient.invalidateQueries({ queryKey: checkKey(id) })
      }
    })
    source.onerror = () => source.close()
    return () => source.close()
  }, [id, enabled, queryClient])
}

export const useCreateCheck = () => useMutation({ mutationFn: createCheck })

export function useRetryCheck(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => retryCheck(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: checkKey(id) }),
  })
}

export const useRules = (category: Category) =>
  useQuery({
    queryKey: ['rules', category],
    queryFn: () => getRules(category),
    staleTime: Infinity,
  })

export const useEvalMetrics = () =>
  useQuery({ queryKey: ['eval'], queryFn: getEvalMetrics, retry: false })

export const useHealth = () =>
  useQuery({ queryKey: ['health'], queryFn: getHealth, staleTime: Infinity, retry: false })
