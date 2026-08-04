"use client";

import { AlertCircle, AlertTriangle, Bell, CheckCircle2, Info, Trash2 } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import { EmptyState } from "@/components/feedback/empty-state";
import {
  unreadCount,
  useNotificationStore,
  type NotificationTone,
} from "@/store/notification-store";
import { cn } from "@/lib/utils";

const toneIcon: Record<NotificationTone, React.ReactNode> = {
  success: <CheckCircle2 className="h-4 w-4 text-success" aria-hidden="true" />,
  warning: <AlertTriangle className="h-4 w-4 text-warning" aria-hidden="true" />,
  error: <AlertCircle className="h-4 w-4 text-danger" aria-hidden="true" />,
  info: <Info className="h-4 w-4 text-info" aria-hidden="true" />,
};

function formatRelative(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function NotificationCenter() {
  const notifications = useNotificationStore((s) => s.notifications);
  const markRead = useNotificationStore((s) => s.markRead);
  const markAllRead = useNotificationStore((s) => s.markAllRead);
  const dismiss = useNotificationStore((s) => s.dismiss);
  const clearAll = useNotificationStore((s) => s.clearAll);
  const unread = unreadCount(notifications);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative" aria-label="Open notifications">
          <Bell className="h-4 w-4" />
          {unread > 0 ? (
            <span className="absolute right-1.5 top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-danger px-1 text-[10px] font-semibold text-danger-foreground">
              {unread > 9 ? "9+" : unread}
            </span>
          ) : null}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[22rem] p-0">
        <div className="flex items-center justify-between px-3 py-2">
          <DropdownMenuLabel className="p-0">Notifications</DropdownMenuLabel>
          <div className="flex items-center gap-1">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 text-xs"
              disabled={unread === 0}
              onClick={markAllRead}
            >
              Mark all read
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              aria-label="Clear all notifications"
              disabled={notifications.length === 0}
              onClick={clearAll}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
        <DropdownMenuSeparator className="m-0" />
        {notifications.length === 0 ? (
          <EmptyState
            title="No notifications"
            description="System notices will appear here. Nothing requires your attention right now."
            icon={Bell}
            className="border-0 py-10 shadow-none"
          />
        ) : (
          <ScrollArea className="h-80">
            <ul className="p-1" role="list">
              <AnimatePresence initial={false}>
                {notifications.map((item) => (
                  <motion.li
                    key={item.id}
                    layout
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.18 }}
                  >
                    <button
                      type="button"
                      className={cn(
                        "flex w-full gap-3 rounded-md px-3 py-2.5 text-left transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                        !item.read && "bg-muted/50",
                      )}
                      onClick={() => markRead(item.id)}
                    >
                      <span className="mt-0.5">{toneIcon[item.tone]}</span>
                      <span className="min-w-0 flex-1">
                        <span className="flex items-start justify-between gap-2">
                          <span className="text-sm font-medium">{item.title}</span>
                          {!item.read ? (
                            <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" aria-label="Unread" />
                          ) : null}
                        </span>
                        {item.description ? (
                          <span className="mt-0.5 block text-xs text-muted-foreground">
                            {item.description}
                          </span>
                        ) : null}
                        <span className="mt-1 block text-[11px] text-muted-foreground">
                          {formatRelative(item.createdAt)}
                        </span>
                      </span>
                      <span
                        role="presentation"
                        className="self-start rounded-sm p-1 text-muted-foreground hover:bg-background hover:text-foreground"
                        onClick={(e) => {
                          e.stopPropagation();
                          dismiss(item.id);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.stopPropagation();
                            dismiss(item.id);
                          }
                        }}
                      >
                        <span className="sr-only">Dismiss</span>
                        ×
                      </span>
                    </button>
                  </motion.li>
                ))}
              </AnimatePresence>
            </ul>
          </ScrollArea>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
