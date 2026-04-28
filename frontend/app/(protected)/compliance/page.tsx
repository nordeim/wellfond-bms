/**
 * Compliance Dashboard Page
 * ===========================
 * Phase 6: Compliance & NParks Reporting
 *
 * Main compliance dashboard with NParks submissions,
 * GST summary, and PDPA consent overview.
 */

"use client"

import { useState } from "react"
import Link from "next/link"
import {
  FileSpreadsheet,
  Calendar,
  CheckCircle,
  Clock,
  Lock,
  Download,
  Eye,
  AlertTriangle,
  TrendingUp,
  Users,
  Shield,
  ChevronRight,
  Filter,
  RefreshCw,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

import {
  useNParksSubmissions,
  useNParksGenerate,
  useGSTSummary,
  usePDPAStats,
} from "@/hooks/use-compliance"

// Document type configuration
const documentTypes: Record<
  string,
  { label: string; description: string; frequency: string; icon: typeof FileSpreadsheet }
> = {
  mating_sheet: {
    label: "Mating Sheet",
    description: "All mating events",
    frequency: "Monthly",
    icon: FileSpreadsheet,
  },
  puppy_movement: {
    label: "Puppy Movement",
    description: "Puppy transfers and sales",
    frequency: "Monthly",
    icon: FileSpreadsheet,
  },
  vet_treatments: {
    label: "Vet Treatments",
    description: "Veterinary procedures",
    frequency: "Monthly",
    icon: FileSpreadsheet,
  },
  puppies_bred: {
    label: "Puppies Bred",
    description: "Birth records",
    frequency: "Monthly",
    icon: FileSpreadsheet,
  },
  dog_movement: {
    label: "Dog Movement",
    description: "Adult dog transfers",
    frequency: "Monthly",
    icon: FileSpreadsheet,
  },
}

// Status configuration
const statusConfig: Record<string, { label: string; color: string; icon: typeof Clock }> = {
  DRAFT: { label: "Draft", color: "bg-gray-100 text-gray-800", icon: Clock },
  SUBMITTED: { label: "Submitted", color: "bg-blue-100 text-blue-800", icon: CheckCircle },
  LOCKED: { label: "Locked", color: "bg-green-100 text-green-800", icon: Lock },
}

// Mock current period
const currentPeriod = "2026-04"

export default function CompliancePage() {
  const [activeTab, setActiveTab] = useState("nparks")
  const [selectedPeriod, setSelectedPeriod] = useState(currentPeriod)

  // Data fetching
  const { data: submissions, isLoading: submissionsLoading } = useNParksSubmissions({
    period: selectedPeriod,
  })

  const { data: gstSummary, isLoading: gstLoading } = useGSTSummary(selectedPeriod)

  const { data: pdpaStats, isLoading: pdpaLoading } = usePDPAStats()

  const generateMutation = useNParksGenerate()

  const handleGenerate = async (documentType: string) => {
    await generateMutation.mutateAsync({
      document_type: documentType as "mating_sheet" | "puppy_movement" | "vet_treatments" | "puppies_bred" | "dog_movement",
      period: selectedPeriod,
    })
  }

  return (
    <div className="container mx-auto max-w-6xl py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Compliance & Reporting</h1>
        <p className="text-muted-foreground">
          NParks submissions, GST reporting, and PDPA consent management
        </p>
      </div>

      {/* Stats Overview */}
      <div className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">NParks Pending</p>
                <p className="text-2xl font-bold">
                  {submissionsLoading ? (
                    <Skeleton className="h-8 w-12" />
                  ) : (
                    submissions?.items.filter((s) => s.status === "DRAFT").length || 0
                  )}
                </p>
              </div>
              <div className="rounded-full bg-amber-100 p-2">
                <Clock className="h-5 w-5 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">GST This Month</p>
                <p className="text-2xl font-bold">
                  {gstLoading ? (
                    <Skeleton className="h-8 w-12" />
                  ) : (
                    `$${(gstSummary?.total_gst || 0).toLocaleString("en-SG", {
                      minimumFractionDigits: 2,
                    })}`
                  )}
                </p>
              </div>
              <div className="rounded-full bg-emerald-100 p-2">
                <TrendingUp className="h-5 w-5 text-emerald-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">PDPA Opt-in Rate</p>
                <p className="text-2xl font-bold">
                  {pdpaLoading ? (
                    <Skeleton className="h-8 w-12" />
                  ) : (
                    `${(pdpaStats?.opt_in_rate || 0).toFixed(1)}%`
                  )}
                </p>
              </div>
              <div className="rounded-full bg-blue-100 p-2">
                <Users className="h-5 w-5 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Compliance Score</p>
                <p className="text-2xl font-bold">98.5%</p>
              </div>
              <div className="rounded-full bg-green-100 p-2">
                <Shield className="h-5 w-5 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 md:w-auto">
          <TabsTrigger value="nparks">NParks Submissions</TabsTrigger>
          <TabsTrigger value="gst">GST Reporting</TabsTrigger>
          <TabsTrigger value="pdpa">PDPA Consent</TabsTrigger>
        </TabsList>

        {/* NParks Submissions Tab */}
        <TabsContent value="nparks" className="space-y-6">
          {/* Period Selector */}
          <Card>
            <CardHeader>
              <CardTitle>Generate NParks Reports</CardTitle>
              <CardDescription>
                Generate and submit monthly reports to NParks AVS
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-6 flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Reporting Period:</span>
                </div>
                <select
                  value={selectedPeriod}
                  onChange={(e) => setSelectedPeriod(e.target.value)}
                  className="rounded-md border px-3 py-2 text-sm"
                >
                  <option value="2026-04">April 2026</option>
                  <option value="2026-03">March 2026</option>
                  <option value="2026-02">February 2026</option>
                </select>
              </div>

              {/* Document Type Grid */}
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {Object.entries(documentTypes).map(([key, config]) => {
                  const Icon = config.icon
                  const submission = submissions?.items.find(
                    (s) => s.document_type === key && s.period === selectedPeriod
                  )
                  const status = submission ? statusConfig[submission.status] : null

                  return (
                    <Card
                      key={key}
                      className={`transition-colors ${submission?.status === "LOCKED" ? "bg-muted/50" : "hover:bg-muted/30"}`}
                    >
                      <CardContent className="p-4">
                        <div className="mb-3 flex items-start justify-between">
                          <div className="flex items-center gap-3">
                            <div className="rounded-lg bg-primary/10 p-2">
                              <Icon className="h-5 w-5 text-primary" />
                            </div>
                            <div>
                              <p className="font-medium">{config.label}</p>
                              <p className="text-xs text-muted-foreground">
                                {config.description}
                              </p>
                            </div>
                          </div>
                          {status && (
                            <Badge className={status.color}>
                              <status.icon className="mr-1 h-3 w-3" />
                              {status.label}
                            </Badge>
                          )}
                        </div>

                        <div className="mb-3 flex items-center gap-4 text-xs text-muted-foreground">
                          <span>{config.frequency}</span>
                          {submission && (
                            <>
                              <span>•</span>
                              <span>{submission.created_at.split("T")[0]}</span>
                            </>
                          )}
                        </div>

                        <div className="flex gap-2">
                          {!submission && (
                            <Button
                              size="sm"
                              className="flex-1"
                              onClick={() => handleGenerate(key)}
                              disabled={generateMutation.isPending}
                            >
                              {generateMutation.isPending ? (
                                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                              ) : (
                                <FileSpreadsheet className="mr-2 h-4 w-4" />
                              )}
                              Generate
                            </Button>
                          )}

                          {submission?.status === "DRAFT" && (
                            <>
                              <Button size="sm" variant="outline">
                                <Eye className="mr-2 h-4 w-4" />
                                Preview
                              </Button>
<Button size="sm" variant="primary">
                              <CheckCircle className="mr-2 h-4 w-4" />
                              Submit
                            </Button>
                            </>
                          )}

                          {(submission?.status === "SUBMITTED" || submission?.status === "LOCKED") && (
                            <Button size="sm" variant="outline" className="flex-1">
                              <Download className="mr-2 h-4 w-4" />
                              Download
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          {/* Submissions History */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Submission History</CardTitle>
                <CardDescription>Previous NParks submissions</CardDescription>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <Filter className="mr-2 h-4 w-4" />
                  Filter
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {submissionsLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : submissions?.items.length === 0 ? (
                <div className="py-8 text-center">
                  <FileSpreadsheet className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                  <h3 className="text-lg font-semibold">No submissions yet</h3>
                  <p className="text-sm text-muted-foreground">
                    Generate your first NParks report to get started
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {submissions?.items.map((submission) => {
                    const docType = documentTypes[submission.document_type]
                    const StatusIcon = statusConfig[submission.status].icon

                    return (
                      <div
                        key={submission.id}
                        className="flex items-center justify-between rounded-lg border p-4 hover:bg-muted/50"
                      >
                        <div className="flex items-center gap-4">
                          <div className="rounded-lg bg-primary/10 p-2">
                            <docType.icon className="h-5 w-5 text-primary" />
                          </div>
                          <div>
                            <p className="font-medium">{docType.label}</p>
                            <p className="text-sm text-muted-foreground">
                              {submission.entity_name} • {submission.period} •{" "}
                              {new Date(submission.created_at).toLocaleDateString("en-SG")}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <Badge className={statusConfig[submission.status].color}>
                            <StatusIcon className="mr-1 h-3 w-3" />
                            {statusConfig[submission.status].label}
                          </Badge>
                          <Button variant="ghost" size="sm">
                            <ChevronRight className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* GST Reporting Tab */}
        <TabsContent value="gst" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>GST Summary</CardTitle>
              <CardDescription>Current period GST calculations</CardDescription>
            </CardHeader>
            <CardContent>
              {gstLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-8 w-full" />
                  <Skeleton className="h-8 w-full" />
                </div>
              ) : gstSummary ? (
                <div className="space-y-6">
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="rounded-lg border p-4">
                      <p className="text-sm text-muted-foreground">Total Sales</p>
                      <p className="text-2xl font-bold">
                        ${gstSummary.total_sales.toLocaleString("en-SG", {
                          minimumFractionDigits: 2,
                        })}
                      </p>
                    </div>
                    <div className="rounded-lg border p-4">
                      <p className="text-sm text-muted-foreground">GST Component</p>
                      <p className="text-2xl font-bold">
                        ${gstSummary.total_gst.toLocaleString("en-SG", {
                          minimumFractionDigits: 2,
                        })}
                      </p>
                    </div>
                    <div className="rounded-lg border p-4">
                      <p className="text-sm text-muted-foreground">Transactions</p>
                      <p className="text-2xl font-bold">{gstSummary.transactions_count}</p>
                    </div>
                  </div>

                  <Separator />

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <AlertTriangle className="h-4 w-4" />
                      <span>
                        Thomson entity is GST exempt (0%). All other entities at 9%.
                      </span>
                    </div>
                    <Button variant="outline">
                      <Download className="mr-2 h-4 w-4" />
                      Export
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="py-8 text-center">
                  <TrendingUp className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                  <h3 className="text-lg font-semibold">No GST data</h3>
                  <p className="text-sm text-muted-foreground">
                    GST summary will appear when agreements are completed
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* GST Ledger Preview */}
          <Card>
            <CardHeader>
              <CardTitle>GST Ledger</CardTitle>
              <CardDescription>Individual transaction GST entries</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <div className="grid grid-cols-5 border-b bg-muted/50 p-3 text-sm font-medium">
                  <div>Date</div>
                  <div>Entity</div>
                  <div className="text-right">Total</div>
                  <div className="text-right">GST</div>
                  <div className="text-right">Actions</div>
                </div>
                <div className="divide-y">
                  {/* Placeholder rows */}
                  <div className="grid grid-cols-5 items-center p-3 text-sm">
                    <div className="text-muted-foreground">No entries</div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* PDPA Consent Tab */}
        <TabsContent value="pdpa" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>PDPA Consent Overview</CardTitle>
              <CardDescription>Customer consent status and compliance</CardDescription>
            </CardHeader>
            <CardContent>
              {pdpaLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-8 w-full" />
                  <Skeleton className="h-8 w-full" />
                </div>
              ) : pdpaStats ? (
                <div className="space-y-6">
                  <div className="grid gap-4 md:grid-cols-4">
                    <div className="rounded-lg border p-4">
                      <p className="text-sm text-muted-foreground">Total Customers</p>
                      <p className="text-2xl font-bold">{pdpaStats.total_customers}</p>
                    </div>
                    <div className="rounded-lg border border-green-200 bg-green-50/50 p-4">
                      <p className="text-sm text-green-700">Opted In</p>
                      <p className="text-2xl font-bold text-green-800">
                        {pdpaStats.opted_in}
                      </p>
                    </div>
                    <div className="rounded-lg border border-red-200 bg-red-50/50 p-4">
                      <p className="text-sm text-red-700">Opted Out</p>
                      <p className="text-2xl font-bold text-red-800">
                        {pdpaStats.opted_out}
                      </p>
                    </div>
                    <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-4">
                      <p className="text-sm text-amber-700">Never Responded</p>
                      <p className="text-2xl font-bold text-amber-800">
                        {pdpaStats.never_responded}
                      </p>
                    </div>
                  </div>

                  <Separator />

                  <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      Hard filter applied: Only opted-in customers receive marketing.
                    </div>
                    <Link href="/compliance/settings">
                      <Button variant="outline">Manage Consent Settings</Button>
                    </Link>
                  </div>
                </div>
              ) : (
                <div className="py-8 text-center">
                  <Shield className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                  <h3 className="text-lg font-semibold">No customer data</h3>
                  <p className="text-sm text-muted-foreground">
                    PDPA statistics will appear when customer records are added
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Consent Log Preview */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Recent Consent Changes</CardTitle>
                <CardDescription>Audit log of consent changes</CardDescription>
              </div>
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    View Full Log
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-3xl">
                  <DialogHeader>
                    <DialogTitle>PDPA Consent Audit Log</DialogTitle>
                    <DialogDescription>
                      Complete history of consent changes (immutable)
                    </DialogDescription>
                  </DialogHeader>
                  <div className="max-h-[400px] overflow-auto">
                    <p className="py-8 text-center text-muted-foreground">
                      Consent log will be available in Phase 7
                    </p>
                  </div>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <div className="grid grid-cols-5 border-b bg-muted/50 p-3 text-sm font-medium">
                  <div>Date</div>
                  <div>Customer</div>
                  <div>Action</div>
                  <div>Actor</div>
                  <div>IP Address</div>
                </div>
                <div className="divide-y">
                  <div className="grid grid-cols-5 items-center p-3 text-sm">
                    <div className="text-muted-foreground">No entries</div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
