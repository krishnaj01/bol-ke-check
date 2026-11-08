import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type Theme = 'light' | 'dark'

interface ThemeState {
  theme: Theme
  toggle: () => void
}

const initialTheme = (document.documentElement.dataset.theme as Theme) ?? 'light'

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: initialTheme,
      toggle: () => set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),
    }),
    { name: 'bkc-ui-theme' },
  ),
)

useThemeStore.subscribe(({ theme }) => {
  document.documentElement.dataset.theme = theme
})
