import { Pause, Play } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { Flag } from '../../api/types'
import { SEVERITY_LABEL } from '../../lib/constants'
import { formatClock } from '../../lib/format'
import { usePlayerStore } from '../../stores/player'
import { Hi, Wave } from '../ui'

const AUDIO_EXTENSIONS = /\.(mp3|wav|m4a)$/i

export function VideoPlayer({
  src,
  duration,
  flags,
}: {
  src: string
  duration: number
  flags: Flag[]
}) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [playing, setPlaying] = useState(false)
  const currentTime = usePlayerStore((state) => state.currentTime)
  const seekRequest = usePlayerStore((state) => state.seekRequest)
  const setCurrentTime = usePlayerStore((state) => state.setCurrentTime)
  const seek = usePlayerStore((state) => state.seek)
  const audioOnly = AUDIO_EXTENSIONS.test(src)

  useEffect(() => {
    if (seekRequest && videoRef.current) videoRef.current.currentTime = seekRequest.time
  }, [seekRequest])

  const liveFlag = flags.find(
    (flag) =>
      flag.family !== 'missing_disclosure' &&
      currentTime >= flag.start_sec &&
      currentTime < flag.end_sec,
  )

  function togglePlay() {
    const video = videoRef.current
    if (!video) return
    if (video.paused) void video.play()
    else video.pause()
  }

  return (
    <div className="player">
      <div className={`relative ${audioOnly ? 'player-audio-only' : ''}`}>
        <video
          ref={videoRef}
          src={src}
          playsInline
          preload="metadata"
          onClick={togglePlay}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
        />
        {audioOnly && <Wave bars={12} live={playing} />}
        {liveFlag && (
          <div className="absolute inset-x-3 bottom-3" aria-live="polite">
            <div className={`notice notice-${liveFlag.severity === 'low' ? 'neutral' : liveFlag.severity}`}>
              <strong>
                <Hi>{SEVERITY_LABEL[liveFlag.severity].hindi}</Hi> · {liveFlag.title}
              </strong>
            </div>
          </div>
        )}
      </div>
      <div className="flex items-center gap-3 px-3 py-2">
        <button
          type="button"
          className="btn btn-icon btn-on-player"
          onClick={togglePlay}
          aria-label={playing ? 'Pause' : 'Play'}
        >
          {playing ? <Pause size={18} /> : <Play size={18} />}
        </button>
        <div className="scrubber flex-1">
          <input
            type="range"
            min={0}
            max={duration || 1}
            step={0.1}
            value={currentTime}
            aria-label="Seek"
            onChange={(event) => seek(Number(event.target.value))}
          />
          {flags.map((flag) => (
            <button
              key={flag.id}
              type="button"
              className="scrubber-marker"
              data-severity={flag.severity}
              style={{ left: `${(flag.start_sec / (duration || 1)) * 100}%` }}
              aria-label={`Jump to ${flag.title} at ${formatClock(flag.start_sec)}`}
              title={flag.title}
              onClick={() => seek(flag.start_sec)}
            />
          ))}
        </div>
        <span className="mono-time">
          {formatClock(currentTime)} / {formatClock(duration)}
        </span>
      </div>
    </div>
  )
}
