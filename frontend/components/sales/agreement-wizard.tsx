/**
 * Agreement Wizard Component
 * ==============================
 * Phase 5: Sales Agreements & AVS Tracking
 *
 * 5-step wizard for creating sales agreements:
 * 1. Select agreement type (B2C/B2B/Rehoming)
 * 2. Select dogs and pricing
 * 3. Enter buyer information
 * 4. Review and sign
 * 5. Send to buyer
 */

"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { 
  FileText, 
  Dog, 
  User, 
  PenTool, 
  Send,
  ChevronRight,
  ChevronLeft,
  Check,
  AlertTriangle
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Alert, AlertDescription } from "@/components/ui/alert"

import { SignaturePad } from "./signature-pad"
import { PreviewPanel } from "./preview-panel"

interface DogData {
  id: string
  name: string
  microchip: string
  breed: string
  dob: string
}

interface AgreementWizardProps {
  dogs: DogData[]
  onComplete: (data: AgreementData) => void
  onCancel: () => void
}

export interface AgreementData {
  type: "B2C" | "B2B" | "REHOME"
  selectedDogs: string[]
  pricing: {
    total: number
    deposit: number
    paymentMethod: string
  }
  buyer: {
    name: string
    mobile: string
    email: string
    address: string
    housingType: string
    nric?: string
  }
  specialConditions: string
  sellerSignature?: string | undefined
}

const steps = [
  { id: 1, title: "Type", icon: FileText },
  { id: 2, title: "Dogs & Price", icon: Dog },
  { id: 3, title: "Buyer Info", icon: User },
  { id: 4, title: "Review & Sign", icon: PenTool },
  { id: 5, title: "Send", icon: Send },
]

const housingTypes = [
  { value: "HDB", label: "HDB", warning: true },
  { value: "CONDO", label: "Condominium" },
  { value: "LANDED", label: "Landed Property" },
  { value: "PRIVATE", label: "Private" },
  { value: "OTHER", label: "Other" },
]

const paymentMethods = [
  { value: "CASH", label: "Cash" },
  { value: "PAYNOW", label: "PayNow" },
  { value: "BANK_TRANSFER", label: "Bank Transfer" },
  { value: "CREDIT_CARD", label: "Credit Card" },
  { value: "INSTALLMENT", label: "Installment" },
]

// Large breeds that trigger HDB warning
const largeBreeds = [
  "Golden Retriever",
  "Labrador Retriever", 
  "German Shepherd",
  "Rottweiler",
  "Doberman",
  "Chow Chow",
  "Husky",
  "Malamute",
  "Saint Bernard",
  "Great Dane",
  "Mastiff",
  "Bernese Mountain Dog",
]

