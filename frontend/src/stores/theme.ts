import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type Theme = 'din' | 'raat'

interface ThemeState {
  theme: Theme
  toggle: () => void
}

const initialTheme = (document.documentElement.dataset.theme as Theme) ?? 'din'

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: initialTheme,
      toggle: () => set((state) => ({ theme: state.theme === 'din' ? 'raat' : 'din' })),
    }),
    { name: 'bkc-theme' },
  ),
)

useThemeStore.subscribe(({ theme }) => {
  document.documentElement.dataset.theme = theme
})
