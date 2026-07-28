import React, { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { FileEdit, Plus, Save, Download, Loader2, Clock } from 'lucide-react';
import { 
  useListMatterDraftsApiV1DraftStudioDraftsMatterMatterIdGet as useListMatterDrafts,
  useGetDraftApiV1DraftStudioDraftsDraftIdGet as useGetDraft,
  useSaveDraftApiV1DraftStudioDraftsPost as useSaveDraft,
  useUpdateDraftApiV1DraftStudioDraftsDraftIdPut as useUpdateDraft,
  useExportDraftApiV1DraftStudioDraftsDraftIdExportPost as useExportDraft,
  useSubmitReviewDraft,
  useApproveDraft,
  useGetDraftCitations
} from '@/api/endpoints/draft-studio/draft-studio';
import { StatusBadge } from '@/components/ui/status-badge';
import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';

export function DraftStudioShell({ matterId }: { matterId: string }) {
  const queryClient = useQueryClient();
  const [activeDraftId, setActiveDraftId] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [currentVersion, setCurrentVersion] = useState(1);
  const [isDirty, setIsDirty] = useState(false);

  const { data: draftsResponse, isLoading: isLoadingList } = useListMatterDrafts(matterId);
  const drafts: any = draftsResponse?.data || [];

  const { data: activeDraftResponse, isLoading: isLoadingDetail } = useGetDraft(activeDraftId as string, {
    query: { enabled: !!activeDraftId }
  });
  const activeDraft: any = activeDraftResponse?.data;

  const { data: citationsResponse } = useGetDraftCitations(activeDraftId as string, {
    query: { enabled: !!activeDraftId }
  });
  const citations: any[] = (citationsResponse?.data as any[]) || [];

  useEffect(() => {
    if (activeDraft) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTitle(activeDraft.title || '');
      setContent(activeDraft.content || '');
      setCurrentVersion(activeDraft.version || 1);
      setIsDirty(false);
    }
  }, [activeDraft]);

  const createMutation = useSaveDraft({
    mutation: {
      onSuccess: (res: any) => {
        toast.success('New draft created');
        queryClient.invalidateQueries({ queryKey: ['useListMatterDrafts'] });
        setActiveDraftId(res.data.id);
      },
      onError: () => toast.error('Failed to create draft')
    }
  });

  const saveMutation = useUpdateDraft({
    mutation: {
      onSuccess: (res: any) => {
        toast.success(`Draft saved (v${res.data.version})`);
        setCurrentVersion(res.data.version);
        setIsDirty(false);
        queryClient.invalidateQueries({ queryKey: ['useListMatterDrafts'] });
        queryClient.invalidateQueries({ queryKey: ['useGetDraft', activeDraftId] });
      },
      onError: (error: any) => {
        if (error.response?.status === 409) {
          toast.error('Version conflict! Someone else modified this draft.');
        } else {
          toast.error('Failed to save draft');
        }
      }
    }
  });

  const exportMutation = useExportDraft({
    mutation: {
      onSuccess: (res: any, variables) => {
        toast.success(`Export job queued (${variables.data.format.toUpperCase()})`);
      },
      onError: () => toast.error('Export request failed')
    }
  });

  const submitReviewMutation = useSubmitReviewDraft({
    mutation: {
      onSuccess: () => {
        toast.success('Draft submitted for review');
        queryClient.invalidateQueries({ queryKey: ['useListMatterDrafts'] });
        queryClient.invalidateQueries({ queryKey: ['useGetDraft', activeDraftId] });
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to submit for review');
      }
    }
  });

  const approveMutation = useApproveDraft({
    mutation: {
      onSuccess: () => {
        toast.success('Draft approved for external use');
        queryClient.invalidateQueries({ queryKey: ['useListMatterDrafts'] });
        queryClient.invalidateQueries({ queryKey: ['useGetDraft', activeDraftId] });
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to approve draft');
      }
    }
  });

  return (
    <div className="flex gap-6 min-h-[600px] border border-[var(--border-surface)] rounded-xl overflow-hidden bg-[var(--bg-surface)] shadow-sm">
      {/* Sidebar List */}
      <div className="w-72 border-r border-[var(--border-surface)] p-4 flex flex-col bg-[var(--bg-surface-hover)]">
        <div className="flex items-center justify-between mb-6 px-1">
          <h3 className="font-semibold text-[var(--foreground)] flex items-center gap-2 text-sm tracking-wide">
            <FileEdit className="w-4 h-4 text-[var(--color-lila-500)]" />
            DRAFTS
          </h3>
          <button
            onClick={() => createMutation.mutate({ data: { matter_id: matterId, title: 'New Legal Draft', content: '# New Legal Document\n\nEnter clauses and terms here...' } })}
            disabled={createMutation.isPending}
            className="p-1.5 bg-[var(--color-lila-600)] hover:bg-[var(--color-lila-500)] text-white rounded-lg transition-colors disabled:opacity-50 shadow-sm"
            title="New Draft"
          >
            {createMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          </button>
        </div>

        {isLoadingList ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-[var(--color-lila-500)]" />
          </div>
        ) : drafts && drafts.length > 0 ? (
          <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
            {drafts.map((d: any) => (
              <button
                key={d.id}
                onClick={() => setActiveDraftId(d.id)}
                className={`w-full text-left p-3.5 rounded-xl text-sm transition-all flex flex-col gap-2 ${
                  activeDraftId === d.id
                    ? 'bg-[var(--color-lila-500)]/10 border border-[var(--color-lila-500)]/30 shadow-sm'
                    : 'bg-[var(--bg-surface)] border border-transparent hover:border-[var(--border-surface)] hover:shadow-sm'
                }`}
              >
                <div className={`font-medium truncate ${activeDraftId === d.id ? 'text-[var(--color-lila-400)]' : 'text-[var(--foreground)]'}`}>
                  {d.title}
                </div>
                <div className="flex items-center justify-between text-xs text-[var(--color-anthracite-400)]">
                  <span className="bg-[var(--color-anthracite-800)] px-2 py-0.5 rounded text-[var(--color-anthracite-200)] font-mono font-medium">v{d.version}</span>
                  {d.updated_at && (
                    <span className="flex items-center gap-1.5 opacity-80">
                      <Clock className="w-3 h-3" />
                      {new Date(d.updated_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-4 text-[var(--color-anthracite-400)] text-sm bg-[var(--bg-surface)] rounded-xl border border-[var(--border-surface)] border-dashed mx-1 mb-1">
            <FileEdit className="w-8 h-8 mb-3 opacity-50 text-[var(--color-lila-500)]" />
            <p className="font-medium text-[var(--foreground)] mb-1">No drafts yet</p>
            <p className="text-xs">Click + to start writing.</p>
          </div>
        )}
      </div>

      {/* Editor Main Area */}
      <div className="flex-1 p-6 md:p-8 flex flex-col bg-[var(--bg-surface)]">
        {!activeDraftId ? (
          <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-anthracite-400)]">
            <div className="w-16 h-16 rounded-2xl bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] flex items-center justify-center mb-4">
              <FileEdit className="w-8 h-8 text-[var(--color-lila-500)]/60" />
            </div>
            <h4 className="text-lg font-semibold text-[var(--foreground)] mb-1">Select or Create a Draft</h4>
            <p className="text-sm">Choose a draft from the left sidebar to start editing.</p>
          </div>
        ) : isLoadingDetail ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-[var(--color-lila-500)]" />
          </div>
        ) : (
          <>
            {/* Header / Actions */}
            <div className="flex items-center justify-between gap-4 mb-6 pb-6 border-b border-[var(--border-surface)]">
              <input
                type="text"
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  setIsDirty(true);
                }}
                placeholder="Draft Title..."
                className="bg-transparent text-2xl font-bold text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--color-lila-500)]/50 rounded-lg px-3 py-1.5 flex-1 border border-transparent hover:bg-[var(--bg-surface-hover)] transition-colors placeholder:text-[var(--color-anthracite-500)]"
              />
              
              <div className="flex items-center gap-3">
                <StatusBadge status={activeDraft?.status === 'APPROVED_FOR_EXTERNAL_USE' ? 'success' : activeDraft?.status === 'IN_REVIEW' ? 'warning' : 'neutral'} label={activeDraft?.status?.replace(/_/g, ' ') || 'DRAFT'} />
                
                <span className="text-xs bg-[var(--color-anthracite-800)] text-[var(--color-anthracite-300)] font-mono font-medium px-3 py-1.5 rounded-lg border border-[var(--border-surface)]">
                  v{currentVersion}
                </span>

                <button
                  onClick={() => saveMutation.mutate({ draftId: activeDraftId, data: { title, content, expected_version: currentVersion } })}
                  disabled={!isDirty || saveMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-[var(--color-lila-600)] hover:bg-[var(--color-lila-500)] disabled:opacity-50 disabled:hover:bg-[var(--color-lila-600)] text-white text-sm font-medium rounded-xl transition-all shadow-sm"
                >
                  {saveMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  Save
                </button>

                <div className="h-6 w-px bg-[var(--border-surface)] mx-1" />

                {(activeDraft?.status === 'DRAFT' || activeDraft?.status === 'REJECTED') && (
                  <button
                    onClick={() => submitReviewMutation.mutate({ draftId: activeDraftId as string })}
                    disabled={submitReviewMutation.isPending || isDirty}
                    title={isDirty ? 'Save changes before submitting' : 'Submit for Review'}
                    className="flex items-center gap-1.5 px-3 py-2 bg-[var(--bg-surface-hover)] hover:bg-[var(--color-anthracite-800)] border border-[var(--border-surface)] disabled:opacity-50 text-[var(--foreground)] text-sm font-medium rounded-xl transition-colors"
                  >
                    Submit for Review
                  </button>
                )}

                {activeDraft?.status === 'IN_REVIEW' && (
                  <button
                    onClick={() => approveMutation.mutate({ draftId: activeDraftId as string })}
                    disabled={approveMutation.isPending || isDirty}
                    title="Approve Draft (Partner Access Required)"
                    className="flex items-center gap-1.5 px-3 py-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 disabled:opacity-50 text-sm font-medium rounded-xl transition-colors"
                  >
                    Approve (Partner)
                  </button>
                )}

                <div className="h-6 w-px bg-[var(--border-surface)] mx-1" />

                <button
                  onClick={() => exportMutation.mutate({ draftId: activeDraftId, data: { format: 'pdf' } })}
                  disabled={exportMutation.isPending || isDirty || activeDraft?.status !== 'APPROVED_FOR_EXTERNAL_USE'}
                  title={isDirty ? 'Save changes before exporting' : activeDraft?.status !== 'APPROVED_FOR_EXTERNAL_USE' ? 'Must be approved to export' : 'Queue PDF Export'}
                  className="flex items-center gap-1.5 px-3 py-2 bg-[var(--bg-surface-hover)] hover:bg-[var(--color-anthracite-800)] border border-[var(--border-surface)] disabled:opacity-50 text-[var(--foreground)] text-sm font-medium rounded-xl transition-colors"
                >
                  <Download className="w-4 h-4 text-rose-400" />
                  PDF
                </button>

                <button
                  onClick={() => exportMutation.mutate({ draftId: activeDraftId, data: { format: 'docx' } })}
                  disabled={exportMutation.isPending || isDirty || activeDraft?.status !== 'APPROVED_FOR_EXTERNAL_USE'}
                  title={isDirty ? 'Save changes before exporting' : activeDraft?.status !== 'APPROVED_FOR_EXTERNAL_USE' ? 'Must be approved to export' : 'Queue DOCX Export'}
                  className="flex items-center gap-1.5 px-3 py-2 bg-[var(--bg-surface-hover)] hover:bg-[var(--color-anthracite-800)] border border-[var(--border-surface)] disabled:opacity-50 text-[var(--foreground)] text-sm font-medium rounded-xl transition-colors"
                >
                  <Download className="w-4 h-4 text-blue-400" />
                  DOCX
                </button>
              </div>
            </div>

            {/* Content Editor */}
            <div className="flex-1 flex flex-col bg-[var(--bg-surface-hover)] rounded-xl border border-[var(--border-surface)] overflow-hidden shadow-inner">
              <textarea
                value={content}
                onChange={(e) => {
                  setContent(e.target.value);
                  setIsDirty(true);
                }}
                placeholder="Write or edit clauses, legal arguments, and contractual provisions here..."
                className="flex-1 w-full bg-transparent p-6 text-[var(--foreground)] font-mono text-sm leading-relaxed resize-none focus:outline-none focus:ring-1 focus:ring-[var(--color-lila-500)]/50 transition-shadow custom-scrollbar"
              />
            </div>
            <div className="flex justify-between items-center mt-3 text-xs text-[var(--color-anthracite-400)] px-2 font-medium">
              <span className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${isDirty ? 'bg-amber-400' : 'bg-emerald-400'}`}></span>
                {isDirty ? 'Unsaved changes' : 'All changes saved'}
              </span>
              <span>{content.length.toLocaleString()} characters</span>
            </div>
          </>
        )}
      </div>

      {/* Right Sidebar: Citations */}
      {activeDraftId && !isLoadingDetail && (
        <div className="w-80 border-l border-[var(--border-surface)] flex flex-col bg-[var(--bg-surface)] shrink-0">
          <div className="p-4 border-b border-[var(--border-surface)] bg-[var(--bg-surface-hover)] shrink-0">
            <h3 className="font-semibold text-[var(--foreground)] text-sm tracking-wide">
              Document Citations
            </h3>
            <p className="text-xs text-[var(--color-anthracite-400)] mt-1">
              Verified legal sources for this draft
            </p>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
            {citations.length === 0 ? (
              <div className="text-center text-[var(--color-anthracite-400)] text-xs mt-8">
                No citations found for this draft.
              </div>
            ) : (
              citations.map((c) => (
                <div key={c.id} className="p-3 bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] rounded-xl flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-[var(--color-lila-400)] bg-[var(--color-lila-500)]/10 px-1.5 py-0.5 rounded">
                      Doc: {c.document_id.substring(0,8)}
                    </span>
                    {c.verification_state === 'verified' ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    ) : c.verification_state === 'STALE_REVISION' ? (
                      <AlertTriangle className="w-4 h-4 text-amber-500" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-500" />
                    )}
                  </div>
                  <p className="text-xs text-[var(--foreground)] italic line-clamp-3">
                    "{c.text_snippet}"
                  </p>
                  <div className="text-[10px] text-[var(--color-anthracite-400)] uppercase font-semibold mt-1">
                    State: <span className={c.verification_state === 'verified' ? 'text-emerald-500' : 'text-amber-500'}>{c.verification_state}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
