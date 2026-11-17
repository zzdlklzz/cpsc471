import Field from "./Field";
import type { FieldErrors, MemberInput } from "../types/api";

interface Props {
  value: MemberInput;
  errors: FieldErrors;
  onChange: (value: MemberInput) => void;
}

/** Name, date of birth and optional phone. Used by sign-up and Add / Edit Member. */
export default function MemberFields({ value, errors, onChange }: Props) {
  const set = (field: keyof MemberInput, v: string) => onChange({ ...value, [field]: v });
  return (
    <>
      <Field label="First name" error={errors.first_name}>
        <input value={value.first_name} onChange={(e) => set("first_name", e.target.value)} required maxLength={100} />
      </Field>
      <Field label="Last name" error={errors.last_name}>
        <input value={value.last_name} onChange={(e) => set("last_name", e.target.value)} required maxLength={100} />
      </Field>
      <Field label="Date of birth" error={errors.date_of_birth}>
        <input type="date" value={value.date_of_birth} onChange={(e) => set("date_of_birth", e.target.value)} required />
      </Field>
      <Field label="Phone number (optional)" error={errors.phone_number}>
        <input value={value.phone_number} onChange={(e) => set("phone_number", e.target.value)} maxLength={30} />
      </Field>
    </>
  );
}
