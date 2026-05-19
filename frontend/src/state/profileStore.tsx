import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import {
  createProfileProfilesPost,
  deleteProfileProfilesProfileIdDelete,
  listProfilesProfilesGet,
  updateProfileProfilesProfileIdPatch,
} from '@/client';
import type { Profile } from '@/client/types.gen';
import { ACTIVE_PROFILE_STORAGE_KEY, readActiveProfileId } from '@/client/configure';

import { useAuth } from './authStore';

interface ProfileContextValue {
  profiles: Profile[];
  activeProfileId: string | null;
  activeProfile: Profile | null;
  loading: boolean;
  setActiveProfile: (profileId: string) => void;
  refreshProfiles: () => Promise<void>;
  createProfile: (name: string) => Promise<Profile>;
  renameProfile: (profileId: string, name: string) => Promise<Profile>;
  setDefaultProfile: (profileId: string) => Promise<Profile>;
  deleteProfile: (profileId: string) => Promise<void>;
}

const ProfileContext = createContext<ProfileContextValue | null>(null);

function persistActiveProfile(profileId: string | null): void {
  try {
    if (profileId) localStorage.setItem(ACTIVE_PROFILE_STORAGE_KEY, profileId);
    else localStorage.removeItem(ACTIVE_PROFILE_STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

export function ProfileProvider({ children }: { children: React.ReactNode }) {
  const { status } = useAuth();
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [activeProfileId, setActiveProfileIdState] = useState<string | null>(() => readActiveProfileId());
  const [loading, setLoading] = useState(false);

  const setActiveProfile = useCallback((profileId: string) => {
    persistActiveProfile(profileId);
    setActiveProfileIdState(profileId);
  }, []);

  const reconcileActive = useCallback((list: Profile[]) => {
    const current = readActiveProfileId();
    const stillExists = list.some((p) => p.id === current);
    if (stillExists && current) {
      setActiveProfileIdState(current);
      return;
    }
    const fallback = list.find((p) => p.isDefault) ?? list[0];
    if (fallback) {
      persistActiveProfile(fallback.id);
      setActiveProfileIdState(fallback.id);
    } else {
      persistActiveProfile(null);
      setActiveProfileIdState(null);
    }
  }, []);

  const refreshProfiles = useCallback(async () => {
    setLoading(true);
    try {
      const response = await listProfilesProfilesGet();
      const list = response.data ?? [];
      setProfiles(list);
      reconcileActive(list);
    } finally {
      setLoading(false);
    }
  }, [reconcileActive]);

  useEffect(() => {
    if (status === 'authenticated') {
      refreshProfiles();
    } else if (status === 'unauthenticated') {
      setProfiles([]);
      persistActiveProfile(null);
      setActiveProfileIdState(null);
    }
  }, [status, refreshProfiles]);

  const createProfile = useCallback(async (name: string) => {
    const response = await createProfileProfilesPost({ body: { name } });
    if (!response.data) throw new Error('Failed to create profile');
    await refreshProfiles();
    return response.data;
  }, [refreshProfiles]);

  const renameProfile = useCallback(async (profileId: string, name: string) => {
    const response = await updateProfileProfilesProfileIdPatch({
      path: { profile_id: profileId },
      body: { name },
    });
    if (!response.data) throw new Error('Failed to rename profile');
    await refreshProfiles();
    return response.data;
  }, [refreshProfiles]);

  const setDefaultProfile = useCallback(async (profileId: string) => {
    const response = await updateProfileProfilesProfileIdPatch({
      path: { profile_id: profileId },
      body: { isDefault: true },
    });
    if (!response.data) throw new Error('Failed to set default profile');
    await refreshProfiles();
    return response.data;
  }, [refreshProfiles]);

  const deleteProfile = useCallback(async (profileId: string) => {
    await deleteProfileProfilesProfileIdDelete({ path: { profile_id: profileId } });
    await refreshProfiles();
  }, [refreshProfiles]);

  const activeProfile = useMemo(
    () => profiles.find((p) => p.id === activeProfileId) ?? null,
    [profiles, activeProfileId],
  );

  const value = useMemo<ProfileContextValue>(
    () => ({
      profiles,
      activeProfileId,
      activeProfile,
      loading,
      setActiveProfile,
      refreshProfiles,
      createProfile,
      renameProfile,
      setDefaultProfile,
      deleteProfile,
    }),
    [profiles, activeProfileId, activeProfile, loading, setActiveProfile, refreshProfiles, createProfile, renameProfile, setDefaultProfile, deleteProfile],
  );

  return <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>;
}

export function useProfiles(): ProfileContextValue {
  const ctx = useContext(ProfileContext);
  if (!ctx) throw new Error('useProfiles must be used inside <ProfileProvider>');
  return ctx;
}
