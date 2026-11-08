import { Play } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { useCreateCheck } from '../api/hooks'
import type { CheckForm as CheckFormValues } from '../api/types'
import { Wave } from '../components/ui'
import { CheckForm } from '../components/upload/CheckForm'
import { MAX_UPLOAD_MB, SAMPLES } from '../lib/constants'
import { useUploadStore } from '../stores/upload'

const STATS = [
  { value: '97.3%', key: 'home.stat1' },
  { value: '69%', key: 'home.stat2' },
]

export function UploadPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const createCheck = useCreateCheck()
  const [message, setMessage] = useState<string | null>(null)
  const [loadingSample, setLoadingSample] = useState<string | null>(null)

  function friendlyError(error: unknown): string {
    if (error instanceof ApiError) {
      if (error.status === 413) return t('form.tooBig', { mb: MAX_UPLOAD_MB })
      if (error.status === 415) return t('form.badType')
      if (error.status === 429) return t('form.limitReached')
    }
    return t('form.startFailed')
  }

  async function start(values: CheckFormValues) {
    setMessage(null)
    try {
      const { check_id: id } = await createCheck.mutateAsync(values)
      void navigate(`/check/${id}`)
    } catch (error) {
      setMessage(friendlyError(error))
    }
  }

  function submitForm() {
    const { file, category, audioLanguage, paidCollab, brand, speakSummary } =
      useUploadStore.getState()
    if (file) void start({ file, category, audioLanguage, paidCollab, brand, speakSummary })
  }

  async function trySample(sample: (typeof SAMPLES)[number]) {
    setLoadingSample(sample.file)
    try {
      const response = await fetch(`/samples/${sample.file}`)
      const blob = await response.blob()
      await start({
        file: new File([blob], sample.file, { type: 'video/mp4' }),
        category: sample.category,
        audioLanguage: 'hi-IN',
        paidCollab: true,
        brand: sample.brand,
        speakSummary: true,
      })
    } finally {
      setLoadingSample(null)
    }
  }

  return (
    <div className="flex flex-col gap-16">
      <div className="grid items-start gap-10 lg:grid-cols-[1.1fr_1fr] lg:gap-14">
        <section className="flex flex-col items-start gap-6 lg:pt-6">
          <span className="pill">
            <Wave bars={4} /> {t('home.eyebrow')}
          </span>
          <h1 className="hero-title">
            {t('home.titleStart')} <em>{t('home.titleAccent')}</em>
          </h1>
          <p className="m-0 max-w-[34rem] text-lg text-ink-soft">{t('home.lede')}</p>

          <dl className="m-0 grid w-full gap-6 sm:grid-cols-2">
            {STATS.map((stat) => (
              <div key={stat.key}>
                <dt className="stat-value">{stat.value}</dt>
                <dd className="m-0 mt-1 text-sm text-ink-soft">{t(stat.key)}</dd>
              </div>
            ))}
          </dl>

          <div className="w-full">
            <h2 className="eyebrow mb-3 font-semibold">{t('home.samples')}</h2>
            <div className="grid gap-2 sm:grid-cols-3">
              {SAMPLES.map((sample) => (
                <button
                  key={sample.file}
                  type="button"
                  className="sample-card"
                  disabled={loadingSample !== null || createCheck.isPending}
                  onClick={() => void trySample(sample)}
                >
                  <span className="flex items-center gap-1.5">
                    <Play size={12} className="text-accent-text" />
                    {t(`samples.${sample.key}.title`)}
                  </span>
                  <small>
                    {loadingSample === sample.file
                      ? t('home.starting')
                      : t(`samples.${sample.key}.blurb`)}
                  </small>
                </button>
              ))}
            </div>
          </div>
        </section>

        <CheckForm
          onSubmit={submitForm}
          busy={createCheck.isPending}
          error={message}
          onError={setMessage}
        />
      </div>

      <section className="flex flex-col gap-6">
        <h2 className="text-2xl">{t('home.stepsTitle')}</h2>
        <ol className="m-0 grid list-none gap-4 p-0 md:grid-cols-3">
          {[1, 2, 3].map((step) => (
            <li key={step} className="card flex flex-col gap-3 p-5">
              <span className="step-number">{step}</span>
              <h3 className="text-lg">{t(`home.step${step}Title`)}</h3>
              <p className="m-0 text-sm text-ink-soft">{t(`home.step${step}Body`)}</p>
            </li>
          ))}
        </ol>
      </section>
    </div>
  )
}
