import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import AiAssistantDrawer from '../components/ai/AiAssistantDrawer'
import '../i18n'
import { api } from '../services/api'

// jsdom does not implement scrollIntoView, which the drawer calls on updates.
if (typeof Element !== 'undefined' && !Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {}
}

const guidanceReply = {
  reply: 'Use the language selector at the top of the portal to switch languages.',
  source: 'ChhatraLekha knowledge base',
  actions: [],
  grounded: false,
  intent: 'help',
  confidence: 0.7,
  data: null,
  citations: [
    {
      label: 'language_and_voice',
      collection: 'ChhatraLekha knowledge base',
      scope: 'kb:language_and_voice:en',
    },
  ],
  followups: [],
  retrieval: {
    provider: 'tfidf-local',
    chunks: [
      {
        doc_id: 'kb:language_and_voice:en',
        section: 'language_and_voice',
        text: 'The language selector supports thirteen Indian languages.',
        score: 0.9,
        source: 'ChhatraLekha knowledge base',
      },
    ],
  },
  generation: { provider: 'deterministic', used: false, failover_reason: '' },
}

function renderDrawer(onClose = vi.fn()) {
  return render(
    <MemoryRouter>
      <AiAssistantDrawer isOpen onClose={onClose} />
    </MemoryRouter>
  )
}

describe('AI assistant RAG metadata display', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(api, 'get').mockResolvedValue({
      data: { prompts: ['How do I change my language?'] },
    })
  })

  it('renders citations and the RAG pipeline badge from the chat response', async () => {
    vi.spyOn(api, 'post').mockResolvedValue({ data: guidanceReply })
    const user = userEvent.setup()
    renderDrawer()

    await user.type(
      screen.getByPlaceholderText(/Ask about timetable/),
      'How do I change my language?'
    )
    await user.click(screen.getByLabelText('Send message'))

    await waitFor(() =>
      expect(
        screen.getByText(/Use the language selector at the top/)
      ).toBeInTheDocument()
    )
    expect(screen.getByText(/Sources \(1\)/)).toBeInTheDocument()
    const badge = screen.getByText(/RAG · tfidf-local/)
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveAttribute(
      'title',
      'Local retrieval with a faithfulness-constrained generator'
    )
  })

  it('exposes a provider failover reason as a tooltip', async () => {
    vi.spyOn(api, 'post').mockResolvedValue({
      data: {
        ...guidanceReply,
        generation: {
          provider: 'deterministic',
          used: false,
          failover_reason: 'provider_error:TimeoutError',
        },
      },
    })
    const user = userEvent.setup()
    renderDrawer()

    await user.type(
      screen.getByPlaceholderText(/Ask about timetable/),
      'How do I change my language?'
    )
    await user.click(screen.getByLabelText('Send message'))

    await waitFor(() =>
      expect(screen.getByText(/RAG · tfidf-local/)).toHaveAttribute(
        'title',
        'provider_error:TimeoutError'
      )
    )
  })

  it('does not show the badge when the response carries no RAG metadata', async () => {
    vi.spyOn(api, 'post').mockResolvedValue({
      data: {
        ...guidanceReply,
        retrieval: null,
        generation: null,
      },
    })
    const user = userEvent.setup()
    renderDrawer()

    await user.type(
      screen.getByPlaceholderText(/Ask about timetable/),
      'How do I change my language?'
    )
    await user.click(screen.getByLabelText('Send message'))

    await waitFor(() =>
      expect(
        screen.getByText(/Use the language selector at the top/)
      ).toBeInTheDocument()
    )
    expect(screen.queryByText(/RAG ·/)).not.toBeInTheDocument()
  })
})
