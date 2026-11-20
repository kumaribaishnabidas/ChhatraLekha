'use strict'

const PRODUCTION_HOST = 'chhatralekha.vercel.app'
const DEV_HOSTS = new Set(['localhost', '127.0.0.1'])

function parsePortalUrl(raw) {
  let url
  try {
    url = new URL(raw)
  } catch {
    throw new Error('The portal URL is invalid.')
  }

  const isProduction = url.protocol === 'https:' && url.hostname === PRODUCTION_HOST
  const isLocalDev =
    url.protocol === 'http:' && DEV_HOSTS.has(url.hostname) && url.port === '5173'

  if (!isProduction && !isLocalDev) {
    throw new Error('Only the official HTTPS portal or the local Vite development server is allowed.')
  }

  if (url.username || url.password) {
    throw new Error('Portal URLs must not contain credentials.')
  }

  return url
}

function isInternalPortalUrl(raw, baseUrl) {
  try {
    const candidate = new URL(raw, baseUrl)
    const base = parsePortalUrl(baseUrl)
    return candidate.origin === base.origin
  } catch {
    return false
  }
}

module.exports = { parsePortalUrl, isInternalPortalUrl, PRODUCTION_HOST }
