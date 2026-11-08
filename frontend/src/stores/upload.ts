import { create } from 'zustand'
import type { AudioLanguage, Category } from '../api/types'

interface UploadState {
  file: File | null
  category: Category
  audioLanguage: AudioLanguage
  paidCollab: boolean
  brand: string
  speakSummary: boolean
  setFile: (file: File | null) => void
  setCategory: (category: Category) => void
  setAudioLanguage: (audioLanguage: AudioLanguage) => void
  setPaidCollab: (paidCollab: boolean) => void
  setBrand: (brand: string) => void
  setSpeakSummary: (speakSummary: boolean) => void
}

export const useUploadStore = create<UploadState>()((set) => ({
  file: null,
  category: 'personal_care',
  audioLanguage: 'hi-IN',
  paidCollab: false,
  brand: '',
  speakSummary: true,
  setFile: (file) => set({ file }),
  setCategory: (category) => set({ category }),
  setAudioLanguage: (audioLanguage) => set({ audioLanguage }),
  setPaidCollab: (paidCollab) => set({ paidCollab }),
  setBrand: (brand) => set({ brand }),
  setSpeakSummary: (speakSummary) => set({ speakSummary }),
}))
