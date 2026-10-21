import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ImpactPage from '../pages/ImpactPage'
import { AuthProvider } from '../hooks/useAuth'
import { api } from '../services/api'

const STUDENTS = [
  {
    record_id: 'rec-1',
    apaar_id: '984210357890',
    student_name: 'Rahul Kumar',
    institution_id: 'INST-T1',
    program_id: 'BTECH_CSE',
    academic_year: '2024-25',
    enrollment_date: '2024-07-01',
    admission_quota: 'REGULAR_MERIT',
    nationality: 'Indian',
    student_institute_roll_no: 'CSE-0001',
    contact_email: 'rahul@example.in',
    contact_phone: '+91 90000 00000',
  },
]

const PREVIEW = {
  preview: true,
  student_record_id: 'rec-1',
  current_version: 1,
  changed_fields: [{ field: 'academic_year', before: '2024-25', after: '2025-26' }],
  findings: [
    {
      rule_id: 'CIA-C',
      title: 'The enrolment has to be counted in both academic years',
      explanation: 'The enrolment moves from 2024-25 to 2025-26.',
      affected_refs: ['rec-1'],
      severity: 'MEDIUM',
      certainty: 'confirmed',
      suggested_action: 'Recalculate the intake of both academic years.',
      human_review_required: true,
      institution_id: 'INST-T1',
      rule_data: {},
    },
  ],
  checklist: [
    {
      rule_id: 'CIA-C',
      title: 'The enrolment has to be counted in both academic years',
      explanation: 'The enrolment moves from 2024-25 to 2025-26.',
      suggested_action: 'Recalculate the intake of both academic years.',
      severity: 'MEDIUM',
      certainty: 'confirmed',
      institution_id: 'INST-T1',
      affected_refs: ['rec-1'],
    },
  ],
  highest_severity: 'MEDIUM',
  requires_review: true,
  policy: { policy_id: 'aph-2024-01', version: '2024-01', source: 'collection' },
  notice: 'Preview only: nothing has been saved.',
}

function renderPage() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <ImpactPage />
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('ImpactPage', () => {
  beforeEach(() => {
    api.get = vi.fn((url) => {
      if (url === '/students') return Promise.resolve({ data: STUDENTS })
      if (url.startsWith('/review-tasks')) return Promise.resolve({ data: [] })
      if (url.startsWith('/students/')) return Promise.resolve({ data: [] })
      return Promise.resolve({ data: [] })
    })
    api.post = vi.fn(() => Promise.resolve({ data: PREVIEW }))
    api.patch = vi.fn(() => Promise.resolve({ data: {} }))
  })

  it('renders the three steps of the workflow', async () => {
    renderPage()
    expect(screen.getByText('Change Impact')).toBeInTheDocument()
    expect(screen.getByText('1. Choose a student')).toBeInTheDocument()
    expect(screen.getByText('2. Propose a correction')).toBeInTheDocument()
    expect(screen.getByText('Review checklist')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Rahul Kumar')).toBeInTheDocument())
  })

  it('masks the APAAR ID in the student list', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText('Rahul Kumar')).toBeInTheDocument())
    expect(screen.queryByText('984210357890')).not.toBeInTheDocument()
    expect(screen.getByText('9842 **** ****')).toBeInTheDocument()
  })

  it('shows the before and the after value of a changed field', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => expect(screen.getByText('Rahul Kumar')).toBeInTheDocument())
    await user.click(screen.getByText('Rahul Kumar'))

    const field = await screen.findByLabelText('New Academic year')
    expect(screen.getByText('2024-25')).toBeInTheDocument()
    expect(field).toHaveValue('')
    await user.type(field, '2025-26')
    expect(field).toHaveValue('2025-26')
  })

  it('shows the preview banner and the findings', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => expect(screen.getByText('Rahul Kumar')).toBeInTheDocument())
    await user.click(screen.getByText('Rahul Kumar'))
    const field = await screen.findByLabelText('New Academic year')
    await user.type(field, '2025-26')
    await user.click(screen.getByRole('button', { name: /preview the impact/i }))

    await waitFor(() =>
      expect(screen.getByText(/preview only: nothing has been saved/i)).toBeInTheDocument(),
    )
    expect(
      screen.getByText('The enrolment has to be counted in both academic years'),
    ).toBeInTheDocument()
    expect(screen.getByText('CIA-C')).toBeInTheDocument()
    expect(screen.getByText('confirmed')).toBeInTheDocument()
  })

  it('shows an empty state when there is no student', async () => {
    api.get = vi.fn((url) => {
      if (url === '/students') return Promise.resolve({ data: [] })
      return Promise.resolve({ data: [] })
    })
    renderPage()
    await waitFor(() => expect(screen.getByText('No student found')).toBeInTheDocument())
  })

  it('shows an error state when the preview fails', async () => {
    api.post = vi.fn(() =>
      Promise.reject({ response: { data: { detail: 'The preview failed.' } } }),
    )
    const user = userEvent.setup()
    renderPage()
    await waitFor(() => expect(screen.getByText('Rahul Kumar')).toBeInTheDocument())
    await user.click(screen.getByText('Rahul Kumar'))
    const field = await screen.findByLabelText('New Academic year')
    await user.type(field, '2025-26')
    await user.click(screen.getByRole('button', { name: /preview the impact/i }))

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
    expect(screen.getByRole('alert')).toHaveTextContent('The preview failed.')
  })
})
