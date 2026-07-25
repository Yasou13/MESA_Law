# Work Order 010 (WO-010) Handoff

## Objective
Implement Mock Intelligence UX for the Matter Detail page. This includes building mock UI components for Timeline, Claims/Evidence, Q&A Shell, and Research Shell, with simulated delays, error states, and confidence badging.

## Accomplishments
- **UI Components:**
  - Built `Timeline.tsx` with chronological event visualization and random "degraded source" error simulation.
  - Built `ClaimsEvidence.tsx` with confidence and support badges, including "no-evidence" handling.
  - Built `QAShell.tsx` with simulated conversation, citation references, and timeout error states.
  - Built `ResearchShell.tsx` to query mock legislation/case law with percentage match scores.
- **Integration:**
  - Refactored `apps/web/src/app/matters/[id]/page.tsx` to include a Tabbed navigation layout.
  - Moved document upload to the "Overview" tab.
  - Wired in the new intelligence components securely without breaking the canonical document upload flow.
- **Testing & Verification:**
  - Created `apps/web/e2e/mock-intelligence.spec.ts` to test tab switching, AI responses, and research functionality.
  - Fixed exact matches for "Search" buttons and heading assertions in `canonical.spec.ts`.
  - Both E2E tests pass 100% locally.

## Next Suggested Work Order
- **WO-011** (Review, approval ve solo mode)

No MESA Core modifications were required. All mock endpoints run locally via React state for now.
