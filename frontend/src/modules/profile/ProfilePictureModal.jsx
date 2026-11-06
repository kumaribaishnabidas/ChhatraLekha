import { useState } from 'react'
import { api } from '../../services/api'

export const PRESET_AVATARS = [
  {
    id: 'cap',
    label: 'Academic Cap',
    svg: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="%231E3A8A"><rect width="100" height="100" fill="%23DBEAFE"/><path d="M50 20 L85 38 L50 56 L15 38 Z" fill="%231E3A8A"/><path d="M30 48 L30 68 C30 78 70 78 70 68 L70 48" fill="none" stroke="%231E3A8A" stroke-width="6"/><circle cx="50" cy="50" r="10" fill="%23F59E0B"/></svg>',
  },
  {
    id: 'book',
    label: 'Open Book',
    svg: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="%230F766E"><rect width="100" height="100" fill="%23CCFBF1"/><path d="M50 30 C40 22 25 24 20 28 L20 72 C25 68 40 66 50 74 C60 66 75 68 80 72 L80 28 C75 24 60 22 50 30 Z" fill="%230F766E"/><line x1="50" y1="30" x2="50" y2="74" stroke="%23FFFFFF" stroke-width="4"/></svg>',
  },
  {
    id: 'scholar',
    label: 'Scholar Crest',
    svg: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="%23FEF3C7"/><path d="M50 15 L80 30 L80 60 C80 75 50 88 50 88 C50 88 20 75 20 60 L20 30 Z" fill="%23D97706"/><circle cx="50" cy="45" r="14" fill="%23FFFFFF"/><path d="M35 70 C38 60 62 60 65 70" fill="%23FFFFFF"/></svg>',
  },
  {
    id: 'compass',
    label: 'Explorer',
    svg: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="%23F3E8FF"/><circle cx="50" cy="50" r="35" fill="none" stroke="%237E22CE" stroke-width="6"/><polygon points="50,22 58,45 50,78 42,45" fill="%237E22CE"/><polygon points="50,22 58,45 50,45" fill="%23EF4444"/></svg>',
  },
  {
    id: 'shield',
    label: 'Security Shield',
    svg: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="%23E0E7FF"/><path d="M50 18 L82 32 L82 58 C82 74 50 85 50 85 C50 85 18 74 18 58 L18 32 Z" fill="%234338CA"/><path d="M42 50 L48 56 L62 42" fill="none" stroke="%23FFFFFF" stroke-width="6" stroke-linecap="round"/></svg>',
  },
]

