import { useState, useEffect } from 'react'
import { Spinner } from '@heroui/react'

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
    <div className="flex flex-col items-center py-16 gap-4">
      <Spinner color="accent" />
      <p className="text-muted text-sm">{stages ? stages[index] : message}</p>
    </div>
  )
}
