export function relativePracticeDate(iso: string | null): string {
  if (!iso) return 'Not started yet';
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / (1000 * 60 * 60 * 24));
  if (days <= 0) return 'Last practiced today';
  if (days === 1) return 'Last practiced yesterday';
  return `Last practiced ${days} days ago`;
}

export function formatTimePracticed(totalMs: number): string {
  const minutes = Math.round(totalMs / 60_000);
  return minutes < 1 ? 'under a minute' : `${minutes} min`;
}
