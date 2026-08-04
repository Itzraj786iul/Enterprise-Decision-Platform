import { cn } from "@/lib/utils";

type ContentContainerProps = {
  children: React.ReactNode;
  className?: string;
  size?: "default" | "narrow" | "wide" | "full";
};

const sizeClass = {
  narrow: "max-w-3xl",
  default: "max-w-7xl",
  wide: "max-w-[90rem]",
  full: "max-w-none",
} as const;

export function ContentContainer({
  children,
  className,
  size = "wide",
}: ContentContainerProps) {
  return (
    <div className={cn("edp-container py-6 lg:py-8", sizeClass[size], className)}>
      {children}
    </div>
  );
}
