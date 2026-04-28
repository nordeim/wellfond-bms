/**
 * Signature Pad Component
 * ============================
 * Phase 5: Sales Agreements & AVS Tracking
 *
 * Electronic signature capture using HTML5 Canvas.
 * Captures signature data as base64 image.
 */

"use client"

import { useRef, useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Eraser, Check, Undo } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

interface SignaturePadProps {
  onSignature: (signatureData: string) => void
  width?: number
  height?: number
}

export function SignaturePad({ 
  onSignature, 
  width = 400, 
  height = 200 
}: SignaturePadProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [hasSignature, setHasSignature] = useState(false)
  const [strokes, setStrokes] = useState<ImageData[]>([])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    // Set canvas size for high DPI displays
    const dpr = window.devicePixelRatio || 1
    
    canvas.width = width * dpr
    canvas.height = height * dpr
    
    const ctx = canvas.getContext("2d")
    if (ctx) {
      ctx.scale(dpr, dpr)
      ctx.strokeStyle = "#000"
      ctx.lineWidth = 2
      ctx.lineCap = "round"
      ctx.lineJoin = "round"
    }
  }, [width, height])

  const getCoordinates = (e: React.MouseEvent | React.TouchEvent) => {
    const canvas = canvasRef.current
    if (!canvas) return { x: 0, y: 0 }

    const rect = canvas.getBoundingClientRect()
    let clientX, clientY

    if ("touches" in e) {
      clientX = e.touches[0].clientX
      clientY = e.touches[0].clientY
    } else {
      clientX = (e as React.MouseEvent).clientX
      clientY = (e as React.MouseEvent).clientY
    }

    return {
      x: clientX - rect.left,
      y: clientY - rect.top,
    }
  }

  const startDrawing = (e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault()
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // Save current state before new stroke
    const currentData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    setStrokes(prev => [...prev, currentData])

    const { x, y } = getCoordinates(e)
    ctx.beginPath()
    ctx.moveTo(x, y)
    setIsDrawing(true)
  }

  const draw = (e: React.MouseEvent | React.TouchEvent) => {
    if (!isDrawing) return
    e.preventDefault()

    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const { x, y } = getCoordinates(e)
    ctx.lineTo(x, y)
    ctx.stroke()
  }

  const stopDrawing = () => {
    if (!isDrawing) return
    setIsDrawing(false)
    setHasSignature(true)

    const canvas = canvasRef.current
    if (canvas) {
      const signatureData = canvas.toDataURL("image/png")
      onSignature(signatureData)
    }
  }

  const clearSignature = () => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    ctx.clearRect(0, 0, canvas.width, canvas.height)
    setHasSignature(false)
    setStrokes([])
    onSignature("")
  }

  const undoLastStroke = () => {
    if (strokes.length === 0) return

    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const previousStroke = strokes[strokes.length - 1]
    ctx.putImageData(previousStroke, 0, 0)
    setStrokes(prev => prev.slice(0, -1))

    if (strokes.length === 1) {
      setHasSignature(false)
      onSignature("")
    } else {
      const signatureData = canvas.toDataURL("image/png")
      onSignature(signatureData)
    }
  }

  return (
    <div className="space-y-4">
      <Card className="relative overflow-hidden border-2 border-dashed border-muted-foreground/25 bg-muted/50">
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          className="touch-none cursor-crosshair"
          style={{ width: `${width}px`, height: `${height}px` }}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
        />
        {!hasSignature && (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <span className="text-sm text-muted-foreground">
              Sign here
            </span>
          </div>
        )}
      </Card>

      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={undoLastStroke}
            disabled={strokes.length === 0}
          >
            <Undo className="mr-1 h-4 w-4" />
            Undo
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={clearSignature}
            disabled={!hasSignature}
          >
            <Eraser className="mr-1 h-4 w-4" />
            Clear
          </Button>
        </div>

        {hasSignature && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-2 text-sm text-green-600"
          >
            <Check className="h-4 w-4" />
            <span>Signature captured</span>
          </motion.div>
        )}
      </div>

      <p className="text-xs text-muted-foreground">
        By signing, you agree to the terms and conditions of this agreement.
      </p>
    </div>
  )
}
