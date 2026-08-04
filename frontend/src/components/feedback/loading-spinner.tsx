import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type LoadingSpinnerProps = {
  className?: string;
  label?: string;
  size?: "sm" | "md" | "lg";
};

const sizeMap = {
  sm: "h-4 w-4",
  md: "h-6 w-6",
  lg: "h-8 w-8",
} as const;

export function LoadingSpinner({
  className,
  label = "Loading",
  size = "md",
}: LoadingSpinnerProps) {
  return (
    <div
      className={cn("inline-flex items-center justify-center gap-2 text-muted-foreground", className)}
      role="status"
      aria-live="polite"
    >
      <Loader2 className={cn("animate-edp-spin", sizeMap[size])} aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </div>
  );
}
