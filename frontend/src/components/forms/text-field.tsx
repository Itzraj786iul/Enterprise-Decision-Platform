"use client";

import * as React from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type TextFieldProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  description?: string;
  error?: string;
  containerClassName?: string;
};

export const TextField = React.forwardRef<HTMLInputElement, TextFieldProps>(
  ({ label, description, error, id, className, containerClassName, ...props }, ref) => {
    const fieldId = id ?? label.toLowerCase().replace(/\s+/g, "-");
    const describedBy = [
      description ? `${fieldId}-desc` : null,
      error ? `${fieldId}-error` : null,
    ]
      .filter(Boolean)
      .join(" ");

    return (
      <div className={cn("space-y-1.5", containerClassName)}>
        <Label htmlFor={fieldId}>{label}</Label>
        <Input
          ref={ref}
          id={fieldId}
          className={cn(error && "border-danger focus-visible:ring-danger", className)}
          aria-invalid={Boolean(error)}
          aria-describedby={describedBy || undefined}
          {...props}
        />
        {description && !error ? (
          <p id={`${fieldId}-desc`} className="text-xs text-muted-foreground">
            {description}
          </p>
        ) : null}
        {error ? (
          <p id={`${fieldId}-error`} className="text-xs text-danger" role="alert">
            {error}
          </p>
        ) : null}
      </div>
    );
  },
);
TextField.displayName = "TextField";
