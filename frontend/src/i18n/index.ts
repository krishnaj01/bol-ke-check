import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import { useLocaleStore } from '../stores/locale'
import en from './en.json'
import hi from './hi.json'

const initial = useLocaleStore.getState().locale
document.documentElement.lang = initial

void i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, hi: { translation: hi } },
  lng: initial,
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
  returnObjects: true,
})

useLocaleStore.subscribe(({ locale }) => {
  document.documentElement.lang = locale
  void i18n.changeLanguage(locale)
})

export default i18n
