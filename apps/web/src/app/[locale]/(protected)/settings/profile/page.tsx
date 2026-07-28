'use client'

import { useState } from 'react'
import { User, Mail, Save, Loader2, Shield, Camera } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from 'react-hot-toast'
import { useGetCurrentUserProfileApiV1UsersMeGet, useUpdateCurrentUserProfile } from '@/api/endpoints/users/users'

export default function ProfilePage() {
  const { data: profileResponse, refetch, isLoading } = useGetCurrentUserProfileApiV1UsersMeGet()
  const { mutateAsync: updateProfile, isPending: isUpdating } = useUpdateCurrentUserProfile()
  const profile: any = profileResponse

  const [fullName, setFullName] = useState(profile?.full_name || '')
  const [email, setEmail] = useState(profile?.email || '')
  const [isDirty, setIsDirty] = useState(false)

  // Sync state on load
  if (profile && !fullName && !email) {
    setFullName(profile.full_name)
    setEmail(profile.email)
  }

  const updateMutation = useUpdateCurrentUserProfile({
    mutation: {
      onSuccess: () => {
        toast.success("Profile updated successfully")
        setIsDirty(false)
        refetch()
      },
      onError: () => toast.error("Failed to update profile")
    }
  })

  const handleSave = () => {
    updateMutation.mutate({ data: { full_name: fullName, email: email } })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-[var(--color-lila-500)]" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6 lg:p-8 space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">User Profile</h1>
          <p className="text-[var(--color-anthracite-500)] mt-1">Manage your personal information and preferences.</p>
        </div>
        <Button onClick={handleSave} disabled={!isDirty || updateMutation.isPending} className="gap-2 bg-[var(--color-lila-600)] text-white hover:bg-[var(--color-lila-500)]">
          {updateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          {updateMutation.isPending ? 'Saving...' : 'Save Profile'}
        </Button>
      </div>

      <div className="glass-card rounded-xl border border-[var(--border-surface)] overflow-hidden">
        <div className="p-6 md:p-8 border-b border-[var(--border-surface)] flex items-center gap-6">
          <div className="relative group cursor-not-allowed">
            <div className="w-24 h-24 rounded-full bg-[var(--color-lila-500)]/10 border-2 border-[var(--color-lila-500)]/20 flex items-center justify-center text-3xl font-bold text-[var(--color-lila-500)]">
              {profile?.full_name ? profile.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="absolute inset-0 bg-black/50 rounded-full hidden group-hover:flex items-center justify-center backdrop-blur-sm transition-all">
              <Camera className="w-6 h-6 text-white/50" />
            </div>
          </div>
          <div>
            <h2 className="text-xl font-semibold text-[var(--foreground)]">{profile?.full_name || 'User'}</h2>
            <p className="text-[var(--color-anthracite-400)]">{profile?.roles?.join(', ') || 'No specific roles'}</p>
          </div>
        </div>

        <div className="p-6 md:p-8 space-y-6 bg-[var(--bg-surface-hover)]">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none flex items-center gap-2">
                <User className="w-4 h-4 text-[var(--color-anthracite-400)]" /> Full Name
              </label>
              <Input 
                value={fullName}
                onChange={(e) => {
                  setFullName(e.target.value)
                  setIsDirty(true)
                }}
                className="bg-[var(--background)] border-[var(--border-surface)]" 
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none flex items-center gap-2">
                <Mail className="w-4 h-4 text-[var(--color-anthracite-400)]" /> Email Address
              </label>
              <Input 
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  setIsDirty(true)
                }}
                className="bg-[var(--background)] border-[var(--border-surface)]" 
              />
            </div>
          </div>

          {profile?.is_support_access_granted && (
            <div className="mt-8 p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-4">
              <Shield className="w-6 h-6 text-amber-500 shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-[var(--foreground)] text-amber-500">Support Access Active</h3>
                <p className="text-sm text-[var(--color-anthracite-400)] mt-1">
                  You have granted temporary support access to MESA engineers. Valid until: {new Date(profile.support_access_granted_until).toLocaleString()}.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
