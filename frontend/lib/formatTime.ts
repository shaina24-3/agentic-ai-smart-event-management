export function formatTime(value: string | null | undefined): string {
  if (!value) return "";

  const match = value.trim().match(/^(\d{1,2}):(\d{2})(?::\d{2})?\s*(AM|PM)?$/i);
  if (!match) return value;

  const hour = Number(match[1]);
  const minute = match[2];
  const marker = match[3]?.toUpperCase();

  if (Number(minute) > 59) return value;
  if (marker) {
    if (hour < 1 || hour > 12) return value;
    return `${String(hour).padStart(2, "0")}:${minute} ${marker}`;
  }
  if (hour > 23) return value;

  const period = hour < 12 ? "AM" : "PM";
  const displayHour = hour % 12 || 12;
  return `${String(displayHour).padStart(2, "0")}:${minute} ${period}`;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(date);
}