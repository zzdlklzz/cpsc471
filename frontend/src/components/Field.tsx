import type { ReactNode } from "react";

/** A label, an input (passed as children) and the error message for that field. */
export default function Field({ label, error, children }: { label: string; error?: string; children: ReactNode }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {error && <span className="field-error">{error}</span>}
    </label>
  );
}
