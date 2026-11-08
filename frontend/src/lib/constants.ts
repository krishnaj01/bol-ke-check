import type { Category, ErrorCode, RiskLevel, Severity, Stage } from '../api/types'

export const MAX_UPLOAD_MB = 100
export const ACCEPTED_EXTENSIONS = ['.mp4', '.mov', '.webm', '.mp3', '.wav', '.m4a']

export const CATEGORIES: { id: Category; label: string; hindi: string }[] = [
  { id: 'personal_care', label: 'Personal care', hindi: 'त्वचा और बाल' },
  { id: 'food', label: 'Food', hindi: 'खान-पान' },
  { id: 'finance', label: 'Finance', hindi: 'पैसा' },
  { id: 'health', label: 'Health', hindi: 'सेहत' },
  { id: 'betting', label: 'Betting / gaming', hindi: 'सट्टा' },
  { id: 'general', label: 'General', hindi: 'सामान्य' },
]

export const categoryLabel = (id: Category) =>
  CATEGORIES.find((category) => category.id === id)?.label ?? id

export const SEVERITY_LABEL: Record<Severity, { label: string; hindi: string }> = {
  high: { label: 'High', hindi: 'ख़तरा' },
  medium: { label: 'Medium', hindi: 'सावधान' },
  low: { label: 'Low', hindi: 'ध्यान दें' },
}

export const LEVEL_LABEL: Record<RiskLevel, { label: string; hindi: string }> = {
  high: { label: 'High risk', hindi: 'ज़्यादा ख़तरा' },
  medium: { label: 'Medium risk', hindi: 'थोड़ा ख़तरा' },
  low: { label: 'Low risk', hindi: 'कम ख़तरा' },
}

export const STAGES: { id: Stage; label: string; hindi: string }[] = [
  { id: 'extract', label: 'Extracting audio', hindi: 'आवाज़ अलग कर रहे हैं' },
  { id: 'transcribe', label: 'Transcribing with Gnani Prisma', hindi: 'सुन रहे हैं' },
  { id: 'rules', label: 'Checking rules', hindi: 'नियम जाँच रहे हैं' },
  { id: 'review', label: 'Reviewing with Gnani Evon', hindi: 'बारीकी से समझ रहे हैं' },
  { id: 'summary', label: 'Writing summary with Gnani Timbre', hindi: 'सार बोल रहे हैं' },
]

export const ERROR_COPY: Record<ErrorCode, { title: string; body: string; retry: boolean }> = {
  no_speech: {
    title: 'Is file mein koi boli nahi mili',
    body: 'We could not find speech in this file. Check that the audio track is not muted.',
    retry: false,
  },
  too_long: {
    title: 'Video bahut lamba hai',
    body: 'Bol Ke Check takes up to 3 minutes of audio. Trim the reel and upload it again.',
    retry: false,
  },
  bad_media: {
    title: 'Ye file khul nahi rahi',
    body: 'We could not read this file. Export it again as MP4, MOV, WEBM, MP3, WAV or M4A.',
    retry: false,
  },
  gnani_failed: {
    title: 'Gnani se jawab nahi aaya',
    body: 'The call to Gnani failed. Retrying reuses finished transcripts, so it costs little.',
    retry: true,
  },
  internal: {
    title: 'Kuch gadbad ho gayi',
    body: 'Something went wrong on our side while checking this file.',
    retry: true,
  },
}

export const SAMPLES: {
  file: string
  title: string
  hindi: string
  blurb: string
  category: Category
  brand: string
}[] = [
  {
    file: 'sample_no_disclosure.mp4',
    title: 'Missing disclosure',
    hindi: 'छुपा हुआ ऐड',
    blurb: 'Skincare reel, paid, never says so',
    category: 'personal_care',
    brand: 'DemoSkin',
  },
  {
    file: 'sample_finance_claims.mp4',
    title: 'Guaranteed returns',
    hindi: 'पैसा डबल पक्का',
    blurb: 'Finance reel with risky promises',
    category: 'finance',
    brand: 'DemoFin',
  },
  {
    file: 'sample_clean.mp4',
    title: 'Clean reel',
    hindi: 'साफ़ वीडियो',
    blurb: 'Disclosed early, honest claims',
    category: 'personal_care',
    brand: 'DemoSkin',
  },
]

export const SCRIPT_RIBBON: { text: string; script: string; lang: string }[] = [
  { text: 'बोल के चेक', script: 'script-devanagari', lang: 'hi' },
  { text: 'বোল কে চেক', script: 'script-bangla', lang: 'bn' },
  { text: 'போல் கே செக்', script: 'script-tamil', lang: 'ta' },
  { text: 'బోల్ కే చెక్', script: 'script-telugu', lang: 'te' },
  { text: 'ಬೋಲ್ ಕೆ ಚೆಕ್', script: 'script-kannada', lang: 'kn' },
  { text: 'બોલ કે ચેક', script: 'script-gujarati', lang: 'gu' },
  { text: 'ਬੋਲ ਕੇ ਚੈੱਕ', script: 'script-gurmukhi', lang: 'pa' },
  { text: 'ബോൽ കെ ചെക്ക്', script: 'script-malayalam', lang: 'ml' },
  { text: 'Bol Ke Check', script: '', lang: 'en' },
]

export const SCORE_FORMULA =
  'Start at 0. Add 35 per high flag, 15 per medium, 5 per low. Evon flags are multiplied by their confidence. Capped at 100. 0–24 low, 25–59 medium, 60+ high.'
