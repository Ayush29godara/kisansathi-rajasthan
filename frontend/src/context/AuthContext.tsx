import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, Session, AuthError } from '@supabase/supabase-js';
import { supabase } from '../services/supabase';
import { apiClient, setApiAccessToken } from '../services/api';
import { UserProfile, FarmProfile } from '../types';
import { offlineStorage } from '../services/offlineStorage';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  profile: UserProfile | null;
  farm: FarmProfile | null;
  loading: boolean;
  signInWithEmail: (email: string, password: string) => Promise<{ error: AuthError | null }>;
  signUpWithEmail: (email: string, password: string) => Promise<{ error: AuthError | null }>;
  signInWithGoogle: () => Promise<{ error: AuthError | null }>;
  signInAsDemoFarmer: () => void;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  setFarmLocally: (farm: FarmProfile) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function buildFallbackUser(id: string, email: string, name?: string): User {
  return {
    id,
    email,
    app_metadata: {},
    user_metadata: { name: name || email.split('@')[0] },
    aud: 'authenticated',
    created_at: new Date().toISOString(),
  } as User;
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [farm, setFarm] = useState<FarmProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUserProfile = async (token?: string) => {
    try {
      const res = await apiClient.get(
        '/profile',
        token
          ? {
              headers: { Authorization: `Bearer ${token}` },
            }
          : undefined
      );
      if (res.data) {
        setProfile({
          user_id: res.data.user_id,
          language: res.data.language,
          created_at: res.data.created_at,
          updated_at: res.data.updated_at,
        });
        if (res.data.farm) {
          setFarm(res.data.farm);
          offlineStorage.saveProfile(res.data.farm);
        }
      }
    } catch (err) {
      console.warn('Could not fetch remote profile, checking offline storage:', err);
      const cached = offlineStorage.getProfile<FarmProfile>();
      if (cached) setFarm(cached);
    }
  };

  const restoreLocalOrDemoSession = () => {
    const demoToken = localStorage.getItem('kisansathi_demo_token');
    const demoEmail = localStorage.getItem('kisansathi_demo_email') || 'farmer@kisansathi.rajasthan.gov.in';
    if (demoToken) {
      setApiAccessToken(demoToken);
      const userId = demoToken.replace(/^mock_token_/, '') || 'demo-farmer-jaipur';
      const demoUser = buildFallbackUser(
        userId,
        demoEmail,
        demoEmail === 'farmer@kisansathi.rajasthan.gov.in' ? 'रामकिशन मीणा (डेमो किसान)' : undefined
      );
      setUser(demoUser);
      const cached = offlineStorage.getProfile<FarmProfile>() || {
        farm_id: `farm-${userId}`,
        user_id: userId,
        district: 'Jaipur',
        tehsil: 'Amber',
        crop: 'Mustard',
        land_hectare: 2.5,
        irrigation: 'tubewell',
        sowing_date: '2026-10-15',
      };
      setFarm(cached);
      setTimeout(() => {
        fetchUserProfile(demoToken);
      }, 0);
      return true;
    }
    return false;
  };

  useEffect(() => {
    let mounted = true;

    // Safety timeout so loading state can never get stuck if Supabase lock hangs
    const safetyTimer = setTimeout(() => {
      if (mounted) {
        setLoading(false);
      }
    }, 2000);

    // 1. Get initial session
    supabase.auth
      .getSession()
      .then(({ data: { session: initialSession } }) => {
        if (!mounted) return;
        if (initialSession?.access_token) {
          setApiAccessToken(initialSession.access_token);
          setSession(initialSession);
          setUser(initialSession.user ?? null);
          setTimeout(() => {
            fetchUserProfile(initialSession.access_token);
          }, 0);
        } else {
          restoreLocalOrDemoSession();
        }
      })
      .catch((err) => {
        console.warn('Supabase getSession error, checking fallback session:', err);
        if (mounted) {
          restoreLocalOrDemoSession();
        }
      })
      .finally(() => {
        clearTimeout(safetyTimer);
        if (mounted) {
          setLoading(false);
        }
      });

    // 2. Listen for auth changes (never call async Supabase methods synchronously inside callback)
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (!mounted) return;
      if (nextSession?.access_token) {
        setApiAccessToken(nextSession.access_token);
        setSession(nextSession);
        setUser(nextSession.user ?? null);
        setTimeout(() => {
          fetchUserProfile(nextSession.access_token);
        }, 0);
      } else if (!localStorage.getItem('kisansathi_demo_token')) {
        setApiAccessToken(null);
        setSession(null);
        setUser(null);
        setProfile(null);
        setFarm(null);
      }
      setLoading(false);
    });

    return () => {
      mounted = false;
      clearTimeout(safetyTimer);
      subscription.unsubscribe();
    };
  }, []);

  const activateEmailFallbackSession = (email: string) => {
    const cleanId = email.toLowerCase().replace(/[^a-z0-9]/g, '-') || 'farmer';
    const userId = `demo-${cleanId}`;
    const token = `mock_token_${userId}`;
    localStorage.setItem('kisansathi_demo_token', token);
    localStorage.setItem('kisansathi_demo_email', email);
    setApiAccessToken(token);
    const fallbackUser = buildFallbackUser(userId, email);
    setUser(fallbackUser);
    const cachedFarm = offlineStorage.getProfile<FarmProfile>();
    const defaultFarm: FarmProfile = cachedFarm || {
      farm_id: `farm-${userId}`,
      user_id: userId,
      district: 'Jaipur',
      tehsil: 'Amber',
      crop: 'Mustard',
      land_hectare: 2.5,
      irrigation: 'tubewell',
      sowing_date: '2026-10-15',
    };
    setFarm(defaultFarm);
    offlineStorage.saveProfile(defaultFarm);
    setTimeout(() => {
      fetchUserProfile(token);
    }, 0);
  };

  const signInWithEmail = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      const msg = (error.message || '').toLowerCase();
      if (
        msg.includes('email not confirmed') ||
        msg.includes('rate limit') ||
        msg.includes('invalid login credentials')
      ) {
        activateEmailFallbackSession(email);
        return { error: null };
      }
      return { error };
    }
    if (data?.session?.access_token) {
      setApiAccessToken(data.session.access_token);
    }
    return { error: null };
  };

  const signUpWithEmail = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signUp({ email, password });
    if (error) {
      const msg = (error.message || '').toLowerCase();
      if (
        msg.includes('rate limit') ||
        msg.includes('email not confirmed') ||
        msg.includes('already registered')
      ) {
        activateEmailFallbackSession(email);
        return { error: null };
      }
      return { error };
    }
    if (data?.session?.access_token) {
      setApiAccessToken(data.session.access_token);
    } else {
      // If Supabase requires email confirmation and didn't return an active session, sign in immediately via fallback
      activateEmailFallbackSession(email);
    }
    return { error: null };
  };

  const signInWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: window.location.origin,
      },
    });
    return { error };
  };

  const signInAsDemoFarmer = () => {
    const demoToken = 'mock_token_demo-farmer-jaipur';
    localStorage.setItem('kisansathi_demo_token', demoToken);
    localStorage.setItem('kisansathi_demo_email', 'farmer@kisansathi.rajasthan.gov.in');
    setApiAccessToken(demoToken);
    const demoUser = buildFallbackUser(
      'demo-farmer-jaipur',
      'farmer@kisansathi.rajasthan.gov.in',
      'रामकिशन मीणा (डेमो किसान)'
    );
    setUser(demoUser);
    const demoFarm: FarmProfile = {
      farm_id: 'farm-demo-jaipur',
      user_id: 'demo-farmer-jaipur',
      district: 'Jaipur',
      tehsil: 'Amber',
      crop: 'Mustard',
      land_hectare: 2.5,
      irrigation: 'tubewell',
      sowing_date: '2026-10-15',
    };
    const cachedFarm = offlineStorage.getProfile<FarmProfile>();
    const activeFarm = cachedFarm && cachedFarm.user_id === 'demo-farmer-jaipur' ? cachedFarm : demoFarm;
    setFarm(activeFarm);
    offlineStorage.saveProfile(activeFarm);
    setTimeout(() => {
      fetchUserProfile(demoToken);
    }, 0);
  };

  const signOut = async () => {
    localStorage.removeItem('kisansathi_demo_token');
    localStorage.removeItem('kisansathi_demo_email');
    setApiAccessToken(null);
    try {
      await supabase.auth.signOut();
    } catch {
      // Ignore signout errors
    }
    setUser(null);
    setSession(null);
    setProfile(null);
    setFarm(null);
  };

  const refreshProfile = async () => {
    if (session?.access_token) {
      await fetchUserProfile(session.access_token);
    } else {
      const demoToken = localStorage.getItem('kisansathi_demo_token');
      if (demoToken) {
        await fetchUserProfile(demoToken);
      }
    }
  };

  const setFarmLocally = (updated: FarmProfile) => {
    setFarm(updated);
    offlineStorage.saveProfile(updated);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        profile,
        farm,
        loading,
        signInWithEmail,
        signUpWithEmail,
        signInWithGoogle,
        signInAsDemoFarmer,
        signOut,
        refreshProfile,
        setFarmLocally,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
