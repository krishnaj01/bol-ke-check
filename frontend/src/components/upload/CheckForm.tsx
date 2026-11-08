import { FileAudio, UploadCloud, X } from 'lucide-react'
import { useState } from 'react'
import type { DragEvent } from 'react'
import { ACCEPTED_EXTENSIONS, CATEGORIES, MAX_UPLOAD_MB } from '../../lib/constants'
import { useUploadStore } from '../../stores/upload'
import { Hi, Switch } from '../ui'

function validateFile(file: File): string | null {
  const name = file.name.toLowerCase()
  if (!ACCEPTED_EXTENSIONS.some((extension) => name.endsWith(extension))) {
    return 'Please use MP4, MOV, WEBM, MP3, WAV or M4A.'
  }
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return `File is over ${MAX_UPLOAD_MB} MB.`
  return null
}

function DropZone({ onError }: { onError: (message: string | null) => void }) {
  const [dragging, setDragging] = useState(false)
  const { file, setFile } = useUploadStore()

  function accept(candidate: File | undefined) {
    if (!candidate) return
    const problem = validateFile(candidate)
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
        <FileAudio size={24} className="text-accent-ink" />
        <p className="m-0 max-w-full truncate font-semibold">{file.name}</p>
        <button type="button" className="btn" onClick={() => setFile(null)}>
          <X size={14} /> Remove
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
      <UploadCloud size={28} className="text-accent-ink" />
      <span className="text-lg font-semibold">
        <Hi>अपनी रील यहाँ डालें</Hi>
      </span>
      <span className="text-sm text-ink-soft">Drop your draft reel, or tap to choose</span>
      <span className="text-xs text-ink-faint">Up to 3 minutes · {MAX_UPLOAD_MB} MB</span>
      <input
        type="file"
        className="sr-only"
        accept={ACCEPTED_EXTENSIONS.join(',')}
        onChange={(event) => accept(event.target.files?.[0])}
      />
    </label>
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

      <fieldset className="m-0 border-0 p-0">
        <legend className="eyebrow mb-2 p-0">Category</legend>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {CATEGORIES.map((category) => (
            <button
              key={category.id}
              type="button"
              className="chip"
              aria-pressed={state.category === category.id}
              onClick={() => state.setCategory(category.id)}
            >
              {category.label}
              <small lang="hi">{category.hindi}</small>
            </button>
          ))}
        </div>
      </fieldset>

      <div className="flex items-center justify-between gap-4">
        <span>
          <span className="block font-semibold">This is a paid collaboration</span>
          <span className="block text-sm text-ink-faint">
            We then check that the ad is disclosed out loud
          </span>
        </span>
        <Switch
          checked={state.paidCollab}
          onChange={state.setPaidCollab}
          label="This is a paid collaboration"
        />
      </div>

      {state.paidCollab && (
        <input
          className="field"
          placeholder="Brand name (optional)"
          aria-label="Brand name"
          maxLength={120}
          value={state.brand}
          onChange={(event) => state.setBrand(event.target.value)}
        />
      )}

      <div className="flex items-center justify-between gap-4">
        <span>
          <span className="block font-semibold">Speak the summary in Hindi</span>
          <span className="block text-sm text-ink-faint">Read aloud by Gnani Timbre</span>
        </span>
        <Switch
          checked={state.speakSummary}
          onChange={state.setSpeakSummary}
          label="Speak the summary in Hindi"
        />
      </div>

      {error && (
        <p role="alert" className="notice notice-high m-0">
          {error}
        </p>
      )}

      <button type="submit" className="btn btn-primary" disabled={!state.file || busy}>
        {busy ? 'Uploading…' : <Hi>बोल के चेक करो</Hi>}
      </button>
    </form>
  )
}
