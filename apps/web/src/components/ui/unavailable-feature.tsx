import { Ban } from 'lucide-react'
import type { ReactNode } from 'react'

import { Panel, PanelBody } from '@/components/ui/panel'

export function UnavailableFeature({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <Panel className="border-warning/30">
      <PanelBody className="flex flex-col items-start gap-4 py-8 sm:flex-row">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-warning-soft text-warning"><Ban className="size-5" /></span>
        <div className="max-w-2xl"><h1 className="text-xl font-semibold">{title}</h1><p className="mt-2 text-sm leading-6 text-foreground-secondary">{description}</p>{action && <div className="mt-5">{action}</div>}</div>
      </PanelBody>
    </Panel>
  )
}
