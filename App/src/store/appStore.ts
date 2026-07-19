import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ActiveDataset } from '@/types/trust'

interface AppState {
  selectedStationId: string | null
  selectedVariable: string
  lastMessage: string | null
  activeDataset: ActiveDataset | null
  setStation: (id: string | null) => void
  setVariable: (v: string) => void
  setMessage: (msg: string | null) => void
  setActiveDataset: (ds: ActiveDataset | null) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      selectedStationId: null,
      selectedVariable: 'temperature',
      lastMessage: null,
      activeDataset: null,
      setStation: (id) => set({ selectedStationId: id }),
      setVariable: (v) => set({ selectedVariable: v }),
      setMessage: (msg) => set({ lastMessage: msg }),
      setActiveDataset: (ds) => set({ activeDataset: ds }),
    }),
    { name: 'trust-pws-ui' },
  ),
)
