import { useCallback, useState } from "react";
import { ApiError } from "./api/client";
import type { FieldErrors } from "./types/api";

/** Keeps the general error message and the per-field messages of one form. */
export function useFormErrors() {
  const [message, setMessage] = useState("");
  const [fields, setFields] = useState<FieldErrors>({});

  const show = useCallback((err: unknown) => {
    if (err instanceof ApiError) {
      setMessage(err.message);
      setFields(err.fields);
    } else {
      setMessage("Something went wrong.");
      setFields({});
    }
  }, []);

  const clear = useCallback(() => {
    setMessage("");
    setFields({});
  }, []);

  return { message, fields, show, clear };
}
