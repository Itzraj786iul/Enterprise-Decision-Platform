"use client";

import { Check, ChevronsUpDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { workspaces } from "@/config/navigation";
import { useShellStore } from "@/store/shell-store";
import { cn } from "@/lib/utils";

export function WorkspaceSelector({ className }: { className?: string }) {
  const workspaceId = useShellStore((s) => s.workspaceId);
  const setWorkspaceId = useShellStore((s) => s.setWorkspaceId);
  const current = workspaces.find((w) => w.id === workspaceId) ?? workspaces[0];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={cn("hidden max-w-[12rem] gap-1.5 sm:inline-flex", className)}
          aria-label="Select workspace"
        >
          <span className="truncate">{current.label}</span>
          <ChevronsUpDown className="h-3.5 w-3.5 opacity-60" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        <DropdownMenuLabel>Workspace</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {workspaces.map((workspace) => (
          <DropdownMenuItem
            key={workspace.id}
            onSelect={() => setWorkspaceId(workspace.id)}
            className="justify-between"
          >
            {workspace.label}
            {workspace.id === current.id ? (
              <Check className="h-4 w-4 text-primary" aria-hidden="true" />
            ) : null}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
