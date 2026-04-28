"""Preview Panel Component
============================
Phase 5: Sales Agreements & AVS Tracking

Agreement preview with terms and conditions display.
"""

import { FileText, User, Dog, DollarSign, Shield } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"

import type { AgreementData } from "./agreement-wizard"

interface DogData {
  id: string
  name: string
  microchip: string
  breed: string
  dob: string
}

interface PreviewPanelProps {
  formData: AgreementData
  dogs: DogData[]
}

const typeLabels: Record<string, string> = {
  B2C: "Business to Consumer",
  B2B: "Business to Business",
  REHOME: "Rehoming",
}

const paymentMethodLabels: Record<string, string> = {
  CASH: "Cash",
  PAYNOW: "PayNow",
  BANK_TRANSFER: "Bank Transfer",
  CREDIT_CARD: "Credit Card",
  INSTALLMENT: "Installment",
}

// Default T&C content
const defaultTerms = `
TERMS & CONDITIONS

1. Deposit: The deposit paid is NON-REFUNDABLE except in case of breach by seller.
2. Health Guarantee: Dog is sold in good health as examined by licensed veterinarian.
3. Transfer: Ownership transfer will be processed via AVS upon full payment.
4. Returns: No returns accepted after 14 days from collection date.
5. PDPA: Buyer consents to data collection per PDPA.

SALES AGREEMENT

This agreement is made between:

SELLER: Wellfond Pet Pte Ltd
BUYER: [Buyer Name]

The seller agrees to sell and the buyer agrees to purchase the following:

DESCRIPTION: [Dog Details]
TOTAL PRICE: $[Amount] (incl. GST where applicable)
DEPOSIT: $[Deposit Amount] (Non-refundable)

By signing below, both parties agree to the terms outlined above.
`

export function PreviewPanel({ formData, dogs }: PreviewPanelProps) {
  const selectedDogs = dogs.filter(dog => formData.selectedDogs.includes(dog.id))
  const balance = formData.pricing.total - formData.pricing.deposit

  // Calculate GST
  const gstAmount = Math.round(formData.pricing.total * 9 / 109 * 100) / 100
  const subtotal = formData.pricing.total - gstAmount

  return (
    <div className="space-y-6">
      {/* Agreement Header */}
      <div className="rounded-lg border bg-card p-6">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold">Sales Agreement Preview</h3>
            <p className="text-sm text-muted-foreground">
              Type: {typeLabels[formData.type]}
            </p>
          </div>
          <Badge variant={formData.type === "REHOME" ? "secondary" : "default"}>
            {formData.type}
          </Badge>
        </div>
      </div>

      {/* Dogs Section */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Dog className="h-4 w-4" />
            Dogs
          </CardTitle>
        </CardHeader>
        <CardContent>
          {selectedDogs.length > 0 ? (
            <div className="space-y-3">
              {selectedDogs.map((dog) => (
                <div
                  key={dog.id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div>
                    <p className="font-medium">{dog.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {dog.breed} • Microchip: {dog.microchip}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No dogs selected</p>
          )}
        </CardContent>
      </Card>

      {/* Pricing Section */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <DollarSign className="h-4 w-4" />
            Pricing
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Subtotal:</span>
              <span>${subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">GST (9%):</span>
              <span>${gstAmount.toFixed(2)}</span>
            </div>
            <Separator />
            <div className="flex justify-between font-semibold">
              <span>Total:</span>
              <span>${formData.pricing.total.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm text-red-600">
              <span>Deposit (Non-refundable):</span>
              <span>-${formData.pricing.deposit.toFixed(2)}</span>
            </div>
            <Separator />
            <div className="flex justify-between font-semibold">
              <span>Balance Due:</span>
              <span>${balance.toFixed(2)}</span>
            </div>
            <div className="pt-2 text-sm text-muted-foreground">
              Payment Method: {paymentMethodLabels[formData.pricing.paymentMethod]}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Buyer Information */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <User className="h-4 w-4" />
            Buyer Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Name</p>
              <p className="font-medium">{formData.buyer.name || "-"}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Mobile</p>
              <p className="font-medium">{formData.buyer.mobile || "-"}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Email</p>
              <p className="font-medium">{formData.buyer.email || "-"}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Housing Type</p>
              <p className="font-medium">{formData.buyer.housingType}</p>
            </div>
            <div className="col-span-2">
              <p className="text-muted-foreground">Address</p>
              <p className="font-medium">{formData.buyer.address || "-"}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Terms & Conditions */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <FileText className="h-4 w-4" />
            Terms & Conditions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="max-h-60 overflow-y-auto rounded-lg bg-muted p-4 text-sm whitespace-pre-wrap">
            {defaultTerms
              .replace("[Buyer Name]", formData.buyer.name || "[Buyer Name]")
              .replace("[Dog Details]", selectedDogs.map(d => `${d.name} (${d.microchip})`).join(", ") || "[Dog Details]")
              .replace("[Amount]", formData.pricing.total.toFixed(2))
              .replace("[Deposit Amount]", formData.pricing.deposit.toFixed(2))}
          </div>
          {formData.specialConditions && (
            <div className="mt-4">
              <p className="text-sm font-medium">Special Conditions:</p>
              <p className="text-sm text-muted-foreground">{formData.specialConditions}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* PDPA Notice */}
      <Alert>
        <Shield className="h-4 w-4" />
        <AlertDescription className="text-xs">
          This agreement collects personal data in accordance with the Personal Data 
          Protection Act (PDPA) of Singapore. By proceeding, the buyer consents to 
          the collection and use of their personal information for this transaction.
        </AlertDescription>
      </Alert>
    </div>
  )
}
