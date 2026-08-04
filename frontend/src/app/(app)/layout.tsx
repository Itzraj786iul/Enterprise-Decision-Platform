"use client";

import { ApplicationShell } from "@/components/shell/application-shell";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <ApplicationShell>{children}</ApplicationShell>;
}
