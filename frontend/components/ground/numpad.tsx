"use client";

/**
 * Numpad Component
 * ================
 * Mobile-friendly numeric input pad for ground operations.
 * 48px touch targets, decimal support, clear/backspace functionality.
 *
 * @component
 * @example
 * ```tsx
 * <Numpad
 *   value={weight}
 *   onChange={setWeight}
 *   onSubmit={handleSubmit}
 *   maxLength={6}
 *   allowDecimal={true}
 * />
 * ```
 */

import { useState, useCallback } from "react";
import { Delete, RotateCcw } from "lucide-react";

interface NumpadProps {
  /** Current value */
  value: string;
  /** Callback when value changes */
  onChange: (value: string) => void;
  /** Callback when submit is pressed */
  onSubmit: () => void;
  /** Maximum length of input */
  maxLength?: number;
  /** Allow decimal point */
  allowDecimal?: boolean;
  /** Label to display above value */
  label?: string;
  /** Unit to display after value */
  unit?: string;
  /** Whether the numpad is disabled */
  disabled?: boolean;
  /** Custom className */
  className?: string;
}

export function Numpad({
  value,
  onChange,
  onSubmit,
  maxLength = 6,
  allowDecimal = true,
  label,
  unit,
  disabled = false,
  className = "",
}: NumpadProps) {
  const [hasDecimal, setHasDecimal] = useState(value.includes("."));

  /**
   * Handle number button press
   */
  const handleNumber = useCallback(
    (num: string) => {
      if (disabled) return;

      // Prevent exceeding max length
      if (value.replace(".", "").length >= maxLength && num !== ".") return;

      // Handle decimal point
      if (num === ".") {
        if (!allowDecimal || hasDecimal) return;
        setHasDecimal(true);
        onChange(value + num);
        return;
      }

      // Prevent leading zeros (unless decimal)
      if (value === "0" && num !== ".") {
        onChange(num);
        return;
      }

      onChange(value + num);
    },
    [value, onChange, maxLength, allowDecimal, hasDecimal, disabled]
  );

  /**
   * Handle clear button
   */
  const handleClear = useCallback(() => {
    if (disabled) return;
    setHasDecimal(false);
    onChange("");
  }, [onChange, disabled]);

  /**
   * Handle backspace
   */
  const handleBackspace = useCallback(() => {
    if (disabled) return;
    const newValue = value.slice(0, -1);
    setHasDecimal(newValue.includes("."));
    onChange(newValue);
  }, [value, onChange, disabled]);

  /**
   * Handle submit
   */
  const handleSubmit = useCallback(() => {
    if (disabled || !value) return;
    onSubmit();
  }, [onSubmit, value, disabled]);

  // Format display value
  const displayValue = value || "0";

  return (
    <div className={`flex flex-col gap-4 ${className}`}>
      {/* Display */}
      <div className="bg-[#1A1A1A] rounded-lg p-4 border border-[#333333]">
        {label && (
          <div className="text-[#888888] text-sm mb-1">{label}</div>
        )}
        <div className="flex items-baseline justify-between">
          <span
            className={`text-4xl font-bold ${
              value ? "text-white" : "text-[#666666]"
            }`}
            data-testid="numpad-display"
          >
            {displayValue}
          </span>
          {unit && <span className="text-[#888888] text-lg">{unit}</span>}
        </div>
      </div>

      {/* Numpad Grid */}
      <div className="grid grid-cols-3 gap-2">
        {/* Row 1: 7, 8, 9 */}
        <NumpadButton
          label="7"
          onClick={() => handleNumber("7")}
          disabled={disabled}
        />
        <NumpadButton
          label="8"
          onClick={() => handleNumber("8")}
          disabled={disabled}
        />
        <NumpadButton
          label="9"
          onClick={() => handleNumber("9")}
          disabled={disabled}
        />

        {/* Row 2: 4, 5, 6 */}
        <NumpadButton
          label="4"
          onClick={() => handleNumber("4")}
          disabled={disabled}
        />
        <NumpadButton
          label="5"
          onClick={() => handleNumber("5")}
          disabled={disabled}
        />
        <NumpadButton
          label="6"
          onClick={() => handleNumber("6")}
          disabled={disabled}
        />

        {/* Row 3: 1, 2, 3 */}
        <NumpadButton
          label="1"
          onClick={() => handleNumber("1")}
          disabled={disabled}
        />
        <NumpadButton
          label="2"
          onClick={() => handleNumber("2")}
          disabled={disabled}
        />
        <NumpadButton
          label="3"
          onClick={() => handleNumber("3")}
          disabled={disabled}
        />

        {/* Row 4: C, 0, . */}
        <NumpadButton
          label={<RotateCcw className="w-6 h-6" />}
          onClick={handleClear}
          variant="secondary"
          disabled={disabled}
          aria-label="Clear"
        />
        <NumpadButton
          label="0"
          onClick={() => handleNumber("0")}
          disabled={disabled}
        />
        <NumpadButton
          label="."
          onClick={() => handleNumber(".")}
          disabled={disabled || !allowDecimal || hasDecimal}
          aria-label="Decimal point"
        />

        {/* Row 5: Backspace, Submit */}
        <NumpadButton
          label={<Delete className="w-6 h-6" />}
          onClick={handleBackspace}
          variant="secondary"
          disabled={disabled || !value}
          className="col-span-1"
          aria-label="Backspace"
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !value}
          className={`
            col-span-2 h-14 rounded-lg font-semibold text-lg
            transition-all duration-200 active:scale-95
            min-h-[48px] min-w-[48px]
            flex items-center justify-center gap-2
            ${
              disabled || !value
                ? "bg-[#333333] text-[#666666] cursor-not-allowed"
                : "bg-[#F37022] text-white hover:bg-[#E56012] active:bg-[#D55002]"
            }
          `}
          aria-label="Submit"
        >
          Submit
        </button>
      </div>
    </div>
  );
}

interface NumpadButtonProps {
  label: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  variant?: "primary" | "secondary";
  className?: string;
  "aria-label"?: string;
}

function NumpadButton({
  label,
  onClick,
  disabled = false,
  variant = "primary",
  className = "",
  "aria-label": ariaLabel,
}: NumpadButtonProps) {
  const baseStyles = `
    h-14 rounded-lg font-semibold text-xl
    transition-all duration-200 active:scale-95
    min-h-[48px] min-w-[48px]
    flex items-center justify-center
    touch-manipulation
    select-none
  `;

  const variantStyles =
    variant === "secondary"
      ? disabled
        ? "bg-[#2A2A2A] text-[#555555] cursor-not-allowed"
        : "bg-[#2A2A2A] text-[#AAAAAA] hover:bg-[#333333] active:bg-[#444444]"
      : disabled
      ? "bg-[#1A1A1A] text-[#555555] cursor-not-allowed border border-[#333333]"
      : "bg-[#1A1A1A] text-white border border-[#444444] hover:bg-[#2A2A2A] active:bg-[#333333]";

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyles} ${variantStyles} ${className}`}
      aria-label={ariaLabel}
      type="button"
    >
      {label}
    </button>
  );
}
