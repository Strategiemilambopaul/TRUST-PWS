export function formatNumber(n: number, digits = 0): string {
  return new Intl.NumberFormat('fr-FR', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(n)
}

export function formatPercent(rate: number, digits = 1): string {
  return `${formatNumber(rate * 100, digits)} %`
}

export function formatScore(score: number): string {
  return formatNumber(score, 3)
}

export function variableLabel(v: string): string {
  const map: Record<string, string> = {
    temperature: 'Température',
    humidity: 'Humidité',
    pressure: 'Pression',
  }
  return map[v] ?? v
}

export function statusColor(status: string): string {
  if (status === 'valide' || status === 'élevé') return 'bg-[var(--color-ok)]'
  if (status === 'a_verifier' || status === 'moyen') return 'bg-[var(--color-warn)]'
  return 'bg-[var(--color-danger)]'
}
