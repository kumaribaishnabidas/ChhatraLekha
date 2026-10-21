import { describe, expect, it } from 'vitest'

import {
  anomalyLabel,
  formatApaar,
  formatNumber,
  formatPercent,
  maskApaar,
  quotaLabel,
  riskClass,
  severityClass,
  statusClass,
} from '../utils/format'
import { can, canAny, permissionsFor } from '../utils/permissions'

describe('formatting', () => {
  it('formats an APAAR ID in groups of four', () => {
    expect(formatApaar('984210357890')).toBe('9842 1035 7890')
  })

  it('leaves a malformed APAAR ID alone', () => {
    expect(formatApaar('12345')).toBe('12345')
  })

  it('masks everything but the first group', () => {
    expect(maskApaar('984210357890')).toBe('9842 **** ****')
  })

  it('formats numbers for the Indian locale', () => {
    expect(formatNumber(2219)).toBe('2,219')
  })

  it('formats a percentage', () => {
    expect(formatPercent(87.456)).toBe('87.5%')
  })

  it('labels the quota buckets', () => {
    expect(quotaLabel('REGULAR_MERIT')).toBe('Merit')
    expect(quotaLabel('SUPERNUMERARY_TFW')).toBe('TFW')
  })

  it('labels the anomaly families', () => {
    expect(anomalyLabel('EXCESS_APPROVED_INTAKE')).toBe('Over-admission')
  })

  it('maps a severity to a badge class', () => {
    expect(severityClass('CRITICAL')).toContain('crimson')
    expect(severityClass('WARNING')).toContain('mid-blue')
  })

  it('maps a verification status to a badge class', () => {
    expect(statusClass('VERIFIED')).toContain('#0A6B3D')
    expect(statusClass('FLAGGED_ANOMALY')).toContain('crimson')
  })

  it('maps a risk band to a badge class', () => {
    expect(riskClass('CRITICAL')).toContain('crimson')
    expect(riskClass('LOW')).toContain('#0A6B3D')
  })
})

describe('the permission matrix', () => {
  it('lets the directorate see the national picture', () => {
    expect(can('aicte_admin', 'view_national_dashboard')).toBe(true)
    expect(can('aicte_admin', 'review_anomalies')).toBe(true)
  })

  it('does not let the directorate onboard students', () => {
    expect(can('aicte_admin', 'onboard_students')).toBe(false)
  })

  it('lets an institution onboard and import', () => {
    expect(can('institution_admin', 'onboard_students')).toBe(true)
    expect(can('institution_admin', 'import_csv')).toBe(true)
    expect(can('institution_admin', 'view_national_dashboard')).toBe(false)
  })

  it('lets a verifier only verify', () => {
    expect(can('verifier', 'verify_credential')).toBe(true)
    expect(can('verifier', 'export_reports')).toBe(false)
  })

  it('lets a student see only their own record', () => {
    expect(can('student', 'view_own_record')).toBe(true)
    expect(can('student', 'view_student_register')).toBe(false)
  })

  it('grants nothing to an unknown role', () => {
    expect(permissionsFor('wizard')).toEqual([])
  })

  it('matches any of several permissions', () => {
    expect(canAny('verifier', ['onboard_students', 'verify_credential'])).toBe(true)
    expect(canAny('verifier', ['onboard_students', 'export_reports'])).toBe(false)
  })
})
