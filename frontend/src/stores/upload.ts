import { create } from 'zustand'
import type { Category } from '../api/types'

interface UploadState {
  file: File | null
  category: Category
  paidCollab: boolean
  brand: string
  speakSummary: boolean
  setFile: (file: File | null) => void
  setCategory: (category: Category) => void
  setPaidCollab: (paidCollab: boolean) => void
  setBrand: (brand: string) => void
  setSpeakSummary: (speakSummary: boolean) => void
}

export const useUploadStore = create<UploadState>()((set) => ({
  file: null,
  category: 'personal_care',
  paidCollab: false,
  brand: '',
  speakSummary: true,
  setFile: (file) => set({ file }),
  setCategory: (category) => set({ category }),
  setPaidCollab: (paidCollab) => set({ paidCollab }),
  setBrand: (brand) => set({ brand }),
  setSpeakSummary: (speakSummary) => set({ speakSummary }),
}))
