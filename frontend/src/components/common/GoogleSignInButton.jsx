/**
 * The Google sign-in button.
 *
 * The flow is a redirect, not a popup: the browser is sent to the backend's
 * `/api/auth/google`, which redirects to Google's consent screen, which comes
 * back to the backend's callback, which returns the browser here with the
 * tokens in the URL *fragment*. The fragment is never sent to a server and
 * never lands in a log.
 */
export default function GoogleSignInButton({ apiBase = '/api', disabled = false }) {
  const handleClick = () => {
    if (disabled) return
    window.location.assign(`${apiBase}/auth/google`)
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      className="btn w-full border border-line bg-surface text-ink hover:bg-surface-2"
      style={{ boxShadow: '0 1px 2px rgba(20,36,107,.06)' }}
    >
      <GoogleMark />
      <span className="ml-2 font-semibold">Sign in with Google</span>
    </button>
  )
}

function GoogleMark() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true" focusable="false">
      <path
        fill="#EA4335"
        d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
      />
      <path
        fill="#4285F4"
        d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
      />
      <path
        fill="#FBBC05"
        d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"
      />
      <path
        fill="#34A853"
        d="M24 48c6.48 0 11.93-2.13 15.9-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.17 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
      />
    </svg>
  )
}
