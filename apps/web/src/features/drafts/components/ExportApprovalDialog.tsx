'use client'

import React, { useState } from 'react'
import { CheckCircle2, FileUp, Send, Check, AlertCircle, Building2, Eye } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'


export function ExportApprovalDialog({ 
  trigger,
  draftTitle = "Motion for Summary Judgment"
}: { 
  trigger?: React.ReactNode,
  draftTitle?: string 
}) {
  const [open, setOpen] = useState(false)
  const [step, setStep] = useState<1 | 2>(1)
  const [isLoading, setIsLoading] = useState(false)

  const handleApprove = () => {
    setIsLoading(true)
    setTimeout(() => {
      setIsLoading(false)
      setStep(2)
    }, 1500)
  }

  const handleClose = () => {
    setOpen(false)
    setTimeout(() => setStep(1), 300) // reset after animation
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 h-9 px-4 py-2 gap-2 bg-[var(--color-lila-600)] text-white hover:bg-[var(--color-lila-500)]">
        <Send className="w-4 h-4" /> Send for Approval
      </DialogTrigger>
      <DialogContent className="sm:max-w-md bg-[var(--bg-surface)] border-[var(--border-surface)]">
        {step === 1 ? (
          <>
            <DialogHeader>
              <DialogTitle className="text-[var(--foreground)]">External-Use Approval</DialogTitle>
              <DialogDescription className="text-[var(--color-anthracite-400)]">
                Prepare <strong>{draftTitle}</strong> for external sharing or filing.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-6 py-4">
              <div className="bg-[var(--color-anthracite-900)] p-4 rounded-xl border border-[var(--color-semantic-warning)]/20">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-[var(--color-semantic-warning)] shrink-0 mt-0.5" />
                  <div className="text-sm">
                    <h4 className="font-semibold text-[var(--foreground)]">Final Verification Required</h4>
                    <p className="text-[var(--color-anthracite-400)] mt-1">
                      By approving this document, you confirm that it has been cite-checked and reviewed by an authorized attorney.
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <label htmlFor="recipient" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Primary Recipient / Court</label>
                  <Input 
                    id="recipient" 
                    placeholder="e.g., U.S. District Court, Opposing Counsel" 
                    className="bg-[var(--background)] border-[var(--border-surface)]"
                  />
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Firm Branding</label>
                  <div className="flex items-center gap-4 p-3 border border-[var(--border-surface)] rounded-xl bg-[var(--bg-surface-hover)]">
                    <Building2 className="w-6 h-6 text-[var(--color-lila-500)]" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-[var(--foreground)]">Apply Standard Firm Letterhead</p>
                      <p className="text-xs text-[var(--color-anthracite-500)]">Includes logo, footer, and partner signatures.</p>
                    </div>
                    <Button variant="outline" size="sm" className="h-8">Preview</Button>
                  </div>
                </div>
              </div>
            </div>

            <DialogFooter className="flex items-center gap-3">
              <Button variant="outline" onClick={() => setOpen(false)} disabled={isLoading}>
                Cancel
              </Button>
              <Button 
                onClick={handleApprove} 
                disabled={isLoading}
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin"></div>
                    Approving...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" /> Approve & Sign
                  </div>
                )}
              </Button>
            </DialogFooter>
          </>
        ) : (
          <div className="py-8 flex flex-col items-center justify-center text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500">
              <Check className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-[var(--foreground)]">Document Approved</h3>
              <p className="text-[var(--color-anthracite-400)] mt-2 max-w-sm">
                The draft has been digitally signed and is now ready for external export.
              </p>
            </div>
            <div className="flex items-center gap-3 mt-4 pt-4 border-t border-[var(--border-surface)] w-full justify-center">
              <Button variant="outline" onClick={handleClose}>
                Close
              </Button>
              <Button className="bg-[var(--color-lila-600)] text-white hover:bg-[var(--color-lila-500)] gap-2">
                <FileUp className="w-4 h-4" /> Export as PDF
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
