import Field from "./Field";
import type { Credentials, FieldErrors } from "../types/api";

interface Props {
  value: Credentials;
  errors: FieldErrors;
  onChange: (value: Credentials) => void;
  newPassword?: boolean; // true on sign-up and Enable Member Account
}

export default function CredentialFields({ value, errors, onChange, newPassword = false }: Props) {
  return (
    <>
      <Field label="Email" error={errors.login_email}>
        <input
          type="email"
          value={value.login_email}
          onChange={(e) => onChange({ ...value, login_email: e.target.value })}
          required
          maxLength={254}
          autoComplete="username"
        />
      </Field>
      <Field label={newPassword ? "Password (at least 8 characters)" : "Password"} error={errors.password}>
        <input
          type="password"
          value={value.password}
          onChange={(e) => onChange({ ...value, password: e.target.value })}
          required
          minLength={newPassword ? 8 : undefined}
          autoComplete={newPassword ? "new-password" : "current-password"}
        />
      </Field>
    </>
  );
}
