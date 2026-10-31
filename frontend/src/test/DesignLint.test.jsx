import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { sanitizeCopyPayload } from '../components/common/CopyButton'

function getAllFiles(dir, extensions = ['.jsx', '.js', '.css', '.json']) {
  let results = []
  const list = fs.readdirSync(dir)
  for (const file of list) {
    const fullPath = path.join(dir, file)
    const stat = fs.statSync(fullPath)
    if (stat && stat.isDirectory()) {
      results = results.concat(getAllFiles(fullPath, extensions))
    } else {
      if (extensions.some((ext) => file.endsWith(ext))) {
        results.push(fullPath)
      }
    }
  }
  return results
}

describe('Stage 6: Design System Lint', () => {
  const srcDir = path.resolve(__dirname, '..')

  it('contains zero harsh gradients (bg-gradient / gradient-)', () => {
    const codeFiles = getAllFiles(srcDir, ['.jsx', '.js', '.css'])
    const violations = []
    for (const file of codeFiles) {
      if (file.includes('DesignLint.test')) continue
      const content = fs.readFileSync(file, 'utf-8')
      const lines = content.split('\n')
      lines.forEach((line, idx) => {
        if (/bg-gradient|gradient-to-/.test(line)) {
          violations.push(`${path.relative(srcDir, file)}:${idx + 1}: ${line.trim()}`)
        }
      })
    }
    expect(violations).toEqual([])
  })

  it('contains zero backdrop-blur classes', () => {
    const codeFiles = getAllFiles(srcDir, ['.jsx', '.js', '.css'])
    const violations = []
    for (const file of codeFiles) {
      if (file.includes('DesignLint.test')) continue
      const content = fs.readFileSync(file, 'utf-8')
      const lines = content.split('\n')
      lines.forEach((line, idx) => {
        if (/backdrop-blur/.test(line)) {
          violations.push(`${path.relative(srcDir, file)}:${idx + 1}: ${line.trim()}`)
        }
      })
    }
    expect(violations).toEqual([])
  })

  it('contains zero large soft corner radius tokens (rounded-xl, rounded-2xl, rounded-3xl)', () => {
    const codeFiles = getAllFiles(srcDir, ['.jsx', '.js', '.css'])
    const violations = []
    for (const file of codeFiles) {
      if (file.includes('DesignLint.test')) continue
      const content = fs.readFileSync(file, 'utf-8')
      const lines = content.split('\n')
      lines.forEach((line, idx) => {
        if (/rounded-(?:xl|2xl|3xl)/.test(line)) {
          violations.push(`${path.relative(srcDir, file)}:${idx + 1}: ${line.trim()}`)
        }
      })
    }
    expect(violations).toEqual([])
  })

  it('contains zero heavy drop shadows (shadow-lg, shadow-xl, shadow-2xl)', () => {
    const codeFiles = getAllFiles(srcDir, ['.jsx', '.js', '.css'])
    const violations = []
    for (const file of codeFiles) {
      if (file.includes('DesignLint.test')) continue
      const content = fs.readFileSync(file, 'utf-8')
      const lines = content.split('\n')
      lines.forEach((line, idx) => {
        if (/shadow-(?:lg|xl|2xl)/.test(line)) {
          violations.push(`${path.relative(srcDir, file)}:${idx + 1}: ${line.trim()}`)
        }
      })
    }
    expect(violations).toEqual([])
  })

  it('contains zero emojis in source code and locale files', () => {
    const allFiles = getAllFiles(srcDir, ['.jsx', '.js', '.css', '.json'])
    const emojiRegex = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u
    const violations = []
    for (const file of allFiles) {
      if (file.includes('DesignLint.test')) continue
      const content = fs.readFileSync(file, 'utf-8')
      const lines = content.split('\n')
      lines.forEach((line, idx) => {
        if (emojiRegex.test(line)) {
          violations.push(`${path.relative(srcDir, file)}:${idx + 1}: ${line.trim()}`)
        }
      })
    }
    expect(violations).toEqual([])
  })

  it('contains zero em dashes (U+2014) or en dashes (U+2013) in user text or locales', () => {
    const allFiles = getAllFiles(srcDir, ['.jsx', '.js', '.css', '.json'])
    const dashRegex = /[\u2013\u2014]/
    const violations = []
    for (const file of allFiles) {
      if (file.includes('DesignLint.test')) continue
      const content = fs.readFileSync(file, 'utf-8')
      const lines = content.split('\n')
      lines.forEach((line, idx) => {
        if (dashRegex.test(line)) {
          violations.push(`${path.relative(srcDir, file)}:${idx + 1}: ${line.trim()}`)
        }
      })
    }
    expect(violations).toEqual([])
  })

  it('sanitizeCopyPayload masks raw 12-digit APAAR IDs and leaves tokens intact', () => {
    expect(sanitizeCopyPayload('123456789012')).toBe('****-****-9012')
    expect(sanitizeCopyPayload('1234-5678-9012')).toBe('****-****-9012')
    expect(sanitizeCopyPayload('https://chhatralekha.vercel.app/verify/t/abc123token')).toBe(
      'https://chhatralekha.vercel.app/verify/t/abc123token',
    )
    expect(sanitizeCopyPayload('9876')).toBe('9876')
  })
})
