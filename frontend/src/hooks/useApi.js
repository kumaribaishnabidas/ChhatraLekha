/** A tiny data-fetching hook with loading and error state. */
import { useCallback, useEffect, useState } from 'react'

import { errorMessage } from '../services/api'

export function useApi(fetcher, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reloadIndex, setReloadIndex] = useState(0)

  const reload = useCallback(() => setReloadIndex((value) => value + 1), [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')
    Promise.resolve()
      .then(fetcher)
      .then((result) => {
        if (!cancelled) setData(result)
      })
      .catch((caught) => {
        if (!cancelled) setError(errorMessage(caught))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, reloadIndex])

  return { data, loading, error, reload, setData }
}
