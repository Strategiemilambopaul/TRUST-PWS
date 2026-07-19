import { NavLink, Outlet } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  Cpu,
  Gauge,
  History,
  LayoutDashboard,
  LineChart,
  Upload,
  Workflow,
} from 'lucide-react'
import { APP_NAME, APP_SUBTITLE } from '@/constants/pipeline'
import { cn } from '@/utils/cn'
import { useAppStore } from '@/store/appStore'

const links = [
  { to: '/', label: 'Tableau de bord', icon: LayoutDashboard },
  { to: '/import', label: 'Import', icon: Upload },
  { to: '/iot', label: 'IoT / Arduino', icon: Cpu },
  { to: '/visualisation', label: 'Visualisation', icon: LineChart },
  { to: '/evaluation', label: 'Évaluation', icon: Workflow },
  { to: '/anomalies', label: 'Anomalies', icon: AlertTriangle },
  { to: '/score', label: 'Score', icon: Gauge },
  { to: '/historique', label: 'Historique', icon: History },
]

export function AppLayout() {
  const message = useAppStore((s) => s.lastMessage)
  const activeDataset = useAppStore((s) => s.activeDataset)

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="border-b border-[var(--color-line)] bg-[#122028] text-[#f3efe6] lg:min-h-screen lg:border-b-0 lg:border-r lg:border-[#24343f]">
        <div className="px-5 py-6">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-[#8fd0b8]" />
            <span className="font-[family-name:var(--font-display)] text-xl font-semibold">
              {APP_NAME}
            </span>
          </div>
          <p className="mt-2 text-xs leading-relaxed text-[#9aa8b3]">{APP_SUBTITLE}</p>
          {activeDataset && (
            <p className="mt-3 rounded-lg bg-[#1b2a33] px-3 py-2 text-[11px] leading-snug text-[#8fd0b8]">
              Dataset actif : {activeDataset.filename}
              {activeDataset.dropSuspects ? ' (nettoyé)' : ''}
            </p>
          )}
        </div>
        <nav className="flex gap-1 overflow-x-auto px-3 pb-4 lg:flex-col lg:overflow-visible">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2 rounded-lg px-3 py-2 text-sm whitespace-nowrap transition',
                  isActive
                    ? 'bg-[#1f6f5b] text-white'
                    : 'text-[#c9d3da] hover:bg-[#1b2a33] hover:text-white',
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="min-w-0">
        {message && (
          <div className="border-b border-[var(--color-line)] bg-[var(--color-accent-soft)] px-4 py-2 text-sm text-[var(--color-accent)]">
            {message}
          </div>
        )}
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