export default function ProfilePictureModal({
  isOpen,
  onClose,
  pictures = {},
  onUpdated,
}) {
  const [activePlatform, setActivePlatform] = useState('common')
  const [useCommon, setUseCommon] = useState(pictures.use_common ?? true)
  const [selectedPreview, setSelectedPreview] = useState(null)
  const [uploadError, setUploadError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isOpen) return null

  const getPlatformUrl = (platform) => {
    if (platform === 'common') return pictures.common_url
    if (platform === 'web') return pictures.web_url
    if (platform === 'android') return pictures.android_url
    if (platform === 'ios') return pictures.ios_url
    return null
  }

  const currentUrl = selectedPreview || getPlatformUrl(activePlatform) || pictures.common_url

  const handleFileChange = (e) => {
    setUploadError('')
    const file = e.target.files?.[0]
    if (!file) return

    // Max 2MB validation
    if (file.size > 2 * 1024 * 1024) {
      setUploadError('File size exceeds 2MB limit. Please choose a smaller image.')
      return
    }

    // MIME type check
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
      setUploadError('Only PNG, JPEG, or WebP images are supported.')
      return
    }

    const reader = new FileReader()
    reader.onload = () => {
      setSelectedPreview(reader.result)
    }
    reader.readAsDataURL(file)
  }

  const handleSelectPreset = (svgUrl) => {
    setUploadError('')
    setSelectedPreview(svgUrl)
  }

  const handleSavePicture = async () => {
    if (!selectedPreview) return
    setIsSubmitting(true)
    setUploadError('')
    try {
      const resp = await api.post('/profile/picture', {
        platform: activePlatform,
        image_url: selectedPreview,
      })
      if (onUpdated) {
        onUpdated(resp.data)
      }
      setSelectedPreview(null)
      onClose()
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Failed to update profile picture.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleResetPicture = async () => {
    setIsSubmitting(true)
    setUploadError('')
    try {
      const resp = await api.delete('/profile/picture', {
        params: { platform: activePlatform },
      })
      if (onUpdated) {
        onUpdated(resp.data)
      }
      setSelectedPreview(null)
      onClose()
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Failed to reset picture.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleToggleUseCommon = async (val) => {
    setUseCommon(val)
    try {
      const resp = await api.put('/profile/picture/settings', {
        use_common: val,
      })
      if (onUpdated) {
        onUpdated(resp.data)
      }
    } catch {
      // Revert if request fails
      setUseCommon(!val)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="w-full max-w-lg rounded-lg bg-surface border border-line shadow-md p-6 space-y-6 text-ink">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-line pb-3">
          <div>
            <h2 id="modal-title" className="m-0 text-base font-bold text-ink">
              Profile Picture Management
            </h2>
            <p className="m-0 text-xs text-muted mt-0.5">
              Customize your avatar across Web, Android, and iOS devices.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded text-muted hover:text-ink hover:bg-surface-2 cursor-pointer border-0"
            aria-label="Close modal"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Common Avatar Toggle */}
        <div className="flex items-center justify-between p-3 rounded-lg bg-surface-2 border border-line">
          <div>
            <span className="text-xs font-bold text-ink block">Unified Profile Picture</span>
            <span className="text-[11px] text-muted block">
              Use one common picture across Web, Android, and iOS platforms.
            </span>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={useCommon}
              onChange={(e) => handleToggleUseCommon(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-9 h-5 bg-line peer-focus:outline-hidden rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-line after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-brand" />
          </label>
        </div>

        {/* Platform Tabs */}
        {!useCommon && (
          <div className="flex gap-1.5 border-b border-line pb-2">
            {[
              { id: 'web', label: 'Web Application' },
              { id: 'android', label: 'Android Mobile' },
              { id: 'ios', label: 'iOS Mobile' },
            ].map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => {
                  setActivePlatform(p.id)
                  setSelectedPreview(null)
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition-colors ${
                  activePlatform === p.id
                    ? 'bg-brand text-on-brand shadow-xs'
                    : 'bg-surface text-ink border border-line hover:border-brand'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        )}

        {/* Current Avatar Preview & Dropzone */}
        <div className="flex flex-col sm:flex-row items-center gap-6 p-4 rounded-lg bg-surface-2/40 border border-line">
          <div className="w-24 h-24 rounded-full border-2 border-brand/50 overflow-hidden bg-surface flex items-center justify-center flex-shrink-0 shadow-xs">
            {currentUrl ? (
              <img src={currentUrl} alt="Avatar preview" className="w-full h-full object-cover" />
            ) : (
              <span className="text-2xl font-bold text-brand">U</span>
            )}
          </div>

          <div className="space-y-2 text-center sm:text-left flex-1">
            <p className="m-0 text-xs font-semibold text-ink">Upload Custom Image</p>
            <p className="m-0 text-[11px] text-muted">PNG, JPG, or WebP. Maximum size: 2MB.</p>
            <label className="inline-block px-3 py-1.5 rounded bg-surface border border-line text-xs font-semibold text-ink hover:bg-surface-2 cursor-pointer shadow-xs">
              Choose Image File
              <input type="file" accept="image/png, image/jpeg, image/webp" onChange={handleFileChange} className="hidden" />
            </label>
          </div>
        </div>

        {/* Error message */}
        {uploadError && (
          <div className="p-2.5 rounded bg-danger/10 border border-danger/30 text-danger text-xs font-medium">
            {uploadError}
          </div>
        )}

        {/* Preset Badges */}
        <div className="space-y-2">
          <span className="text-xs font-semibold text-muted block">Or choose an educational badge:</span>
          <div className="flex flex-wrap gap-2.5">
            {PRESET_AVATARS.map((av) => (
              <button
                key={av.id}
                type="button"
                onClick={() => handleSelectPreset(av.svg)}
                className="w-10 h-10 rounded-full border border-line hover:border-brand p-1 cursor-pointer bg-surface transition-transform hover:scale-105 flex items-center justify-center shadow-xs"
                title={av.label}
              >
                <img src={av.svg} alt={av.label} className="w-full h-full rounded-full object-contain" />
              </button>
            ))}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-line pt-4">
          <button
            type="button"
            onClick={handleResetPicture}
            disabled={isSubmitting}
            className="text-xs text-muted hover:text-danger cursor-pointer p-0 bg-transparent border-0"
          >
            Reset to default avatar
          </button>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-3 py-1.5 rounded border border-line bg-surface text-xs font-semibold text-ink hover:bg-surface-2 cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSavePicture}
              disabled={isSubmitting || !selectedPreview}
              className={`px-4 py-1.5 rounded bg-brand text-on-brand text-xs font-bold transition-opacity shadow-xs ${
                !selectedPreview || isSubmitting ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:bg-brand-deep'
              }`}
            >
              {isSubmitting ? 'Saving...' : 'Apply Picture'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
