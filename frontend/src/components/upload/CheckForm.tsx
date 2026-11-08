import { FileAudio, UploadCloud, X } from 'lucide-react'
import { useState } from 'react'
import type { DragEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { ACCEPTED_EXTENSIONS, AUDIO_LANGUAGES, CATEGORIES, MAX_UPLOAD_MB } from '../../lib/constants'
import { useUploadStore } from '../../stores/upload'
import { Segmented, Switch } from '../ui'

function DropZone({ onError }: { onError: (message: string | null) => void }) {
  const { t } = useTranslation()
  const [dragging, setDragging] = useState(false)
  const { file, setFile } = useUploadStore()

  function problemWith(candidate: File): string | null {
    const name = candidate.name.toLowerCase()
    if (!ACCEPTED_EXTENSIONS.some((extension) => name.endsWith(extension))) {
      return t('form.badType')
    }
    if (candidate.size > MAX_UPLOAD_MB * 1024 * 1024) {
      return t('form.tooBig', { mb: MAX_UPLOAD_MB })
    }
    return null
  }

  function accept(candidate: File | undefined) {
    if (!candidate) return
    const problem = problemWith(candidate)
    onError(problem)
    setFile(problem ? null : candidate)
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault()
    setDragging(false)
    accept(event.dataTransfer.files[0])
  }

  if (file) {
    return (
      <div className="dropzone dropzone-filled">
        <FileAudio size={22} className="text-accent-text" />
        <p className="m-0 max-w-full truncate font-semibold">{file.name}</p>
        <button type="button" className="btn" onClick={() => setFile(null)}>
          <X size={14} /> {t('form.remove')}
        </button>
      </div>
    )
  }

  return (
    <label
      className="dropzone"
      data-active={dragging}
      onDragOver={(event) => {
        event.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      <UploadCloud size={26} className="text-accent-text" />
      <span className="font-semibold">{t('form.dropTitle')}</span>
      <span className="text-sm text-ink-soft">{t('form.dropHint')}</span>
      <span className="text-xs text-ink-faint">{t('form.dropLimits', { mb: MAX_UPLOAD_MB })}</span>
      <input
        type="file"
        className="sr-only"
        accept={ACCEPTED_EXTENSIONS.join(',')}
        onChange={(event) => accept(event.target.files?.[0])}
      />
    </label>
  )
}

function ToggleRow({
  title,
  hint,
  checked,
  onChange,
}: {
  title: string
  hint: string
  checked: boolean
  onChange: (value: boolean) => void
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span>
        <span className="block text-sm font-semibold">{title}</span>
        <span className="block text-xs text-ink-faint">{hint}</span>
      </span>
      <Switch checked={checked} onChange={onChange} label={title} />
    </div>
  )
}

export function CheckForm({
  onSubmit,
  busy,
  error,
  onError,
}: {
  onSubmit: () => void
  busy: boolean
  error: string | null
  onError: (message: string | null) => void
}) {
  const { t } = useTranslation()
  const state = useUploadStore()
  return (
    <form
      className="card flex flex-col gap-5 p-5 md:p-6"
      onSubmit={(event) => {
        event.preventDefault()
        onSubmit()
      }}
    >
      <DropZone onError={onError} />

      <div>
        <p className="eyebrow m-0 mb-2">{t('form.audioLanguage')}</p>
        <Segmented
          block
          label={t('form.audioLanguage')}
          value={state.audioLanguage}
          onChange={state.setAudioLanguage}
          options={AUDIO_LANGUAGES.map((value) => ({
            value,
            label: t(`audioLanguage.${value}`),
          }))}
        />
        <p className="m-0 mt-1.5 text-xs text-ink-faint">{t('form.audioLanguageHint')}</p>
      </div>

      <fieldset className="m-0 border-0 p-0">
        <legend className="eyebrow mb-2 p-0">{t('form.category')}</legend>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {CATEGORIES.map((category) => (
            <button
              key={category}
              type="button"
              className="chip"
              aria-pressed={state.category === category}
              onClick={() => state.setCategory(category)}
            >
              {t(`category.${category}`)}
            </button>
          ))}
        </div>
      </fieldset>

      <ToggleRow
        title={t('form.paidTitle')}
        hint={t('form.paidHint')}
        checked={state.paidCollab}
        onChange={state.setPaidCollab}
      />

      {state.paidCollab && (
        <input
          className="field"
          placeholder={t('form.brandPlaceholder')}
          aria-label={t('form.brandPlaceholder')}
          maxLength={120}
          value={state.brand}
          onChange={(event) => state.setBrand(event.target.value)}
        />
      )}

      <ToggleRow
        title={t('form.summaryTitle')}
        hint={t('form.summaryHint')}
        checked={state.speakSummary}
        onChange={state.setSpeakSummary}
      />

      {error && (
        <p role="alert" className="notice notice-high m-0">
          {error}
        </p>
      )}

      <button type="submit" className="btn btn-primary" disabled={!state.file || busy}>
        {busy ? t('form.uploading') : t('form.submit')}
      </button>
    </form>
  )
}
