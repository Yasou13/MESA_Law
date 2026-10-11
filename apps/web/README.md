# MESA Law - Frontend

This is the frontend application for MESA Law, an intelligent legal case management platform. 

It is built with [Next.js](https://nextjs.org) (App Router), [React](https://react.dev), and uses [Tailwind CSS](https://tailwindcss.com/) alongside [shadcn/ui](https://ui.shadcn.com/) for UI components.

## Getting Started

### Prerequisites

- Node.js >= 18 (20 recommended)
- `pnpm` >= 8

### Installation

1. Install dependencies from the root of the monorepo or within `apps/web`:
```bash
pnpm install
```

2. Run the development server:
```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the application.

## Architecture

### State Management
- **Server State:** Managed by [TanStack React Query](https://tanstack.com/query/latest) (`@tanstack/react-query`). All backend data fetching, caching, and invalidation occurs through Query hooks.
- **Form State:** Managed by [React Hook Form](https://react-hook-form.com/) combined with [Zod](https://zod.dev/) for schema validation.
- **Auth State:** Managed by [NextAuth.js](https://next-auth.js.org/). Session logic handles tenant/firm separation and robust access controls.

### API Layer
- **Orval:** We use [Orval](https://orval.dev/) to automatically generate React Query hooks and Axios HTTP clients directly from the Python backend's OpenAPI specification. 
- Generated files reside in `src/api/` and should **not** be manually edited.
- To regenerate API clients, run:
  ```bash
  pnpm run api:generate
  ```
- **Java API:** Set `NEXT_PUBLIC_MESA_LAW_JAVA_API_BASE_URL` to the Spring Boot API origin to send requests for implemented Java endpoints to it. The shared client maps the Java-supported endpoints and adapts JSON field casing; requests without a matching Java controller keep using `NEXT_PUBLIC_MESA_LAW_API_BASE_URL` (or the same-origin API proxy).

### UI Components & Styling
- **shadcn/ui:** We use shadcn/ui to build composable, accessible components. Components are located in `src/components/ui`.
- **CSS Architecture:** We use Tailwind CSS combined with a custom CSS variables system (`var(--bg-surface)`, etc.) to support a dynamic OKLCH color space for robust light and dark theming.

## Quality Gates & Testing

We enforce high standards for frontend quality:
- **Linting:** `pnpm lint` (ESLint + Prettier + Security plugins)
- **Typechecking:** `pnpm typecheck` (TypeScript strict mode)
- **Unit Tests:** `pnpm test:unit` (Vitest + React Testing Library)
- **E2E Tests:** `pnpm test` (Playwright tests in `e2e/`)

## Environment Variables

Check `.env.example` (or configure your local `.env`) for required variables. Typically, you will need:
- `NEXT_PUBLIC_MESA_LAW_API_BASE_URL`: Optional FastAPI origin. Leave unset for same-origin deployments; do not append `/api/v1`.
- `NEXT_PUBLIC_MESA_LAW_JAVA_API_BASE_URL`: Optional Spring Boot origin for endpoints implemented in `apps/api-java`. Leave unset to keep all requests on the existing API. The Java origin must allow the frontend origin through CORS when the browser calls it directly.
- `NEXTAUTH_SECRET`: Secret for NextAuth session encryption.
- `NEXTAUTH_URL`: Canonical URL of the frontend.
