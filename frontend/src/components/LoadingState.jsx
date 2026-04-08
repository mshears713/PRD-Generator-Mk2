import { useState, useEffect } from 'react'

export default function LoadingState({ message, stages, cycleInterval = 6000 }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    if (!stages) return
    const timer = setInterval(
      () => setIndex(i => Math.min(i + 1, stages.length - 1)),
      cycleInterval
    )
    return () => clearInterval(timer)
  }, [stages, cycleInterval])

  return (
    <div className="loading-state">
      <div className="spinner" />
      <p className="loading-message">{stages ? stages[index] : message}</p>
    </div>
  )
}
