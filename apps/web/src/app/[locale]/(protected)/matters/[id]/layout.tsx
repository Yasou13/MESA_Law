import { MatterWorkspaceShell } from '@/components/layout/MatterWorkspaceShell'

export default async function MatterLayout({ children, params }: {
  children: React.ReactNode
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return <MatterWorkspaceShell matterId={id}>{children}</MatterWorkspaceShell>
}
