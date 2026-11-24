export interface RegistrationSummary {
  registration_id: number;
  submitted_at: string;
  status: string;
  current_placement: { status: string } | null;
}

export function filterRegistrations<T extends RegistrationSummary>(rows: T[], status: string, placement: string, sort: string): T[] {
  return rows.filter(row => (!status || row.status === status) &&
    (!placement || (placement === "none" ? row.current_placement === null : row.current_placement?.status === placement)))
    .sort((a, b) => {
      if (sort === "id-asc") return a.registration_id - b.registration_id;
      if (sort === "id-desc") return b.registration_id - a.registration_id;
      const byDate = a.submitted_at.localeCompare(b.submitted_at);
      return sort === "oldest" ? byDate || a.registration_id - b.registration_id : -byDate || b.registration_id - a.registration_id;
    });
}
