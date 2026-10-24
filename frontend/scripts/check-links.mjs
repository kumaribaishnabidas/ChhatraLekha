import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const rootDir = path.resolve(__dirname, '..')
const publicDir = path.join(rootDir, 'public')
const srcDir = path.join(rootDir, 'src')

console.log('Checking internal links, routes, and assets...')

// 1. Collect all declared routes from App.jsx
const appJsx = fs.readFileSync(path.join(srcDir, 'App.jsx'), 'utf-8')
const routeMatches = [...appJsx.matchAll(/path="([^"]+)"/g)].map((m) => m[1])
const knownRoutes = new Set(routeMatches)
knownRoutes.add('/')

console.log(`Discovered ${knownRoutes.size} configured application routes:`, [...knownRoutes].join(', '))

// 2. Scan JSX files for <Link to="...">, <NavLink to="...">, and <a href="...">
const jsxFiles = []
function collectJsx(dir) {
  for (const item of fs.readdirSync(dir)) {
    const full = path.join(dir, item)
    if (fs.statSync(full).isDirectory()) {
      collectJsx(full)
    } else if (item.endsWith('.jsx') || item.endsWith('.js')) {
      jsxFiles.push(full)
    }
  }
}
collectJsx(srcDir)

const internalLinks = new Set()
const staticAssets = new Set()
const errors = []

for (const file of jsxFiles) {
  const content = fs.readFileSync(file, 'utf-8')
  // Match to="/..." or href="/..."
  const linkMatches = [...content.matchAll(/(?:to|href)=["'](\/[^"']*)["']/g)]
  for (const [, link] of linkMatches) {
    if (link.startsWith('/brand/') || link.startsWith('/favicon') || link.endsWith('.png') || link.endsWith('.svg') || link.endsWith('.ico') || link.endsWith('.txt') || link.endsWith('.xml')) {
      staticAssets.add(link)
    } else {
      internalLinks.add(link.split('#')[0] || '/')
    }
  }
}

// 3. Verify internal links
for (const link of internalLinks) {
  // Allow dynamic parameters like /verify/t/:token or /verify/t/...
  if (link.startsWith('/verify/t/')) continue
  if (!knownRoutes.has(link) && link !== '' && link !== '/') {
    errors.push(`Dead internal link found: "${link}" not matched by any route.`)
  }
}

// 4. Verify static assets exist in public/
for (const asset of staticAssets) {
  const assetPath = path.join(publicDir, asset.replace(/^\//, ''))
  if (!fs.existsSync(assetPath)) {
    errors.push(`Missing static asset: "${asset}" not found at "${assetPath}".`)
  }
}

// 5. Verify sitemap.xml routes match known public routes
const sitemapPath = path.join(publicDir, 'sitemap.xml')
if (fs.existsSync(sitemapPath)) {
  const sitemapContent = fs.readFileSync(sitemapPath, 'utf-8')
  const locMatches = [...sitemapContent.matchAll(/<loc>https:\/\/[^/]+(\/[^<]*)<\/loc>/g)].map(m => m[1] || '/')
  for (const loc of locMatches) {
    if (!knownRoutes.has(loc)) {
      errors.push(`sitemap.xml references unknown route: "${loc}"`)
    }
  }
} else {
  errors.push('public/sitemap.xml is missing')
}

// 6. Verify robots.txt exists
const robotsPath = path.join(publicDir, 'robots.txt')
if (!fs.existsSync(robotsPath)) {
  errors.push('public/robots.txt is missing')
}

if (errors.length > 0) {
  console.error('\nLink and asset check FAILED with errors:')
  for (const err of errors) {
    console.error(` - ${err}`)
  }
  process.exit(1)
}

console.log(`\nLink and asset check PASSED: verified ${internalLinks.size} internal routes and ${staticAssets.size} static assets.`)
