import { createContext, useContext, useMemo, useRef, useState, type ReactNode } from 'react'

interface SimulationProfileValue {
  failNextChat: boolean
  failNextUpload: boolean
  setFailNextChat: (value: boolean) => void
  setFailNextUpload: (value: boolean) => void
  consumeUploadFailure: () => boolean
  consumeChatFailure: () => boolean
}

const SimulationProfileContext = createContext<SimulationProfileValue | null>(null)

export function SimulationProfileProvider({ children }: { children: ReactNode }) {
  const [failNextChat, setFailNextChatState] = useState(false)
  const [failNextUpload, setFailNextUploadState] = useState(false)
  const failNextChatRef = useRef(false)
  const failNextUploadRef = useRef(false)

  const setFailNextChat = (value: boolean) => {
    failNextChatRef.current = value
    setFailNextChatState(value)
  }

  const setFailNextUpload = (value: boolean) => {
    failNextUploadRef.current = value
    setFailNextUploadState(value)
  }

  const value = useMemo<SimulationProfileValue>(() => ({
    failNextChat,
    failNextUpload,
    setFailNextChat,
    setFailNextUpload,
    consumeUploadFailure() {
      if (!failNextUploadRef.current) return false
      failNextUploadRef.current = false
      setFailNextUploadState(false)
      return true
    },
    consumeChatFailure() {
      if (!failNextChatRef.current) return false
      failNextChatRef.current = false
      setFailNextChatState(false)
      return true
    },
  }), [failNextChat, failNextUpload])

  return <SimulationProfileContext.Provider value={value}>{children}</SimulationProfileContext.Provider>
}

export function useSimulationProfile() {
  const value = useContext(SimulationProfileContext)
  if (!value) throw new Error('useSimulationProfile must be used within SimulationProfileProvider')
  return value
}
