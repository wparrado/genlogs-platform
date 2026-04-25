import React, { useEffect } from 'react'
import styles from './Toast.module.css'

type Props = {
  message: string
  onClose?: () => void
  duration?: number // milliseconds
}

export default function Toast({ message, onClose, duration = 5000 }: Props): React.ReactElement | null {
  useEffect(() => {
    if (!message) return
    const t = window.setTimeout(() => {
      onClose && onClose()
    }, duration)
    return () => window.clearTimeout(t)
  }, [message, duration, onClose])

  if (!message) return null

  return (
    <div className={styles.toast} role="status" aria-live="polite">
      <div className={styles.message}>{message}</div>
      <button className={styles.close} aria-label="Cerrar" onClick={() => onClose && onClose()}>×</button>
    </div>
  )
}
