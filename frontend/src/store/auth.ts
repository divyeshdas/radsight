"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: true }),
      clearAuth: () => {
        set({ user: null, isAuthenticated: false });
        if (typeof window !== "undefined") {
          localStorage.removeItem("radsight_access_token");
          localStorage.removeItem("radsight_refresh_token");
        }
      },
    }),
    { name: "radsight-auth", partialize: (s) => ({ user: s.user, isAuthenticated: s.isAuthenticated }) }
  )
);
