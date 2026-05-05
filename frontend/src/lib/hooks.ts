import { useEffect, useRef, useState, useCallback } from 'react'

/** Scroll-triggered reveal: adds 'visible' class when element enters viewport. */
export function useReveal<T extends HTMLElement = any>(threshold = 0.15) {
  const [el, setEl] = useState<T | null>(null)
  useEffect(() => {
    if (!el) return
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { el.classList.add('visible'); obs.unobserve(el) } },
      { threshold }
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [el, threshold])
  return setEl
}

/** Animated counter: counts from 0 to `end` when element enters viewport. */
export function useCounter(end: number, duration = 1500) {
  const [value, setValue] = useState(0)
  const ref = useRef<HTMLDivElement>(null)
  const started = useRef(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && !started.current) {
        started.current = true
        const startTime = performance.now()
        const step = (now: number) => {
          const progress = Math.min((now - startTime) / duration, 1)
          const eased = 1 - Math.pow(1 - progress, 3) // ease-out cubic
          setValue(Math.round(eased * end))
          if (progress < 1) requestAnimationFrame(step)
        }
        requestAnimationFrame(step)
      }
    }, { threshold: 0.3 })
    obs.observe(el)
    return () => obs.disconnect()
  }, [end, duration])

  return { ref, value }
}

/** Scroll progress (0 to 100). */
export function useScrollProgress() {
  const [progress, setProgress] = useState(0)
  useEffect(() => {
    const handler = () => {
      const h = document.documentElement.scrollHeight - window.innerHeight
      setProgress(h > 0 ? (window.scrollY / h) * 100 : 0)
    }
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])
  return progress
}

/** Mouse position tracker for card glow effects. */
export function useMouseGlow<T extends HTMLElement = HTMLDivElement>() {
  const ref = useRef<T>(null)
  const handler = useCallback((e: MouseEvent) => {
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    el.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`)
    el.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`)
  }, [])

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.addEventListener('mousemove', handler)
    return () => el.removeEventListener('mousemove', handler)
  }, [handler])

  return ref
}
