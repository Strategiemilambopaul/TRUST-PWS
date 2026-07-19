import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Download } from 'lucide-react'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { Modal } from '@/components/common/Modal'
import { StatTile } from '@/components/common/StatTile'
import { StatusBadge } from '@/components/quality/StatusBadge'
import { RadarDimensions } from '@/components/charts/RadarDimensions'
import {
  cleanEvaluation,
  downloadEvaluationExport,
  previewImport,
  runEvaluate,
} from '@/services/api'
import { useAppStore } from '@/store/appStore'
import type { EvaluateResult, ImportPreview } from '@/types/trust'
import { formatNumber, formatPercent, formatScore, variableLabel } from '@/utils/format'

function apiErrorDetail(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data
    ?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (typeof d === 'object' && d && 'msg' in d ? String(d.msg) : String(d)))
      .join('\n')
  }
  return 'Format invalide ou fichier illisible.'
}

async function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

const schema = z.object({
  file: z
    .custom<FileList>((v) => v instanceof FileList && v.length > 0, 'Fichier requis')
    .refine((files) => {
      const name = files[0]?.name.toLowerCase() ?? ''
      return name.endsWith('.csv') || name.endsWith('.json')
    }, 'Formats acceptés: CSV ou JSON'),
})

type FormValues = z.infer<typeof schema>