export function AgreementWizard({ dogs, onComplete, onCancel }: AgreementWizardProps) {
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState<AgreementData>({
    type: "B2C",
    selectedDogs: [],
    pricing: {
      total: 0,
      deposit: 0,
      paymentMethod: "CASH",
    },
    buyer: {
      name: "",
      mobile: "",
      email: "",
      address: "",
      housingType: "HDB",
    },
    specialConditions: "",
    sellerSignature: undefined as string | undefined,
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Check if HDB warning should be shown
  const showHDBWarning = formData.buyer.housingType === "HDB" && 
    formData.selectedDogs.some(dogId => {
      const dog = dogs.find(d => d.id === dogId)
      return dog && largeBreeds.some(breed => 
        dog.breed.toLowerCase().includes(breed.toLowerCase())
      )
    })

  // Calculate GST (9% of total)
  const gstAmount = Math.round(formData.pricing.total * 9 / 109 * 100) / 100
  const subtotal = formData.pricing.total - gstAmount

  const updateFormData = (updates: Partial<AgreementData>) => {
    setFormData(prev => ({ ...prev, ...updates }))
  }

  const updateBuyer = (updates: Partial<AgreementData["buyer"]>) => {
    setFormData(prev => ({
      ...prev,
      buyer: { ...prev.buyer, ...updates },
    }))
  }

  const updatePricing = (updates: Partial<AgreementData["pricing"]>) => {
    setFormData(prev => ({
      ...prev,
      pricing: { ...prev.pricing, ...updates },
    }))
  }

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return !!formData.type
      case 2:
        return formData.selectedDogs.length > 0 && formData.pricing.total > 0
      case 3:
        return formData.buyer.name && formData.buyer.mobile && formData.buyer.email && formData.buyer.address
      case 4:
        return formData.sellerSignature && formData.pricing.total > 0
      default:
        return true
    }
  }

  const handleNext = () => {
    if (currentStep < 5) {
      setCurrentStep(prev => prev + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1)
    }
  }

  const handleComplete = async () => {
    setIsSubmitting(true)
    try {
      await onComplete(formData)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSignature = (signatureData: string) => {
    updateFormData({ sellerSignature: signatureData })
  }

  return (
    <div className="space-y-6">
      {/* Progress Steps */}
      <div className="relative">
        <div className="absolute left-0 top-1/2 h-0.5 w-full -translate-y-1/2 bg-border" />
        <div className="relative flex justify-between">
          {steps.map((step) => {
            const Icon = step.icon
            const isActive = step.id === currentStep
            const isCompleted = step.id < currentStep
            
            return (
              <motion.div
                key={step.id}
                className="flex flex-col items-center gap-2"
                initial={false}
                animate={isActive ? { scale: 1.05 } : { scale: 1 }}
              >
                <div
                  className={`relative z-10 flex h-10 w-10 items-center justify-center rounded-full border-2 transition-colors ${
                    isActive
                      ? "border-primary bg-primary text-primary-foreground"
                      : isCompleted
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border bg-background text-muted-foreground"
                  }`}
                >
                  {isCompleted ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    <Icon className="h-5 w-5" />
                  )}
                </div>
                <span
                  className={`text-xs font-medium ${
                    isActive ? "text-primary" : "text-muted-foreground"
                  }`}
                >
                  {step.title}
                </span>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Step Content */}
      <Card className="min-h-[400px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {(() => {
              const StepIcon = steps[currentStep - 1].icon
              return <StepIcon className="h-5 w-5" />
            })()}
            Step {currentStep}: {steps[currentStep - 1].title}
          </CardTitle>
          <CardDescription>
            {currentStep === 1 && "Select the type of agreement for this sale."}
            {currentStep === 2 && "Select dogs and set pricing details."}
            {currentStep === 3 && "Enter buyer contact information."}
            {currentStep === 4 && "Review the agreement and sign electronically."}
            {currentStep === 5 && "Send the agreement to the buyer for signature."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              {/* Step 1: Agreement Type */}
              {currentStep === 1 && (
                <div className="space-y-4">
                  <Label>Select Agreement Type</Label>
                  <RadioGroup
                    value={formData.type}
                    onValueChange={(value: "B2C" | "B2B" | "REHOME") => 
                      updateFormData({ type: value })
                    }
                    className="grid grid-cols-1 gap-4 md:grid-cols-3"
                  >
                    <div>
                      <RadioGroupItem
                        value="B2C"
                        id="b2c"
                        className="peer sr-only"
                      />
                      <Label
                        htmlFor="b2c"
                        className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-muted bg-popover p-6 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary peer-data-[state=checked]:bg-primary/5"
                      >
                        <User className="mb-3 h-6 w-6" />
                        <span className="font-semibold">B2C Sale</span>
                        <span className="text-xs text-muted-foreground">Retail Customer</span>
                      </Label>
                    </div>
                    <div>
                      <RadioGroupItem
                        value="B2B"
                        id="b2b"
                        className="peer sr-only"
                      />
                      <Label
                        htmlFor="b2b"
                        className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-muted bg-popover p-6 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary peer-data-[state=checked]:bg-primary/5"
                      >
                        <FileText className="mb-3 h-6 w-6" />
                        <span className="font-semibold">B2B Sale</span>
                        <span className="text-xs text-muted-foreground">Business Customer</span>
                      </Label>
                    </div>
                    <div>
                      <RadioGroupItem
                        value="REHOME"
                        id="rehome"
                        className="peer sr-only"
                      />
                      <Label
                        htmlFor="rehome"
                        className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-muted bg-popover p-6 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary peer-data-[state=checked]:bg-primary/5"
                      >
                        <Dog className="mb-3 h-6 w-6" />
                        <span className="font-semibold">Rehoming</span>
                        <span className="text-xs text-muted-foreground">$0 Transfer</span>
                      </Label>
                    </div>
                  </RadioGroup>
                </div>
              )}

              {/* Step 2: Dogs & Pricing */}
              {currentStep === 2 && (
                <div className="space-y-6">
                  {/* Dog Selection */}
                  <div className="space-y-3">
                    <Label>Select Dogs</Label>
                    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                      {dogs.map((dog) => (
                        <div
                          key={dog.id}
                          onClick={() => {
                            const newSelection = formData.selectedDogs.includes(dog.id)
                              ? formData.selectedDogs.filter(id => id !== dog.id)
                              : [...formData.selectedDogs, dog.id]
                            updateFormData({ selectedDogs: newSelection })
                          }}
                          className={`cursor-pointer rounded-lg border-2 p-4 transition-colors ${
                            formData.selectedDogs.includes(dog.id)
                              ? "border-primary bg-primary/5"
                              : "border-muted hover:border-muted-foreground/50"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium">{dog.name}</p>
                              <p className="text-sm text-muted-foreground">
                                {dog.breed} • {dog.microchip}
                              </p>
                            </div>
                            {formData.selectedDogs.includes(dog.id) && (
                              <Check className="h-5 w-5 text-primary" />
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <Separator />

                  {/* Pricing */}
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="total">Total Amount (SGD)</Label>
                        <Input
                          id="total"
                          type="number"
                          step="0.01"
                          value={formData.pricing.total || ""}
                          onChange={(e) => updatePricing({ 
                            total: parseFloat(e.target.value) || 0 
                          })}
                          placeholder="0.00"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="deposit">Deposit (Non-refundable)</Label>
                        <Input
                          id="deposit"
                          type="number"
                          step="0.01"
                          value={formData.pricing.deposit || ""}
                          onChange={(e) => updatePricing({ 
                            deposit: parseFloat(e.target.value) || 0 
                          })}
                          placeholder="0.00"
                        />
                      </div>
                    </div>

                    {/* GST Summary */}
                    {formData.pricing.total > 0 && (
                      <div className="rounded-lg bg-muted p-4">
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span>Subtotal:</span>
                            <span>${subtotal.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>GST (9%):</span>
                            <span>${gstAmount.toFixed(2)}</span>
                          </div>
                          <Separator className="my-2" />
                          <div className="flex justify-between font-semibold">
                            <span>Total:</span>
                            <span>${formData.pricing.total.toFixed(2)}</span>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="space-y-2">
                      <Label htmlFor="payment-method">Payment Method</Label>
                      <Select
                        value={formData.pricing.paymentMethod}
                        onValueChange={(value) => updatePricing({ paymentMethod: value })}
                      >
                        <SelectTrigger id="payment-method">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {paymentMethods.map((method) => (
                            <SelectItem key={method.value} value={method.value}>
                              {method.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 3: Buyer Information */}
              {currentStep === 3 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="buyer-name">Full Name *</Label>
                      <Input
                        id="buyer-name"
                        value={formData.buyer.name}
                        onChange={(e) => updateBuyer({ name: e.target.value })}
                        placeholder="Enter buyer's full name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="buyer-mobile">Mobile Number *</Label>
                      <Input
                        id="buyer-mobile"
                        value={formData.buyer.mobile}
                        onChange={(e) => updateBuyer({ mobile: e.target.value })}
                        placeholder="+65 9123 4567"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="buyer-email">Email Address *</Label>
                    <Input
                      id="buyer-email"
                      type="email"
                      value={formData.buyer.email}
                      onChange={(e) => updateBuyer({ email: e.target.value })}
                      placeholder="buyer@example.com"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="buyer-address">Address *</Label>
                    <Input
                      id="buyer-address"
                      value={formData.buyer.address}
                      onChange={(e) => updateBuyer({ address: e.target.value })}
                      placeholder="Full address"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="housing-type">Housing Type *</Label>
                    <Select
                      value={formData.buyer.housingType}
                      onValueChange={(value) => updateBuyer({ housingType: value })}
                    >
                      <SelectTrigger id="housing-type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {housingTypes.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {formData.type === "B2B" && (
                    <div className="space-y-2">
                      <Label htmlFor="buyer-nric">NRIC/FIN (Optional)</Label>
                      <Input
                        id="buyer-nric"
                        value={formData.buyer.nric || ""}
                        onChange={(e) => updateBuyer({ nric: e.target.value })}
                        placeholder="S1234567A"
                      />
                    </div>
                  )}

                  {/* HDB Warning */}
                  {showHDBWarning && (
                    <Alert variant="destructive">
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <strong>HDB Alert:</strong> The selected dog(s) may exceed HDB size restrictions. 
                        Please verify with HDB before proceeding.
                      </AlertDescription>
                    </Alert>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="special-conditions">Special Conditions (Optional)</Label>
                    <Input
                      id="special-conditions"
                      value={formData.specialConditions}
                      onChange={(e) => updateFormData({ specialConditions: e.target.value })}
                      placeholder="Any special terms or conditions"
                    />
                  </div>
                </div>
              )}

              {/* Step 4: Review & Sign */}
              {currentStep === 4 && (
                <div className="space-y-6">
                  <PreviewPanel formData={formData} dogs={dogs} />
                  
                  <Separator />
                  
                  <div className="space-y-4">
                    <Label>Seller Signature (Required)</Label>
                    <SignaturePad onSignature={handleSignature} />
                    {formData.sellerSignature && (
                      <p className="text-sm text-green-600 flex items-center gap-2">
                        <Check className="h-4 w-4" />
                        Signature captured
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Step 5: Send */}
              {currentStep === 5 && (
                <div className="space-y-6 text-center">
                  <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-primary/10">
                    <Send className="h-10 w-10 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold">Ready to Send</h3>
                    <p className="text-muted-foreground">
                      The agreement will be sent to {formData.buyer.name} at {formData.buyer.email}
                    </p>
                  </div>
                  <div className="rounded-lg bg-muted p-4 text-left">
                    <p className="text-sm font-medium">Summary:</p>
                    <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                      <li>• Agreement Type: {formData.type}</li>
                      <li>• Dogs: {formData.selectedDogs.length} selected</li>
                      <li>• Total: ${formData.pricing.total.toFixed(2)} (incl. GST)</li>
                      <li>• Buyer: {formData.buyer.name}</li>
                    </ul>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={currentStep === 1 ? onCancel : handleBack}
          disabled={isSubmitting}
        >
          <ChevronLeft className="mr-2 h-4 w-4" />
          {currentStep === 1 ? "Cancel" : "Back"}
        </Button>
        
        {currentStep < 5 ? (
          <Button
            onClick={handleNext}
            disabled={!canProceed()}
          >
            Next
            <ChevronRight className="ml-2 h-4 w-4" />
          </Button>
        ) : (
          <Button
            onClick={handleComplete}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                  className="mr-2 h-4 w-4 border-2 border-current border-t-transparent rounded-full"
                />
                Sending...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Send Agreement
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  )
}
