import { Badge } from '@/components/common/Badge'

export function StatusBadge({ status }: { status: string }) {
  const tone =
    status === 'valide' || status === 'élevé'
      ? 'ok'
      : status === 'a_verifier' || status === 'moyen'
        ? 'warn'
        : 'danger'
  return <Badge tone={tone}>{status}</Badge>
}
