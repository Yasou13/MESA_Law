import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Timeline } from './Timeline'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { NextIntlClientProvider } from 'next-intl'
import messages from '../../../../messages/en.json'

const queryClient = new QueryClient()

const mockEvents = [
  {
    id: 'event_1',
    date: '2023-01-15T10:00:00Z',
    title: 'Initial Complaint Filed',
    description: 'The plaintiff filed the initial complaint in federal court.',
    source: 'Complaint.pdf',
    confidence: 'high',
  },
  {
    id: 'event_2',
    date: '2023-02-20T14:30:00Z',
    title: 'Defendant Answer',
    description: 'Defendant filed their answer denying all claims.',
    source: 'Answer.pdf',
    confidence: 'medium',
  }
]

vi.mock('@/api/endpoints/default/default', () => ({
  useListTimelineEvents: vi.fn(() => ({
    data: mockEvents,
    isLoading: false
  }))
}))

describe('Timeline component', () => {
  it('renders timeline events correctly', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <NextIntlClientProvider locale="en" messages={messages}>
          <Timeline matterId="1" />
        </NextIntlClientProvider>
      </QueryClientProvider>
    )
    
    // Check if both titles are rendered
    expect(screen.getByText('Initial Complaint Filed')).toBeInTheDocument()
    expect(screen.getByText('Defendant Answer')).toBeInTheDocument()
  })
})
