import type { AudioLanguage, Category, Stage } from '../api/types'

export const MAX_UPLOAD_MB = 100
export const ACCEPTED_EXTENSIONS = ['.mp4', '.mov', '.webm', '.mp3', '.wav', '.m4a']

export const CATEGORIES: Category[] = [
  'personal_care',
  'food',
  'finance',
  'health',
  'betting',
  'general',
]

export const AUDIO_LANGUAGES: AudioLanguage[] = ['hi-IN', 'en-IN', 'auto']

export const STAGES: Stage[] = ['extract', 'transcribe', 'rules', 'review', 'summary']

export const RETRYABLE_ERRORS = ['gnani_failed', 'internal']

export const SAMPLES: { file: string; key: string; category: Category; brand: string }[] = [
  {
    file: 'sample_no_disclosure.mp4',
    key: 'noDisclosure',
    category: 'personal_care',
    brand: 'DemoSkin',
  },
  { file: 'sample_finance_claims.mp4', key: 'finance', category: 'finance', brand: 'DemoFin' },
  { file: 'sample_clean.mp4', key: 'clean', category: 'personal_care', brand: 'DemoSkin' },
]

export const PIPELINE: { key: string; gnani?: boolean }[] = [
  { key: 'reel' },
  { key: 'api' },
  { key: 'ffmpeg' },
  { key: 'vad' },
  { key: 'prisma', gnani: true },
  { key: 'rules' },
  { key: 'evon', gnani: true },
  { key: 'score' },
  { key: 'timbre', gnani: true },
]

export const LINKS = {
  asci: 'https://www.ascionline.in/',
  asciVideo: 'https://www.youtube.com/watch?v=BikMAhxFwfk',
  gnaniDocs: 'https://docs.gnani.ai/',
}
