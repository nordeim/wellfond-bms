/**
 * New Agreement Wizard Page
 * ============================
 * Phase 5: Sales Agreements & AVS Tracking
 *
 * Wizard page for creating new sales agreements.
 */

"use client"

import Link from "next/link"
import { ArrowLeft } from "lucide-react"

import { Button } from "@/components/ui/button"

import { AgreementWizard, type AgreementData } from "@/components/sales/agreement-wizard"

// Mock dogs data - replace with actual data fetching
const mockDogs = [
  {
    id: "1",
    name: "Max",
    microchip: "9000000001",
    breed: "Golden Retriever",
    dob: "2022-01-15",
  },
  {
    id: "2",
    name: "Bella",
    microchip: "9000000002",
    breed: "Labrador",
    dob: "2021-08-20",
  },
  {
    id: "3",
    name: "Charlie",
    microchip: "9000000003",
    breed: "Beagle",
    dob: "2023-03-10",
  },
  {
    id: "4",
    name: "Luna",
    microchip: "9000000004",
    breed: "Poodle",
    dob: "2022-11-05",
  },
]

export default function NewAgreementPage() {
  const handleComplete = async (data: AgreementData) => {
    // TODO: Submit to API
    console.log("Agreement data:", data)
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Redirect to agreements list
    window.location.href = "/sales"
  }

  const handleCancel = () => {
    window.location.href = "/sales"
  }

  return (
    <div className="container mx-auto max-w-4xl py-8">
      {/* Header */}
      <div className="mb-8">
        <Link href="/sales">
          <Button variant="ghost" className="mb-4 -ml-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Sales
          </Button>
        </Link>
        <h1 className="text-3xl font-bold">Create Sales Agreement</h1>
        <p className="text-muted-foreground">
          Complete all steps to create a new sales agreement
        </p>
      </div>

      {/* Wizard */}
      <AgreementWizard
        dogs={mockDogs}
        onComplete={handleComplete}
        onCancel={handleCancel}
      />
    </div>
  )
}
