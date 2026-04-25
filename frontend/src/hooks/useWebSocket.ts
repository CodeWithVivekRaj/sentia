import { useEffect, useRef, useCallback } from 'react'
import { useSentiaStore } from '../stores/sentiaStore'
import type { WSMessage } from '../types/events'

const WS_URL = `ws://${window.location.host}/ws`
const RECONNECT_DELAY_MS = 3000

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()
  const { setConnected, setWsError, setState, pushEvent, addMessage } = useSentiaStore()

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      setWsError(null)
    }

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data)
        if (msg.type === 'state_snapshot' && msg.state) {
          setState(msg.state)
        } else if (msg.type === 'event') {
          if (msg.state) setState(msg.state)
          if (msg.data) {
            pushEvent(msg.data)
            // Sentia reaching out unprompted → inject into chat
            if (msg.data.type === 'AIInitiatedContact' && msg.data.payload?.content) {
              addMessage({
                id: msg.data.id,
                role: 'sentia',
                content: msg.data.payload.content as string,
                timestamp: msg.data.timestamp,
                emotion: msg.data.payload.emotion as string | undefined,
                initiated: true,
              })
            }
          }
        }
      } catch (e) {
        console.error('WS parse error', e)
      }
    }

    ws.onerror = () => {
      setWsError('WebSocket error')
    }

    ws.onclose = () => {
      setConnected(false)
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS)
    }
  }, [setConnected, setWsError, setState, pushEvent])

  const ping = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }))
    }
  }, [])

  useEffect(() => {
    connect()
    const pingInterval = setInterval(ping, 20000)
    return () => {
      clearInterval(pingInterval)
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect, ping])
}
