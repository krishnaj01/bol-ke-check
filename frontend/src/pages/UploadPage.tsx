import { Play } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { useCreateCheck } from '../api/hooks'
import type { CheckForm as CheckFormValues } from '../api/types'
import { CheckForm } from '../components/upload/CheckForm'
import { Hi } from '../components/ui'
import { SAMPLES } from '../lib/constants'
import { useUploadStore } from '../stores/upload'

function friendlyError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 413) return 'That file is too large. The limit is 100 MB.'
    if (error.status === 415) return 'Please use MP4, MOV, WEBM, MP3, WAV or M4A.'
    if (error.status === 429) return 'The demo has reached its usage limit for now.'
  }
  return 'We could not start the check. Is the backend running?'
}

export function UploadPage() {
  const navigate = useNavigate()
  const createCheck = useCreateCheck()
  const [message, setMessage] = useState<string | null>(null)
  const [loadingSample, setLoadingSample] = useState<string | null>(null)

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
    const { file, category, paidCollab, brand, speakSummary } = useUploadStore.getState()
    if (file) void start({ file, category, paidCollab, brand, speakSummary })
  }

  async function trySample(sample: (typeof SAMPLES)[number]) {
    setLoadingSample(sample.file)
    try {
      const response = await fetch(`/samples/${sample.file}`)
      const blob = await response.blob()
      await start({
        file: new File([blob], sample.file, { type: 'video/mp4' }),
        category: sample.category,
        paidCollab: true,
        brand: sample.brand,
        speakSummary: true,
      })
    } finally {
      setLoadingSample(null)
    }
  }

  return (
    <div className="grid gap-10 lg:grid-cols-[1.1fr_1fr] lg:gap-14">
      <section className="flex flex-col gap-6">
        <h1 className="hero-title" lang="hi">
          बोलने से पहले, <em>चेक</em> करो।
        </h1>
        <p className="m-0 max-w-[34rem] text-lg text-ink-soft">
          Upload a draft reel. Get every risky spoken Hinglish claim with its timestamp, the rule
          it breaks and a safer line to say instead, before you post.
        </p>

        <figure className="m-0 border-l-4 border-accent pl-4">
          <blockquote className="display m-0 text-2xl">97.3%</blockquote>
          <figcaption className="text-sm text-ink-soft">
            of influencer ads ASCI reviewed in FY26 needed changes. Caption scanners never hear
            what was said on camera.
          </figcaption>
        </figure>

        <div>
          <h2 className="eyebrow mb-3 font-normal">
            Try a sample · <Hi>नमूना चलाएँ</Hi>
          </h2>
          <div className="grid gap-2 sm:grid-cols-3">
            {SAMPLES.map((sample) => (
              <button
                key={sample.file}
                type="button"
                className="chip"
                disabled={loadingSample !== null || createCheck.isPending}
                onClick={() => void trySample(sample)}
              >
                <span lang="hi" className="flex items-center gap-1">
                  <Play size={12} className="text-accent-ink" /> {sample.hindi}
                </span>
                <small>
                  {loadingSample === sample.file ? 'Starting…' : sample.blurb}
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
  )
}
