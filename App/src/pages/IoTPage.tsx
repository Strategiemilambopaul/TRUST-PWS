import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Cpu, Radio, Trash2, Wand2 } from 'lucide-react'
import { useState } from 'react'
import { Badge } from '@/components/common/Badge'
import { Card } from '@/components/common/Card'
import { StatTile } from '@/components/common/StatTile'
import {
  clearIoTBuffer,
  evaluateIoTBuffer,
  fetchIoTReadings,
  fetchIoTStatus,
  ingestIoTManual,
  simulateIoT,
} from '@/services/api'
import { useAppStore } from '@/store/appStore'
import type { EvaluateResult } from '@/types/trust'
import { formatNumber, formatScore, variableLabel } from '@/utils/format'

export function IoTPage() {
  const qc = useQueryClient()
  const setMessage = useAppStore((s) => s.setMessage)
  const setActiveDataset = useAppStore((s) => s.setActiveDataset)
  const [result, setResult] = useState<EvaluateResult | null>(null)
  const [manual, setManual] = useState({
    device_id: 'arduino-pws',
    temperature: '22.5',
    humidity: '55',
    pressure: '1013',
  })

  const statusQ = useQuery({
    queryKey: ['iot-status'],
    queryFn: fetchIoTStatus,
    refetchInterval: 2000,
  })
  const readingsQ = useQuery({
    queryKey: ['iot-readings'],
    queryFn: () => fetchIoTReadings(60),
    refetchInterval: 2000,
  })

  const refresh = () => {
    void qc.invalidateQueries({ queryKey: ['iot-status'] })
    void qc.invalidateQueries({ queryKey: ['iot-readings'] })
  }

  const simMut = useMutation({
    mutationFn: () => simulateIoT(30),
    onSuccess: (d) => {
      setMessage(`Simulation IoT : ${d.accepted} mesures ajoutées (${d.device_id}).`)
      refresh()
    },
  })

  const clearMut = useMutation({
    mutationFn: clearIoTBuffer,
    onSuccess: () => {
      setResult(null)
      setMessage('Buffer IoT vidé.')
      refresh()
    },
  })

  const evalMut = useMutation({
    mutationFn: evaluateIoTBuffer,
    onSuccess: (data) => {
      setResult(data)
      setActiveDataset({
        evaluationId: data.evaluation_id,
        filename: data.filename ?? 'iot.csv',
        dropSuspects: false,
        dropReview: false,
        nRemoved: 0,
        nObservations: data.summary.n_observations,
        trustMedian: data.summary.trust_score_median,
      })
      setMessage(data.message)
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Évaluation IoT impossible.'
      setMessage(String(detail))
    },
  })

  const manualMut = useMutation({
    mutationFn: () =>
      ingestIoTManual({
        device_id: manual.device_id || 'arduino-pws',
        temperature: manual.temperature ? Number(manual.temperature) : undefined,
        humidity: manual.humidity ? Number(manual.humidity) : undefined,
        pressure: manual.pressure ? Number(manual.pressure) : undefined,
      }),
    onSuccess: () => {
      setMessage('Mesure manuelle envoyée au buffer IoT.')
      refresh()
    },
  })

  const st = statusQ.data
  const hostHint =
    typeof window !== 'undefined' ? window.location.hostname : 'IP_DU_PC'

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-[family-name:var(--font-display)] text-3xl font-semibold">
          IoT / Arduino
        </h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Connectez un ESP32 / Arduino WiFi pour envoyer T/H/P en direct, puis évaluez la
          confiance comme pour un CSV uploadé.
        </p>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatTile
          label="Mesures en buffer"
          value={formatNumber(st?.buffer_size ?? 0)}
          hint={`max ${st?.max_points ?? 5000}`}
        />
        <StatTile
          label="Dernier appareil"
          value={st?.last_device_id ?? '—'}
          hint={st?.last_seen_at ? `vu ${st.last_seen_at}` : 'en attente'}
        />
        <StatTile
          label="Total reçu"
          value={formatNumber(st?.total_received ?? 0)}
        />
        <StatTile
          label="Prêt à évaluer"
          value={st?.ready_for_evaluation ? 'Oui' : 'Non'}
          hint={`recommandé ≥ ${st?.min_recommended ?? 12} points`}
          tone={st?.ready_for_evaluation ? 'ok' : 'warn'}
        />
      </div>

      <Card title="Connexion matérielle" subtitle="ESP32 / Arduino avec WiFi">
        <ol className="list-decimal space-y-2 pl-5 text-sm text-[var(--color-muted)]">
          <li>
            Lancez l’API en écoute réseau :
            <code className="ml-1 text-[var(--color-ink)]">
              python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
            </code>
          </li>
          <li>
            Sur le même WiFi, pointez la carte vers{' '}
            <code className="text-[var(--color-ink)]">
              http://{hostHint}:8000/iot/ingest
            </code>
          </li>
          <li>
            Utilisez le sketch{' '}
            <code className="text-[var(--color-ink)]">App/arduino/trust_pws_esp32.ino</code>
          </li>
          <li>Quand assez de points arrivent, cliquez « Évaluer le flux IoT ».</li>
        </ol>

        <div className="mt-4 rounded-lg bg-[#f3efe6] p-3 text-xs">
          <p className="font-medium text-[var(--color-ink)]">Exemple JSON (POST)</p>
          <pre className="mt-2 overflow-auto text-[11px] leading-relaxed">{`{
  "device_id": "esp32-salon",
  "temperature": 22.5,
  "humidity": 55.0,
  "pressure": 1013.2
}`}</pre>
          <p className="mt-2 text-[var(--color-muted)]">
            Variante GET :{' '}
            <code>
              /iot/ingest?device_id=esp32&t=22.5&h=55&p=1013
            </code>
          </p>
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Actions">
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-lg bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white"
              disabled={evalMut.isPending || !st?.buffer_size}
              onClick={() => evalMut.mutate()}
            >
              <Radio className="h-4 w-4" />
              {evalMut.isPending ? 'Évaluation…' : 'Évaluer le flux IoT'}
            </button>
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-line)] px-4 py-2 text-sm"
              disabled={simMut.isPending}
              onClick={() => simMut.mutate()}
            >
              <Wand2 className="h-4 w-4" />
              Simuler sans matériel
            </button>
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-danger)] px-4 py-2 text-sm text-[var(--color-danger)]"
              disabled={clearMut.isPending}
              onClick={() => clearMut.mutate()}
            >
              <Trash2 className="h-4 w-4" />
              Vider le buffer
            </button>
          </div>
          {st && !st.ready_for_evaluation && (st.buffer_size ?? 0) > 0 && (
            <p className="mt-3 text-xs text-[var(--color-warn)]">
              Buffer encore court ({st.buffer_size} points). L’évaluation reste possible dès 6
              observations, mais ≥ {st.min_recommended} est préférable.
            </p>
          )}
        </Card>

        <Card title="Envoi manuel (test navigateur)" subtitle="Sans Arduino">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <label className="col-span-2">
              <span className="text-xs text-[var(--color-muted)]">device_id</span>
              <input
                className="mt-1 w-full rounded-lg border border-[var(--color-line)] px-2 py-1.5"
                value={manual.device_id}
                onChange={(e) => setManual((m) => ({ ...m, device_id: e.target.value }))}
              />
            </label>
            {(['temperature', 'humidity', 'pressure'] as const).map((k) => (
              <label key={k}>
                <span className="text-xs text-[var(--color-muted)]">{k}</span>
                <input
                  className="mt-1 w-full rounded-lg border border-[var(--color-line)] px-2 py-1.5"
                  value={manual[k]}
                  onChange={(e) => setManual((m) => ({ ...m, [k]: e.target.value }))}
                />
              </label>
            ))}
          </div>
          <button
            type="button"
            className="mt-3 inline-flex items-center gap-2 rounded-lg border border-[var(--color-line)] px-3 py-2 text-sm"
            disabled={manualMut.isPending}
            onClick={() => manualMut.mutate()}
          >
            <Cpu className="h-4 w-4" />
            Envoyer une mesure
          </button>
        </Card>
      </div>

      <Card title="Dernières mesures reçues">
        <div className="overflow-auto">
          <table className="min-w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[var(--color-line)] text-[var(--color-muted)]">
                <th className="py-2 pr-2">Horodatage</th>
                <th className="py-2 pr-2">Appareil</th>
                <th className="py-2 pr-2">Variable</th>
                <th className="py-2">Valeur</th>
              </tr>
            </thead>
            <tbody>
              {(readingsQ.data ?? [])
                .slice()
                .reverse()
                .slice(0, 40)
                .map((r, i) => (
                  <tr key={`${r.timestamp}-${r.variable}-${i}`} className="border-b border-[var(--color-line)]">
                    <td className="py-1.5 pr-2 whitespace-nowrap">{r.timestamp}</td>
                    <td className="py-1.5 pr-2">{r.station_id}</td>
                    <td className="py-1.5 pr-2">{variableLabel(r.variable)}</td>
                    <td className="py-1.5">
                      {r.value} {r.unit}
                    </td>
                  </tr>
                ))}
              {!readingsQ.data?.length && (
                <tr>
                  <td colSpan={4} className="py-6 text-center text-[var(--color-muted)]">
                    Aucune mesure pour l’instant — simulez ou connectez un Arduino.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {result && (
        <Card title="Résultat évaluation IoT" subtitle={result.message}>
          <div className="mb-3 flex flex-wrap gap-2">
            <Badge tone="accent">source iot</Badge>
            <Badge tone="ok">score {formatScore(result.summary.trust_score_median)}</Badge>
            <Badge tone="neutral">{result.summary.n_observations} obs.</Badge>
          </div>
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
                <tr key={s.variable} className="border-b border-[var(--color-line)]">
                  <td className="py-2 pr-3">{variableLabel(s.variable)}</td>
                  <td className="py-2 pr-3 font-medium">{formatScore(s.trust_score)}</td>
                  <td className="py-2 text-xs">{s.fit_for_purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}