export function ImportPage() {
  const setMessage = useAppStore((s) => s.setMessage)
  const setActiveDataset = useAppStore((s) => s.setActiveDataset)
  const activeDataset = useAppStore((s) => s.activeDataset)

  const [preview, setPreview] = useState<ImportPreview | null>(null)
  const [result, setResult] = useState<EvaluateResult | null>(null)
  const [formatModal, setFormatModal] = useState<{ open: boolean; message: string }>({
    open: false,
    message: '',
  })
  const [cleanModal, setCleanModal] = useState(false)
  const [alsoDropReview, setAlsoDropReview] = useState(false)

  const form = useForm<FormValues>({ resolver: zodResolver(schema) })

  const openFormatModal = (message: string) => {
    setFormatModal({ open: true, message })
    setMessage(message.split('\n')[0] ?? message)
  }

  const markActive = (data: EvaluateResult) => {
    if (data.source !== 'upload' || !data.can_export) return
    setActiveDataset({
      evaluationId: data.evaluation_id,
      filename: data.filename ?? 'dataset.csv',
      dropSuspects: data.drop_suspects_applied,
      dropReview: data.drop_review_applied,
      nRemoved: data.n_removed,
      nObservations: data.summary.n_observations,
      trustMedian: data.summary.trust_score_median,
    })
  }

  const previewMut = useMutation({
    mutationFn: async (file: File) => previewImport(file),
    onSuccess: (data) => {
      setPreview(data)
      setResult(null)
      if (!data.format_ok) {
        openFormatModal(
          data.error_message ??
            data.warnings[0] ??
            'Le format du fichier n’est pas respecté.',
        )
      }
    },
    onError: (err: unknown) => {
      setPreview(null)
      openFormatModal(apiErrorDetail(err))
    },
  })

  const evalMut = useMutation({
    mutationFn: async (file: File) => runEvaluate(file),
    onSuccess: (data) => {
      if (!data.format_ok) {
        setResult(null)
        openFormatModal(
          data.warnings[0] ?? data.message ?? 'Le format du fichier n’est pas respecté.',
        )
        return
      }
      setResult(data)
      setMessage(data.message)
      if (data.n_suspecte > 0 || data.n_a_verifier > 0) {
        setAlsoDropReview(false)
        setCleanModal(true)
      } else {
        markActive(data)
      }
    },
    onError: (err: unknown) => {
      setResult(null)
      openFormatModal(apiErrorDetail(err))
    },
  })

  const cleanMut = useMutation({
    mutationFn: async (opts: { drop_suspects: boolean; drop_review: boolean }) => {
      if (!result) throw new Error('Aucune évaluation')
      return cleanEvaluation(result.evaluation_id, opts)
    },
    onSuccess: (data) => {
      setResult(data)
      markActive(data)
      setCleanModal(false)
      setMessage(data.message)
    },
    onError: (err: unknown) => {
      openFormatModal(apiErrorDetail(err))
    },
  })

  const exportMut = useMutation({
    mutationFn: async (opts: { drop_suspects: boolean; drop_review: boolean }) => {
      if (!result) throw new Error('Aucune évaluation')
      const blob = await downloadEvaluationExport(result.evaluation_id, opts)
      const base = (result.filename ?? 'dataset').replace(/\.(csv|json)$/i, '')
      const suffix = opts.drop_suspects || opts.drop_review ? '_nettoye' : '_normalise'
      await triggerDownload(blob, `${base}${suffix}.csv`)
      return opts
    },
    onSuccess: (opts) => {
      setMessage(
        opts.drop_suspects
          ? 'Export CSV nettoyé (format long normalisé) téléchargé.'
          : 'Export CSV normalisé téléchargé.',
      )
    },
    onError: (err: unknown) => openFormatModal(apiErrorDetail(err)),
  })

  const onInvalid = (errors: typeof form.formState.errors) => {
    openFormatModal(
      errors.file?.message ?? 'Formats de fichier acceptés : CSV ou JSON uniquement.',
    )
  }

  const onPreview = form.handleSubmit(async (values) => {
    await previewMut.mutateAsync(values.file[0])
  }, onInvalid)

  const onEvaluate = form.handleSubmit(async (values) => {
    await evalMut.mutateAsync(values.file[0])
  }, onInvalid)

  const keepAllAndUse = () => {
    if (result) markActive(result)
    setCleanModal(false)
    setMessage('Dataset conservé avec toutes les observations (y compris suspectes).')
  }

  const firstSeries = result?.series[0]

  return (
    <div className="space-y-6">
      <Modal
        open={formatModal.open}
        title="Format non respecté"
        tone="danger"
        onClose={() => setFormatModal({ open: false, message: '' })}
      >
        <p className="whitespace-pre-line">{formatModal.message}</p>
        <div className="mt-4 rounded-lg bg-[#f3efe6] px-3 py-2 text-xs text-[var(--color-muted)]">
          <p className="font-medium text-[var(--color-ink)]">Rappel des formats</p>
          <p className="mt-1">
            Long : <code>timestamp, value, phenomenon|variable [, unit]</code>
          </p>
          <p>
            Large : <code>timestamp, temperature, humidity, pressure</code>
          </p>
        </div>
      </Modal>

      <Modal
        open={cleanModal && !!result}
        title="Valeurs suspectes détectées"
        tone="warn"
        closeOnBackdrop={false}
        onClose={keepAllAndUse}
        footer={
          <>
            <button
              type="button"
              className="rounded-lg border border-[var(--color-line)] px-4 py-2 text-sm"
              onClick={keepAllAndUse}
              disabled={cleanMut.isPending}
            >
              Garder tout
            </button>
            <button
              type="button"
              className="rounded-lg bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white"
              disabled={cleanMut.isPending || !result || result.n_suspecte === 0}
              onClick={() =>
                cleanMut.mutate({
                  drop_suspects: true,
                  drop_review: alsoDropReview,
                })
              }
            >
              {cleanMut.isPending ? 'Nettoyage…' : 'Supprimer les suspectes et utiliser'}
            </button>
          </>
        }
      >
        {result && (
          <>
            <p>
              Le système a détecté{' '}
              <strong>{formatNumber(result.n_suspecte)}</strong> observation(s){' '}
              <strong>suspecte(s)</strong>
              {result.n_a_verifier > 0 && (
                <>
                  {' '}
                  et <strong>{formatNumber(result.n_a_verifier)}</strong> à vérifier
                </>
              )}{' '}
              sur {formatNumber(result.summary.n_observations)} au total.
            </p>
            <p className="mt-3 text-[var(--color-muted)]">
              Souhaitez-vous les retirer avant d’utiliser / exporter le dataset au format
              normalisé du cadre (timestamp, station, variable, value, unit) ?
            </p>
            {result.n_a_verifier > 0 && (
              <label className="mt-4 flex items-start gap-2 text-sm">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={alsoDropReview}
                  onChange={(e) => setAlsoDropReview(e.target.checked)}
                />
                <span>
                  Retirer aussi les observations « à vérifier » ({result.n_a_verifier})
                </span>
              </label>
            )}
          </>
        )}
      </Modal>

      <header>
        <h1 className="font-[family-name:var(--font-display)] text-3xl font-semibold">
          Importation des données
        </h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Uploadez le CSV/JSON de votre station. L’API vérifie le format, calcule QC et
          confiance, puis vous propose d’exporter un dataset normalisé (avec ou sans
          valeurs suspectes).
        </p>
      </header>

      {activeDataset && (
        <Card title="Dataset actif">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <Badge tone="ok">en cours d’utilisation</Badge>
            <span className="font-medium">{activeDataset.filename}</span>
            <span className="text-[var(--color-muted)]">
              {formatNumber(activeDataset.nObservations)} obs. · score médian{' '}
              {formatScore(activeDataset.trustMedian)}
            </span>
            {activeDataset.dropSuspects && <Badge tone="accent">suspectes retirées</Badge>}
            {activeDataset.dropReview && <Badge tone="warn">à vérifier retirées</Badge>}
            {activeDataset.nRemoved > 0 && (
              <span className="text-xs text-[var(--color-muted)]">
                ({activeDataset.nRemoved} retirée(s))
              </span>
            )}
          </div>
        </Card>
      )}

      <Card title="Charger un fichier de station">
        <form className="space-y-4" onSubmit={onPreview}>
          <input
            type="file"
            accept=".csv,.json,text/csv,application/json"
            className="block w-full text-sm"
            {...form.register('file')}
          />
          {form.formState.errors.file && (
            <p className="text-sm text-[var(--color-danger)]">
              {form.formState.errors.file.message}
            </p>
          )}
          <p className="text-xs text-[var(--color-muted)]">
            Formats acceptés — long:{' '}
            <code>timestamp, value, phenomenon|variable [, unit]</code> ; large:{' '}
            <code>timestamp, temperature, humidity, pressure</code>
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="submit"
              className="rounded-lg border border-[var(--color-line)] px-4 py-2 text-sm"
              disabled={previewMut.isPending}
            >
              {previewMut.isPending ? 'Analyse…' : 'Vérifier le format'}
            </button>
            <button
              type="button"
              className="rounded-lg bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white"
              onClick={onEvaluate}
              disabled={evalMut.isPending}
            >
              {evalMut.isPending ? 'Évaluation…' : 'Évaluer ce dataset'}
            </button>
          </div>
        </form>
      </Card>

      {preview && (
        <Card
          title="Contrôle de format"
          subtitle={`${preview.n_rows} lignes · ${preview.columns.length} colonnes`}
        >
          <div className="mb-3 flex flex-wrap gap-2">
            {preview.detected_variables.map((v) => (
              <Badge key={v} tone="accent">
                {v}
              </Badge>
            ))}
            {preview.format_ok ? (
              <Badge tone="ok">Format OK</Badge>
            ) : (
              <Badge tone="danger">Format invalide</Badge>
            )}
          </div>
          {!preview.format_ok && (
            <p className="mb-3 text-sm text-[var(--color-danger)]">
              Ce fichier ne peut pas être évalué tant que le schéma n’est pas corrigé.
            </p>
          )}
          <div className="overflow-auto rounded-lg border border-[var(--color-line)]">
            <table className="min-w-full text-left text-xs">
              <thead className="bg-[#f3efe6]">
                <tr>
                  {preview.columns.map((c) => (
                    <th key={c} className="px-2 py-2 font-medium">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.sample.map((row, i) => (
                  <tr key={i} className="border-t border-[var(--color-line)]">
                    {preview.columns.map((c) => (
                      <td key={c} className="px-2 py-1.5 whitespace-nowrap">
                        {String(row[c] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {result && (
        <>
          <Card title="Résultat de l’évaluation" subtitle={result.message}>
            <div className="mb-4 flex flex-wrap gap-2">
              <Badge tone="ok">format OK</Badge>
              <Badge tone="accent">
                {result.source === 'upload' ? 'fichier uploadé' : 'corpus'}
              </Badge>
              {result.filename && <Badge tone="neutral">{result.filename}</Badge>}
              {result.drop_suspects_applied && (
                <Badge tone="ok">suspectes retirées</Badge>
              )}
            </div>

            {result.can_export && (
              <div className="mb-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-line)] px-3 py-2 text-sm"
                  disabled={exportMut.isPending}
                  onClick={() =>
                    exportMut.mutate({
                      drop_suspects: result.drop_suspects_applied,
                      drop_review: result.drop_review_applied,
                    })
                  }
                >
                  <Download className="h-4 w-4" />
                  Exporter le dataset normalisé
                </button>
                {(result.n_suspecte > 0 || result.n_a_verifier > 0) &&
                  !result.drop_suspects_applied && (
                    <button
                      type="button"
                      className="rounded-lg border border-[var(--color-warn)] px-3 py-2 text-sm text-[var(--color-warn)]"
                      onClick={() => setCleanModal(true)}
                    >
                      Gérer les valeurs suspectes…
                    </button>
                  )}
              </div>
            )}

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <StatTile
                label="Observations QC"
                value={formatNumber(result.summary.n_observations)}
              />
              <StatTile
                label="Score médian"
                value={formatScore(result.summary.trust_score_median)}
                hint={`Qualité ${result.summary.quality_label}`}
              />
              <StatTile
                label="Valides"
                value={formatPercent(
                  result.summary.n_valide / Math.max(result.summary.n_observations, 1),
                )}
              />
              <StatTile
                label="Suspectes"
                value={formatPercent(
                  result.summary.n_suspecte / Math.max(result.summary.n_observations, 1),
                )}
              />
            </div>
          </Card>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card title="Scores par série">
              <div className="overflow-auto">
                <table className="min-w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-line)] text-xs text-[var(--color-muted)]">
                      <th className="py-2 pr-3">Variable</th>
                      <th className="py-2 pr-3">Score</th>
                      <th className="py-2">Fit-for-purpose</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.series.map((s) => (
                      <tr
                        key={`${s.station_id}-${s.variable}`}
                        className="border-b border-[var(--color-line)]"
                      >
                        <td className="py-2 pr-3">{variableLabel(s.variable)}</td>
                        <td className="py-2 pr-3 font-medium">
                          {formatScore(s.trust_score)}
                        </td>
                        <td className="py-2 text-xs">{s.fit_for_purpose}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
            {firstSeries && (
              <Card
                title="Profil des dimensions"
                subtitle={variableLabel(firstSeries.variable)}
              >
                <RadarDimensions series={firstSeries} />
              </Card>
            )}
          </div>

          {result.anomalies.length > 0 && (
            <Card
              title="Anomalies détectées"
              subtitle={`${result.anomalies.length} premières observations signalées`}
            >
              <div className="overflow-auto">
                <table className="min-w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-[var(--color-line)] text-[var(--color-muted)]">
                      <th className="py-2 pr-2">Horodatage</th>
                      <th className="py-2 pr-2">Variable</th>
                      <th className="py-2 pr-2">Valeur</th>
                      <th className="py-2 pr-2">Statut</th>
                      <th className="py-2">Types</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.anomalies.slice(0, 25).map((a, i) => (
                      <tr
                        key={`${a.timestamp}-${i}`}
                        className="border-b border-[var(--color-line)]"
                      >
                        <td className="py-1.5 pr-2 whitespace-nowrap">{a.timestamp}</td>
                        <td className="py-1.5 pr-2">{variableLabel(a.variable)}</td>
                        <td className="py-1.5 pr-2">{a.value_std ?? '—'}</td>
                        <td className="py-1.5 pr-2">
                          <StatusBadge status={a.qc_status} />
                        </td>
                        <td className="py-1.5">{a.anomaly_types.join(', ')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
