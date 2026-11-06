import { useState } from 'react'
import { api } from '../../services/api'

const PRESET_AVATARS = [
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

  const handleRemovePicture = async () => {
    setIsSubmitting(true)
    setUploadError('')
    try {
      const resp = await api.delete(`/profile/picture?platform=${activePlatform}`)
      if (onUpdated) {
        onUpdated(resp.data)
      }
      setSelectedPreview(null)
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Failed to remove picture.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleToggleUseCommon = async (val) => {
    setUseCommon(val)
    try {
      const resp = await api.put('/profile/picture/settings', { use_common: val })
      if (onUpdated) {
        onUpdated(resp.data)
      }
    } catch {
      // Revert if error
      setUseCommon(!val)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60">
      <div className="bg-surface rounded-lg border border-line shadow-md w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-line flex items-center justify-between bg-surface-2">
          <div>
            <h3 className="m-0 text-base font-bold text-ink">Manage Profile Picture</h3>
            <p className="m-0 text-xs text-muted mt-0.5">Customise your avatar across Web, Android, and iOS.</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded text-muted hover:text-ink hover:bg-surface border-0 cursor-pointer"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {/* Platform Settings Toggle */}
          <div className="rounded border border-line bg-surface-2 p-3 flex items-start gap-3">
            <input
              type="checkbox"
              id="use_common_toggle"
              checked={useCommon}
              onChange={(e) => handleToggleUseCommon(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-line text-brand cursor-pointer"
            />
            <label htmlFor="use_common_toggle" className="text-xs text-ink cursor-pointer">
              <span className="font-semibold block">Use one common picture across all platforms</span>
              <span className="text-muted block text-[11px] mt-0.5">
                When enabled, your common picture is displayed on Web, Android, and iOS. Disable to upload distinct images per device.
              </span>
            </label>
          </div>

          {/* Platform Switcher Tabs */}
          {!useCommon && (
            <div className="flex rounded border border-line p-1 bg-surface-2 gap-1 text-xs">
              {[
                { id: 'web', label: 'Web Application' },
                { id: 'android', label: 'Android Client' },
                { id: 'ios', label: 'iOS Client' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => {
                    setActivePlatform(tab.id)
                    setSelectedPreview(null)
                  }}
                  className={`flex-1 py-1.5 px-2 rounded font-semibold text-center transition-colors cursor-pointer border-0 ${
                    activePlatform === tab.id
                      ? 'bg-brand text-white shadow-xs'
                      : 'text-muted hover:text-ink hover:bg-surface'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          )}

          {/* Active Avatar Preview Frame */}
          <div className="flex flex-col items-center justify-center py-2 space-y-3">
            <div className="relative w-28 h-28 rounded-full border-2 border-brand/40 overflow-hidden bg-surface-2 flex items-center justify-center shadow-xs">
              {currentUrl ? (
                <img
                  src={currentUrl}
                  alt="Profile Preview"
                  className="w-full h-full object-cover"
                />
              ) : (
                <span className="text-3xl font-bold text-brand">U</span>
              )}
            </div>
            <div className="text-center">
              <span className="inline-block text-[11px] font-semibold uppercase px-2 py-0.5 rounded bg-surface-2 text-muted border border-line">
                Platform Target: {useCommon ? 'Common (All Platforms)' : activePlatform.toUpperCase()}
              </span>
            </div>
          </div>

          {/* Error Message */}
          {uploadError && (
            <div className="p-2.5 rounded bg-red-50 border border-red-200 text-xs text-red-700">
              {uploadError}
            </div>
          )}

          {/* Upload Custom Image Dropzone */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-ink">Upload Custom Image</label>
            <div className="border border-dashed border-line rounded p-4 text-center hover:border-brand transition-colors bg-surface-2">
              <input
                type="file"
                id="avatar_upload"
                accept="image/png, image/jpeg, image/webp"
                onChange={handleFileChange}
                className="hidden"
              />
              <label
                htmlFor="avatar_upload"
                className="inline-block px-3 py-1.5 rounded bg-surface border border-line text-xs font-semibold text-ink cursor-pointer hover:bg-surface-2"
              >
                Browse Image File
              </label>
              <p className="m-0 text-[11px] text-muted mt-2">
                Supported formats: PNG, JPG, WebP. Maximum file size: 2MB.
              </p>
            </div>
          </div>

          {/* Preset Educational Badges (Privacy by Design) */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-ink">Or Choose an Educational Badge</label>
            <div className="grid grid-cols-5 gap-2">
              {PRESET_AVATARS.map((preset) => (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => handleSelectPreset(preset.svg)}
                  className="p-1 rounded border border-line hover:border-brand bg-surface flex flex-col items-center justify-center gap-1 cursor-pointer transition-colors"
                  title={preset.label}
                >
                  <img src={preset.svg} alt={preset.label} className="w-10 h-10 rounded-full" />
                  <span className="text-[9px] text-muted truncate w-full text-center">{preset.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-line bg-surface-2 flex items-center justify-between">
          <button
            type="button"
            onClick={handleRemovePicture}
            disabled={isSubmitting}
            className="px-3 py-1.5 rounded border border-line bg-surface text-xs font-semibold text-muted hover:text-red-700 hover:border-red-300 cursor-pointer disabled:opacity-50"
          >
            Reset to Default
          </button>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-3 py-1.5 rounded border border-line bg-surface text-xs font-semibold text-ink hover:bg-surface-2 cursor-pointer disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSavePicture}
              disabled={isSubmitting || !selectedPreview}
              className="px-4 py-1.5 rounded bg-brand text-white text-xs font-semibold shadow-xs hover:bg-brand-deep cursor-pointer disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : 'Save Picture'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

