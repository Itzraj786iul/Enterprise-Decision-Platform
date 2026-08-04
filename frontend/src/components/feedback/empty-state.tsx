import { AlertCircle, Inbox, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

type EmptyStateProps = {
  title: string;
  description?: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
  className?: string;
};

export function EmptyState({
  title,
  description,
  icon: Icon = Inbox,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border bg-card/50 px-6 py-12 text-center",
        className,
      )}
      role="status"
    >
      <div className="rounded-full bg-muted p-3 text-muted-foreground">
        <Icon className="h-6 w-6" aria-hidden="true" />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-semibold">{title}</p>
        {description ? <p className="max-w-sm text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}

type ErrorStateProps = {
  title?: string;
  description?: string;
  onRetry?: () => void;
  className?: string;
};

export function ErrorState({
  title = "Something went wrong",
  description = "We could not load this content. Please try again.",
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-lg border border-danger/30 bg-danger/5 px-6 py-12 text-center",
        className,
      )}
      role="alert"
    >
      <AlertCircle className="h-6 w-6 text-danger" aria-hidden="true" />
      <div className="space-y-1">
        <p className="text-sm font-semibold">{title}</p>
        <p className="max-w-sm text-sm text-muted-foreground">{description}</p>
      </div>
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  );
}

export function NoData(props: Omit<EmptyStateProps, "title"> & { title?: string }) {
  return (
    <EmptyState
      title={props.title ?? "No data available"}
      description={props.description ?? "There is nothing to display for the current selection."}
      {...props}
    />
  );
}
