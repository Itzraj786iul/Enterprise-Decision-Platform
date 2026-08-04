"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type NotificationTone = "success" | "warning" | "error" | "info";

export type AppNotification = {
  id: string;
  title: string;
  description?: string;
  tone: NotificationTone;
  createdAt: string;
  read: boolean;
};

type NotificationState = {
  notifications: AppNotification[];
  markRead: (id: string) => void;
  markAllRead: () => void;
  dismiss: (id: string) => void;
  clearAll: () => void;
  /** Framework helper — not for business analytics payloads */
  addNotification: (input: Omit<AppNotification, "id" | "createdAt" | "read"> & { id?: string }) => void;
};

export const useNotificationStore = create<NotificationState>()(
  persist(
    (set) => ({
      // Empty by default — no fake business alerts
      notifications: [],
      markRead: (id) =>
        set((state) => ({
          notifications: state.notifications.map((n) =>
            n.id === id ? { ...n, read: true } : n,
          ),
        })),
      markAllRead: () =>
        set((state) => ({
          notifications: state.notifications.map((n) => ({ ...n, read: true })),
        })),
      dismiss: (id) =>
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        })),
      clearAll: () => set({ notifications: [] }),
      addNotification: (input) =>
        set((state) => ({
          notifications: [
            {
              id: input.id ?? crypto.randomUUID(),
              title: input.title,
              description: input.description,
              tone: input.tone,
              createdAt: new Date().toISOString(),
              read: false,
            },
            ...state.notifications,
          ].slice(0, 50),
        })),
    }),
    {
      name: "edp-notifications",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);

export function unreadCount(notifications: AppNotification[]) {
  return notifications.filter((n) => !n.read).length;
}
