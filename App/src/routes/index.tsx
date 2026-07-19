import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from '@/layouts/AppLayout'
import { DashboardPage } from '@/pages/DashboardPage'
import { ImportPage } from '@/pages/ImportPage'
import { VisualisationPage } from '@/pages/VisualisationPage'
import { EvaluationPage } from '@/pages/EvaluationPage'
import { AnomaliesPage } from '@/pages/AnomaliesPage'
import { ScorePage } from '@/pages/ScorePage'
import { HistoryPage } from '@/pages/HistoryPage'
import { IoTPage } from '@/pages/IoTPage'

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="import" element={<ImportPage />} />
          <Route path="iot" element={<IoTPage />} />
          <Route path="visualisation" element={<VisualisationPage />} />
          <Route path="evaluation" element={<EvaluationPage />} />
          <Route path="anomalies" element={<AnomaliesPage />} />
          <Route path="score" element={<ScorePage />} />
          <Route path="historique" element={<HistoryPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
