"use client";

import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

export type SelectOption = {
  label: string;
  value: string;
  disabled?: boolean;
};

type SelectFieldProps = {
  label: string;
  value?: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  description?: string;
  className?: string;
  id?: string;
  disabled?: boolean;
};

export function SelectField({
  label,
  value,
  onChange,
  options,
  placeholder = "Select…",
  description,
  className,
  id,
  disabled,
}: SelectFieldProps) {
  const fieldId = id ?? label.toLowerCase().replace(/\s+/g, "-");

  return (
    <div className={cn("space-y-1.5", className)}>
      <Label htmlFor={fieldId}>{label}</Label>
      <Select value={value} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger id={fieldId} aria-describedby={description ? `${fieldId}-desc` : undefined}>
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value} disabled={option.disabled}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {description ? (
        <p id={`${fieldId}-desc`} className="text-xs text-muted-foreground">
          {description}
        </p>
      ) : null}
    </div>
  );
}
