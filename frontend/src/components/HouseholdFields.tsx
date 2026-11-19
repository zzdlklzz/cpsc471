import Field from "./Field";
import type { FieldErrors, HouseholdInput, Zone } from "../types/api";

interface Props {
  value: HouseholdInput;
  zones: Zone[];
  errors: FieldErrors;
  onChange: (value: HouseholdInput) => void;
}

/** Address and zone inputs. Used by the sign-up form and the Edit Household form. */
export default function HouseholdFields({ value, zones, errors, onChange }: Props) {
  const set = (field: keyof HouseholdInput, v: string | number) => onChange({ ...value, [field]: v });
  return (
    <>
      <Field label="Street" error={errors.street}>
        <input value={value.street} onChange={(e) => set("street", e.target.value)} required maxLength={255} />
      </Field>
      <Field label="City" error={errors.city}>
        <input value={value.city} onChange={(e) => set("city", e.target.value)} required maxLength={100} />
      </Field>
      <Field label="Province" error={errors.province}>
        <input value={value.province} onChange={(e) => set("province", e.target.value)} required maxLength={100} />
      </Field>
      <Field label="Postal code" error={errors.postal_code}>
        <input value={value.postal_code} onChange={(e) => set("postal_code", e.target.value)} required maxLength={20} />
      </Field>
      <Field label="Evacuation zone" error={errors.zone_id}>
        <select value={value.zone_id || ""} onChange={(e) => set("zone_id", Number(e.target.value))} required>
          <option value="" disabled>
            Choose a zone
          </option>
          {zones.map((z) => (
            <option key={z.zone_id} value={z.zone_id}>
              {z.zone_name}
            </option>
          ))}
        </select>
      </Field>
    </>
  );
}
