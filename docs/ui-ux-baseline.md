# MESA Law UI/UX Baseline — 2026-08-02

## Environment and gates

The baseline was recorded from commit `0736c481` on the existing
`codex/mesa-v4-mvp` branch. The worktree was clean before capture.

| Check | Exact command | Result |
| --- | --- | --- |
| Node | `node --version` | PASS — `v24.14.0` |
| pnpm | `pnpm --version` | PASS — `11.17.0` |
| Local Python | `python3 --version` | NOTE — `3.10.12`; CI remains the Python 3.13 proof environment |
| Frontend lint | `pnpm --dir apps/web run lint` | PASS |
| Frontend typecheck | `pnpm --dir apps/web run typecheck` | PASS |
| Frontend unit | `pnpm --dir apps/web run test:unit` | PASS — 2 files, 5 tests |
| Frontend production build | `pnpm --dir apps/web run build` | PASS — Next.js 16.2.11, webpack production build |
| Existing Law-side Playwright | `pnpm --dir apps/web run test` | PASS — 1/1 after allowing the test server to bind to localhost:3000 |

The first sandboxed Playwright attempt failed closed before collection with
`listen EPERM 0.0.0.0:3000`. The approved localhost rerun passed. The failed
attempt is not counted as a passing test.

## Capture inventory

Thirty-two synthetic, secret-free before screenshots were captured for the
eight required routes at 1440x900, 1280x800, 1024x768 and 768x1024. They are
kept outside Git under `artifacts/ui-audit/before/<viewport>/<screen>.png`.
The E2E source was restored after capture.

Screens: dashboard, matter list, matter detail, documents, document viewer,
review center, Ask MESA and operations.

## Current visual state

- The cream background and blue text dominate every surface. The visual tone
  is closer to a themed template than an information-dense legal workspace.
- `glass-card`, backdrop blur, large radii, shadows, gradients and scale hover
  treatments conflict with the requested restrained legal direction.
- Raw semantic colours and legacy `anthracite`/`lila` tokens coexist with
  direct Tailwind zinc, red, amber, orange, emerald, blue and purple classes.
- A partial `.dark` token set exists, but no theme provider or user control
  applies and verifies it.
- Typography is not wired to IBM Plex Sans or Source Serif 4. Legal excerpts,
  navigation, tables and headings do not have intentional role separation.
- The sidebar mixes global product navigation, administration, notifications,
  language, profile and sign-out in a single long column. A contextual topbar
  is missing.

## Components worth preserving

- The Base UI/shadcn primitives, CVA button foundation and Lucide icon set.
- The single Axios transport, generated Orval hooks and TanStack Query cache.
- Dialog, form, select, table and tooltip accessibility foundations.
- Existing strict TypeScript settings and the fail-closed E2E stub approach.
- The MESA mark chosen by the product owner.

## Components to redesign or consolidate

- Protected layout and Sidebar become AppShell, responsive Sidebar and Topbar.
- Repeated page headings, panels, tables, filters, loading blocks and empty
  states become shared PageHeader, InformationPanel, DataTable, FilterBar and
  async-state components.
- Status badges move from saturated white-on-colour pills to semantic soft
  surfaces with text and icons.
- The iframe document view becomes a lazy, source-aware document workspace.
- Global and matter review pages converge on one source-aware Review Center.
- Matter tabs move from local component state to persistent URL routes.

## Page-level UX findings

- Dashboard uses four equal KPI cards and does not prioritise failed work,
  pending review or degraded capabilities strongly enough.
- Matter list uses oversized promotional cards rather than a compact legal
  workspace index.
- Matter detail embeds five stateful tabs while separate nested routes already
  exist, creating two competing information architectures.
- Matter header fabricates `Not assigned`/`Not specified` values instead of
  distinguishing absent canonical data.
- Document viewer is mostly an iframe and cannot reliably select revision,
  page, span or evidence highlight.
- Ask MESA and document Q&A use informal chat bubbles and omit retrieval and
  trace context.
- Review Center cannot show source revision/page/span because the current list
  contract exposes no source context.
- Operations exposes useful data but presents it as a generic flat table and
  does not separate user-safe messages from technical details.
- User-facing copy is a mixture of English and Turkish despite next-intl being
  present.

## Responsive and accessibility findings

- At tablet widths the full 256px sidebar remains visible; dense workspace
  content loses too much width instead of using an icon rail or drawer.
- Navigation drawer behaviour lacks a verified focus trap and Escape path.
- Several icon-only controls rely on `title` rather than an accessible label.
- Spinners replace layouts instead of preserving them with skeletons.
- Colour is often the only status signal. Some muted cream/blue combinations
  have weak visual distinction.
- Ambient pulse, bounce and scale motion does not consistently respect
  `prefers-reduced-motion`.
- Repeated hard-coded headings make heading order and bilingual coverage hard
  to verify globally.

## Implementation order

1. Semantic light/dark tokens, fonts and common primitives.
2. AppShell, responsive navigation, topbar and URL-based matter workspace.
3. Additive source-context read models and regenerated Orval client.
4. Document Viewer, Review Center and Ask MESA.
5. Dashboard, lists, operations, settings and remaining routes.
6. Turkish-default/English-complete copy, async states and responsive polish.
7. Accessibility, visual regression, performance and final evidence capture.
