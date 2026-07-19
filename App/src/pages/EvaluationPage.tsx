import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { CheckCircle2, Circle } from 'lucide-react'
import { Card } from '@/components/common/Card'
import { fetchPipelineSteps } from '@/services/api'
import { cn } from '@/utils/cn'

export function EvaluationPage() {
  const steps = useQuery({ queryKey: ['pipeline'], queryFn: fetchPipelineSteps })

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-[family-name:var(--font-display)] text-3xl font-semibold">
          Évaluation de la confiance
        </h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Les 8 étapes du cadre méthodologique, alimentées par les exports
          scientifiques (pas de calcul métier dans React).
        </p>
      </header>

      <div className="space-y-3">
        {(steps.data ?? []).map((step, idx) => (
          <motion.div
            key={step.key}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.04 }}
          >
            <Card>
              <div className="flex items-start gap-3">
                <div
                  className={cn(
                    'mt-0.5 rounded-full p-1',
                    step.status === 'done'
                      ? 'text-[var(--color-ok)]'
                      : 'text-[var(--color-muted)]',
                  )}
                >
                  {step.status === 'done' ? (
                    <CheckCircle2 className="h-5 w-5" />
                  ) : (
                    <Circle className="h-5 w-5" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-baseline gap-2">
                    <span className="text-xs font-semibold tracking-wide text-[var(--color-muted)]">
                      ÉTAPE {step.step}
                    </span>
                    <h2 className="font-[family-name:var(--font-display)] text-lg font-semibold">
                      {step.title}
                    </h2>
                  </div>
                  <p className="mt-1 text-sm text-[var(--color-muted)]">{step.description}</p>
                  <pre className="mt-3 overflow-auto rounded-lg bg-[#f3efe6] p-3 text-xs">
                    {JSON.stringify(step.metrics, null, 2)}
                  </pre>
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      {steps.isError && (
        <p className="text-sm text-[var(--color-danger)]">
          Impossible de charger les étapes. Vérifiez que l’API tourne.
        </p>
      )}
    </div>
  )
}
