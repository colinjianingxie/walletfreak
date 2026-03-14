export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
};

export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('en-US').format(num);
};

export const parseDate = (dateInput: any): Date => {
  if (!dateInput) return new Date(0);
  // Firestore Timestamp object: { _seconds, _nanoseconds } or { seconds, nanoseconds }
  if (typeof dateInput === 'object' && (dateInput._seconds != null || dateInput.seconds != null)) {
    const secs = dateInput._seconds ?? dateInput.seconds ?? 0;
    return new Date(secs * 1000);
  }
  // Already a number (epoch ms or seconds)
  if (typeof dateInput === 'number') {
    return dateInput > 1e12 ? new Date(dateInput) : new Date(dateInput * 1000);
  }
  // ISO string or other string
  const d = new Date(dateInput);
  return isNaN(d.getTime()) ? new Date(0) : d;
};

export const formatDate = (dateInput: any): string => {
  const date = parseDate(dateInput);
  if (date.getTime() === 0) return '';
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
};

export const formatRelativeTime = (dateInput: any): string => {
  const date = parseDate(dateInput);
  if (date.getTime() === 0) return '';
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateInput);
};

export const truncate = (str: string, length: number): string => {
  if (str.length <= length) return str;
  return str.slice(0, length) + '...';
};
