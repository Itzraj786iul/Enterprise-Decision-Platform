"use client";

import { LogOut, Settings, User } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

type UserMenuProps = {
  name: string;
  email?: string;
  imageUrl?: string;
  onProfile?: () => void;
  onSettings?: () => void;
  onSignOut?: () => void;
};

export function UserMenu({
  name,
  email,
  imageUrl,
  onProfile,
  onSettings,
  onSignOut,
}: UserMenuProps) {
  const initials = name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="relative h-9 gap-2 rounded-full px-1.5"
          aria-label="Open user menu"
        >
          <Avatar className="h-8 w-8">
            {imageUrl ? <AvatarImage src={imageUrl} alt="" /> : null}
            <AvatarFallback>{initials}</AvatarFallback>
          </Avatar>
          <span className="hidden max-w-[8rem] truncate text-sm font-medium sm:inline">
            {name}
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>
          <div className="flex flex-col space-y-0.5">
            <span>{name}</span>
            {email ? <span className="text-xs font-normal text-muted-foreground">{email}</span> : null}
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={onProfile}>
          <User className="h-4 w-4" aria-hidden="true" />
          Profile
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={onSettings}>
          <Settings className="h-4 w-4" aria-hidden="true" />
          Settings
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={onSignOut}>
          <LogOut className="h-4 w-4" aria-hidden="true" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

/** Alias for product naming consistency. */
export const ProfileMenu = UserMenu;
