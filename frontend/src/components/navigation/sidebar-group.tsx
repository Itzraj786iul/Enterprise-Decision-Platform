import { cn } from "@/lib/utils";

type SidebarGroupProps = {
  label?: string;
  collapsed?: boolean;
  children: React.ReactNode;
  className?: string;
};

export function SidebarGroup({ label, collapsed = false, children, className }: SidebarGroupProps) {
  return (
    <div className={cn("mb-3 space-y-1", className)} role="group" aria-label={label}>
      {label && !collapsed ? (
        <p className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-sidebar-muted">
          {label}
        </p>
      ) : null}
      <div className="space-y-0.5">{children}</div>
    </div>
  );
}
