import { cn } from "@/lib/utils";

type SectionHeaderProps = {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
};

export function SectionHeader({ title, description, actions, className }: SectionHeaderProps) {
  return (
    <div className={cn("mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between", className)}>
      <div className="space-y-1">
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
        {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}
