#!/usr/bin/env node
/** Validate exact key and interpolation parity against English. */
import { readdir, readFile } from 'node:fs/promises'
import { join } from 'node:path'

const root = new URL('../src/i18n/locales/', import.meta.url)
const flatten = (value, prefix = '') => Object.entries(value).flatMap(([key, item]) =>
  item && typeof item === 'object' && !Array.isArray(item)
    ? flatten(item, `${prefix}${key}.`)
    : [[`${prefix}${key}`, String(item)]],
)
const placeholders = (value) => [...value.matchAll(/{{\s*([\w.-]+)\s*}}/g)].map((match) => match[1]).sort()
const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b)

const languages = (await readdir(root, { withFileTypes: true })).filter((item) => item.isDirectory()).map((item) => item.name).sort()
const load = async (language) => JSON.parse(await readFile(new URL(`${language}/common.json`, root), 'utf8'))
const english = Object.fromEntries(flatten(await load('en')))
let failed = false
for (const language of languages.filter((item) => item !== 'en')) {
  const locale = Object.fromEntries(flatten(await load(language)))
  const missing = Object.keys(english).filter((key) => !(key in locale))
  const extra = Object.keys(locale).filter((key) => !(key in english))
  const mismatch = Object.keys(english).filter((key) => key in locale && !equal(placeholders(english[key]), placeholders(locale[key])))
  if (missing.length || extra.length || mismatch.length) {
    failed = true
    console.error(`${language}:`)
    if (missing.length) console.error(`  missing: ${missing.join(', ')}`)
    if (extra.length) console.error(`  extra: ${extra.join(', ')}`)
    if (mismatch.length) console.error(`  placeholder mismatch: ${mismatch.join(', ')}`)
  }
}
if (failed) process.exitCode = 1
else console.log(`i18n check passed: ${languages.length} locales, ${Object.keys(english).length} keys each.`)
