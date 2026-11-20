'use strict'

const test = require('node:test')
const assert = require('node:assert/strict')
const { parsePortalUrl, isInternalPortalUrl } = require('./url-policy.cjs')

test('accepts the production portal over HTTPS', () => {
  assert.equal(parsePortalUrl('https://chhatralekha.vercel.app/').hostname, 'chhatralekha.vercel.app')
})

test('accepts only local Vite HTTP development URLs', () => {
  assert.equal(parsePortalUrl('http://localhost:5173').port, '5173')
  assert.equal(parsePortalUrl('http://127.0.0.1:5173').hostname, '127.0.0.1')
})

test('rejects non-HTTPS production and unrelated hosts', () => {
  assert.throws(() => parsePortalUrl('http://chhatralekha.vercel.app'), /official HTTPS portal/)
  assert.throws(() => parsePortalUrl('https://example.com'), /official HTTPS portal/)
  assert.throws(() => parsePortalUrl('http://localhost:8000'), /official HTTPS portal/)
})

test('rejects credential-bearing portal URLs', () => {
  assert.throws(() => parsePortalUrl('https://user:pass@chhatralekha.vercel.app'), /credentials/)
})

test('keeps internal navigation on the portal origin', () => {
  const base = 'https://chhatralekha.vercel.app/'
  assert.equal(isInternalPortalUrl('/students', base), true)
  assert.equal(isInternalPortalUrl('https://chhatralekha.vercel.app/login', base), true)
  assert.equal(isInternalPortalUrl('https://attacker.example/', base), false)
  assert.equal(isInternalPortalUrl('javascript:alert(1)', base), false)
})
