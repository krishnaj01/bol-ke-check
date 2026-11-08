import { create } from 'zustand'

interface PlayerState {
  currentTime: number
  seekRequest: { time: number; id: number } | null
  setCurrentTime: (time: number) => void
  seek: (time: number) => void
  reset: () => void
}

export const usePlayerStore = create<PlayerState>()((set) => ({
  currentTime: 0,
  seekRequest: null,
  setCurrentTime: (currentTime) => set({ currentTime }),
  seek: (time) =>
    set((state) => ({
      currentTime: time,
      seekRequest: { time, id: (state.seekRequest?.id ?? 0) + 1 },
    })),
  reset: () => set({ currentTime: 0, seekRequest: null }),
}))
