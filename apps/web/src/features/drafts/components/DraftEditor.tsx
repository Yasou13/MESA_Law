'use client'

import React from 'react'
import { DraftStudioShell } from './DraftStudioShell'

export default function DraftEditor({ matterId = "default" }: { matterId?: string }) {
    return <DraftStudioShell matterId={matterId} />
}
