/**
 * Compliance Settings Page
 * =========================
 * Phase 6: Compliance & NParks Reporting
 *
 * Configure T&C templates, GST settings, and PDPA preferences.
 */

"use client"

import { useState } from "react"
import {
  FileText,
  Percent,
  Shield,
  Save,
  RefreshCw,
  AlertTriangle,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { toast } from "sonner"

// Default T&C templates
const defaultTemplates = {
  B2C: `TERMS AND CONDITIONS - B2C SALE

1. DEPOSIT
   A non-refundable deposit of 20% is required to reserve this puppy.
   
2. HEALTH GUARANTEE
   The seller provides a 7-day health guarantee from the date of collection.
   
3. AVS TRANSFER
   Buyer agrees to complete the AVS transfer within 3 days of collection.
   
4. HDB APPROVAL
   For HDB flats, buyer confirms they have obtained prior approval for the breed.
   
5. CANCELLATION
   Deposits are non-refundable. In exceptional circumstances, store credit may be offered at the seller's discretion.`,

  B2B: `TERMS AND CONDITIONS - B2B SALE

1. PAYMENT TERMS
   Net 14 days from invoice date. Late payments subject to 1.5% monthly interest.
   
2. DELIVERY
   Delivery arranged at buyer's cost or collection from seller's premises.
   
3. HEALTH CERTIFICATE
   All dogs come with AVS health certificates and vaccination records.
   
4. MINIMUM ORDER
   Minimum order of 3 puppies per transaction.
   
5. WARRANTY
   48-hour health warranty from collection. Claims require veterinary report.`,

  REHOME: `TERMS AND CONDITIONS - REHOME

1. NO SALE
   This is a rehoming arrangement, not a sale.
   
2. HEALTH DISCLOSURE
   Previous owner discloses all known health conditions.
   
3. NO WARRANTY
   No health warranty provided. Adopter accepts dog as-is.
   
4. AVS TRANSFER
   New owner must complete AVS transfer within 3 days.
   
5. RETURN POLICY
   If rehoming doesn't work out, please contact the previous owner first.`,
}

export default function ComplianceSettingsPage() {
  const [activeTab, setActiveTab] = useState("templates")
  const [saving, setSaving] = useState(false)

  // T&C Template state
  const [templates, setTemplates] = useState(defaultTemplates)

  // GST Settings state
  const [gstSettings, setGstSettings] = useState({
    katongGstRate: 9,
    thomsonGstRate: 0,
    holdingsGstRate: 9,
    autoCalculate: true,
  })

  // PDPA Settings state
  const [pdpaSettings, setPdpaSettings] = useState({
    requireExplicitConsent: true,
    logAllActions: true,
    autoOptOutOnUnsubscribe: true,
    retentionDays: 2555, // 7 years
  })

  const handleSave = async () => {
    setSaving(true)
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000))
    setSaving(false)
    toast.success("Settings saved successfully")
  }

  const handleReset = () => {
    setTemplates(defaultTemplates)
    toast.info("Templates reset to defaults")
  }

  return (
    <div className="container mx-auto max-w-4xl py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Compliance Settings</h1>
        <p className="text-muted-foreground">
          Configure T&C templates, GST rates, and PDPA preferences
        </p>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 md:w-auto">
          <TabsTrigger value="templates">
            <FileText className="mr-2 h-4 w-4" />
            T&C Templates
          </TabsTrigger>
          <TabsTrigger value="gst">
            <Percent className="mr-2 h-4 w-4" />
            GST Settings
          </TabsTrigger>
          <TabsTrigger value="pdpa">
            <Shield className="mr-2 h-4 w-4" />
            PDPA Settings
          </TabsTrigger>
        </TabsList>

        {/* T&C Templates Tab */}
        <TabsContent value="templates" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Terms & Conditions Templates</CardTitle>
                <CardDescription>
                  Customize T&C text for each agreement type
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={handleReset}>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Reset
                </Button>
                <Button onClick={handleSave} disabled={saving}>
                  {saving ? (
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  Save Changes
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* B2C Template */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Badge>B2C</Badge>
                  <Label htmlFor="template-b2c">Consumer Sales Template</Label>
                </div>
                <Textarea
                  id="template-b2c"
                  value={templates.B2C}
                  onChange={(e) =>
                    setTemplates({ ...templates, B2C: e.target.value })
                  }
                  className="min-h-[200px] font-mono text-sm"
                  placeholder="Enter T&C for B2C agreements..."
                />
                <p className="text-xs text-muted-foreground">
                  Used for individual consumer sales
                </p>
              </div>

              <Separator />

              {/* B2B Template */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">B2B</Badge>
                  <Label htmlFor="template-b2b">Business Sales Template</Label>
                </div>
                <Textarea
                  id="template-b2b"
                  value={templates.B2B}
                  onChange={(e) =>
                    setTemplates({ ...templates, B2B: e.target.value })
                  }
                  className="min-h-[200px] font-mono text-sm"
                  placeholder="Enter T&C for B2B agreements..."
                />
                <p className="text-xs text-muted-foreground">
                  Used for business-to-business transactions
                </p>
              </div>

              <Separator />

              {/* Rehome Template */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">Rehome</Badge>
                  <Label htmlFor="template-rehome">Rehoming Template</Label>
                </div>
                <Textarea
                  id="template-rehome"
                  value={templates.REHOME}
                  onChange={(e) =>
                    setTemplates({ ...templates, REHOME: e.target.value })
                  }
                  className="min-h-[200px] font-mono text-sm"
                  placeholder="Enter T&C for rehoming agreements..."
                />
                <p className="text-xs text-muted-foreground">
                  Used for rehoming arrangements (no sale)
                </p>
              </div>

              <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-600" />
                  <div>
                    <p className="font-medium text-amber-900">Important Notice</p>
                    <p className="text-sm text-amber-800">
                      Changes to T&C templates will only affect new agreements.
                      Existing agreements retain their original terms.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* GST Settings Tab */}
        <TabsContent value="gst" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>GST Configuration</CardTitle>
              <CardDescription>
                Entity-specific GST rates and calculation settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-3">
                {/* Katong */}
                <div className="space-y-2">
                  <Label htmlFor="gst-katong">Katong Entity GST Rate (%)</Label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      id="gst-katong"
                      value={gstSettings.katongGstRate}
                      onChange={(e) =>
                        setGstSettings({
                          ...gstSettings,
                          katongGstRate: parseInt(e.target.value) || 0,
                        })
                      }
                      className="flex h-10 w-20 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      min={0}
                      max={20}
                    />
                    <span className="text-sm text-muted-foreground">%</span>
                  </div>
                </div>

                {/* Thomson */}
                <div className="space-y-2">
                  <Label htmlFor="gst-thomson">Thomson Entity GST Rate (%)</Label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      id="gst-thomson"
                      value={gstSettings.thomsonGstRate}
                      onChange={(e) =>
                        setGstSettings({
                          ...gstSettings,
                          thomsonGstRate: parseInt(e.target.value) || 0,
                        })
                      }
                      className="flex h-10 w-20 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      min={0}
                      max={20}
                    />
                    <span className="text-sm text-muted-foreground">%</span>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    Currently exempt
                  </Badge>
                </div>

                {/* Holdings */}
                <div className="space-y-2">
                  <Label htmlFor="gst-holdings">Holdings Entity GST Rate (%)</Label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      id="gst-holdings"
                      value={gstSettings.holdingsGstRate}
                      onChange={(e) =>
                        setGstSettings({
                          ...gstSettings,
                          holdingsGstRate: parseInt(e.target.value) || 0,
                        })
                      }
                      className="flex h-10 w-20 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      min={0}
                      max={20}
                    />
                    <span className="text-sm text-muted-foreground">%</span>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Auto Calculate */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="auto-calculate">Auto-calculate GST</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically calculate GST on agreement creation
                  </p>
                </div>
                <Switch
                  id="auto-calculate"
                  checked={gstSettings.autoCalculate}
                  onCheckedChange={(checked: boolean) =>
                    setGstSettings({ ...gstSettings, autoCalculate: checked })
                  }
                />
              </div>

              <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-4">
                <div className="flex items-start gap-3">
                  <Percent className="mt-0.5 h-5 w-5 text-blue-600" />
                  <div>
                    <p className="font-medium text-blue-900">GST Calculation</p>
                    <p className="text-sm text-blue-800">
                      GST is calculated using formula: price × rate / (100 + rate).<br />
                      Example: $109 at 9% = $109 × 9 / 109 = $9.00
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <Button onClick={handleSave} disabled={saving}>
                  {saving ? (
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  Save GST Settings
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* PDPA Settings Tab */}
        <TabsContent value="pdpa" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>PDPA Configuration</CardTitle>
              <CardDescription>
                Data protection and consent management settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Require Explicit Consent */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="explicit-consent">Require Explicit Consent</Label>
                  <p className="text-sm text-muted-foreground">
                    Customers must actively opt-in to marketing communications
                  </p>
                </div>
                <Switch
                  id="explicit-consent"
                  checked={pdpaSettings.requireExplicitConsent}
onCheckedChange={(checked: boolean) =>
                      setPdpaSettings({
                        ...pdpaSettings,
                        requireExplicitConsent: checked,
                      })
                    }
                />
              </div>

              <Separator />

              {/* Log All Actions */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="log-actions">Log All Actions</Label>
                  <p className="text-sm text-muted-foreground">
                    Record every consent change with IP, user agent, and actor
                  </p>
                </div>
                <Switch
                  id="log-actions"
                  checked={pdpaSettings.logAllActions}
                  onCheckedChange={(checked: boolean) =>
                    setPdpaSettings({
                      ...pdpaSettings,
                      logAllActions: checked,
                    })
                  }
                />
              </div>

              <Separator />

              {/* Auto Opt-Out */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="auto-optout">Auto Opt-Out on Unsubscribe</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically process unsubscribe requests as opt-outs
                  </p>
                </div>
                <Switch
                  id="auto-optout"
                  checked={pdpaSettings.autoOptOutOnUnsubscribe}
                  onCheckedChange={(checked: boolean) =>
                    setPdpaSettings({
                      ...pdpaSettings,
                      autoOptOutOnUnsubscribe: checked,
                    })
                  }
                />
              </div>

              <Separator />

              {/* Data Retention */}
              <div className="space-y-2">
                <Label htmlFor="retention">Data Retention Period (days)</Label>
                <div className="flex items-center gap-4">
                  <input
                    type="number"
                    id="retention"
                    value={pdpaSettings.retentionDays}
                    onChange={(e) =>
                      setPdpaSettings({
                        ...pdpaSettings,
                        retentionDays: parseInt(e.target.value) || 2555,
                      })
                    }
                    className="flex h-10 w-32 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    min={365}
                    max={36500}
                  />
                  <span className="text-sm text-muted-foreground">
                    ≈ {(pdpaSettings.retentionDays / 365).toFixed(1)} years
                  </span>
                </div>
              </div>

              <div className="rounded-lg border border-red-200 bg-red-50/50 p-4">
                <div className="flex items-start gap-3">
                  <Shield className="mt-0.5 h-5 w-5 text-red-600" />
                  <div>
                    <p className="font-medium text-red-900">Hard Filter Notice</p>
                    <p className="text-sm text-red-800">
                      PDPA consent is a hard filter at the query level. Even
                      administrators cannot override consent=false for marketing
                      communications.
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <Button onClick={handleSave} disabled={saving}>
                  {saving ? (
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  Save PDPA Settings
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
