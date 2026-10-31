import { useEffect } from 'react'

/**
 * Update page title, meta description, robots tag, and canonical link per route.
 */
export function usePageMeta({ title, description, noindex = false, canonical = null }) {
  useEffect(() => {
    const prevTitle = document.title
    if (title) {
      document.title = `${title} | EduSynC`
    }

    let metaDesc = document.querySelector('meta[name="description"]')
    if (!metaDesc) {
      metaDesc = document.createElement('meta')
      metaDesc.name = 'description'
      document.head.appendChild(metaDesc)
    }
    const prevDesc = metaDesc.content
    if (description) {
      metaDesc.content = description
    }

    let metaRobots = document.querySelector('meta[name="robots"]')
    if (noindex) {
      if (!metaRobots) {
        metaRobots = document.createElement('meta')
        metaRobots.name = 'robots'
        document.head.appendChild(metaRobots)
      }
      metaRobots.content = 'noindex, nofollow'
    } else if (metaRobots) {
      metaRobots.remove()
    }

    let linkCanonical = document.querySelector('link[rel="canonical"]')
    const siteUrl = import.meta.env.VITE_SITE_URL || 'https://edusync.vercel.app'
    if (canonical && !noindex) {
      if (!linkCanonical) {
        linkCanonical = document.createElement('link')
        linkCanonical.rel = 'canonical'
        document.head.appendChild(linkCanonical)
      }
      linkCanonical.href = `${siteUrl.replace(/\/+$/, '')}${canonical}`
    } else if (linkCanonical) {
      linkCanonical.remove()
    }

    return () => {
      document.title = prevTitle
      if (metaDesc) metaDesc.content = prevDesc
    }
  }, [title, description, noindex, canonical])
}
