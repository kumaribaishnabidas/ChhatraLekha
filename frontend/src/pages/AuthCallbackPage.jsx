/**
 * The landing route of the Google sign-in.
 *
 * The backend returns the browser here with the tokens in the URL fragment:
 * `#access_token=...&refresh_token=...&role=...`. The fragment is never sent
 * to a server, so the tokens do not end up in a log or in the referrer.
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Spinner } from '../components/common'
import { tokenStore } from '../services/api'

export default function AuthCallbackPage() {
  const navigate = useNavigate()
  const [message, setMessage] = useState('Completing the sign-in...')

  useEffect(() => {
    const fragment = window.location.hash.startsWith('#')
      ? window.location.hash.slice(1)
      : window.location.hash
    const params = new URLSearchParams(fragment)
    const error = params.get('error')
    const accessToken = params.get('access_token')

    if (error) {
      setMessage(error)
      window.setTimeout(() => navigate('/login', { replace: true }), 4000)
      return
    }

    if (!accessToken) {
      setMessage('The sign-in did not return a token. Returning to the sign-in page...')
      window.setTimeout(() => navigate('/login', { replace: true }), 2000)
      return
    }

    tokenStore.set({
      access_token: accessToken,
      refresh_token: params.get('refresh_token') || '',
      role: params.get('role') || '',
    })
    // Clear the fragment so the tokens are not left in the address bar.
    window.history.replaceState({}, '', window.location.pathname)
    navigate('/dashboard', { replace: true })
  }, [navigate])

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="card max-w-md p-8 text-center">
        <h1 className="text-lg">Google sign-in</h1>
        <p className="mt-2 text-sm text-muted">{message}</p>
        <div className="mt-4 flex justify-center">
          <Spinner label="" />
        </div>
      </div>
    </div>
  )
}
