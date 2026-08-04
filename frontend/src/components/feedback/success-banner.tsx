import { CheckCircle2, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

type SuccessBannerProps = {
  title: string;
  description?: string;
  onDismiss?: () => void;
  className?: string;
};

export function SuccessBanner({ title, description, onDismiss, className }: SuccessBannerProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg border border-success/30 bg-success/10 px-4 py-3 text-foreground",
        className,
      )}
      role="status"
    >
      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium">{title}</p>
        {description ? <p className="mt-0.5 text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {onDismiss ? (
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          aria-label="Dismiss success message"
          onClick={onDismiss}
        >
          <X className="h-3.5 w-3.5" />
        </Button>
      ) : null}
    </div>
  );
}
