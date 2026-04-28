"""Sales Agreements Page
========================
Phase 5: Sales Agreements & AVS Tracking

List view for sales agreements with status filtering
and quick actions.
"""

import { Suspense } from "react"
import Link from "next/link"
import { 
  FileText, 
  Plus, 
  Filter,
  Search,
  CheckCircle,
  Clock,
  AlertCircle,
  XCircle
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"

// Mock data - replace with actual data fetching
const mockAgreements = [
  {
    id: "1",
    agreement_number: "WF-B2C-001",
    type: "B2C",
    status: "SIGNED",
    buyer_name: "John Tan",
    buyer_mobile: "+65 9123 4567",
    total: 3082.50,
    created_at: "2025-04-28T10:00:00Z",
    dog_count: 1,
  },
  {
    id: "2",
    agreement_number: "WF-B2B-001",
    type: "B2B",
    status: "DRAFT",
    buyer_name: "Pet Paradise Pte Ltd",
    buyer_mobile: "+65 6789 0123",
    total: 15000.00,
    created_at: "2025-04-27T15:30:00Z",
    dog_count: 3,
  },
  {
    id: "3",
    agreement_number: "WF-REHOME-001",
    type: "REHOME",
    status: "COMPLETED",
    buyer_name: "Sarah Lee",
    buyer_mobile: "+65 8765 4321",
    total: 0.00,
    created_at: "2025-04-25T09:00:00Z",
    dog_count: 1,
  },
  {
    id: "4",
    agreement_number: "WF-B2C-002",
    type: "B2C",
    status: "CANCELLED",
    buyer_name: "Michael Chen",
    buyer_mobile: "+65 9345 6789",
    total: 5280.00,
    created_at: "2025-04-24T14:00:00Z",
    dog_count: 1,
  },
]

const statusConfig: Record<string, { label: string; color: string; icon: typeof Clock }> = {
  DRAFT: { label: "Draft", color: "bg-gray-100 text-gray-800", icon: Clock },
  SIGNED: { label: "Signed", color: "bg-blue-100 text-blue-800", icon: CheckCircle },
  COMPLETED: { label: "Completed", color: "bg-green-100 text-green-800", icon: CheckCircle },
  CANCELLED: { label: "Cancelled", color: "bg-red-100 text-red-800", icon: XCircle },
}

const typeConfig: Record<string, { label: string; color: string }> = {
  B2C: { label: "B2C", color: "bg-purple-100 text-purple-800" },
  B2B: { label: "B2B", color: "bg-orange-100 text-orange-800" },
  REHOME: { label: "Rehome", color: "bg-teal-100 text-teal-800" },
}

function AgreementCard({ agreement }: { agreement: typeof mockAgreements[0] }) {
  const status = statusConfig[agreement.status]
  const type = typeConfig[agreement.type]
  const StatusIcon = status.icon

  return (
    <Link href={`/sales/${agreement.id}`}>
      <Card className="group cursor-pointer transition-colors hover:bg-muted/50">
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm text-muted-foreground">
                  {agreement.agreement_number}
                </span>
                <Badge variant="secondary" className={type.color}>
                  {type.label}
                </Badge>
              </div>
              <p className="font-medium">{agreement.buyer_name}</p>
              <p className="text-sm text-muted-foreground">
                {agreement.buyer_mobile}
              </p>
            </div>
            <div className="text-right">
              <Badge className={status.color}>
                <StatusIcon className="mr-1 h-3 w-3" />
                {status.label}
              </Badge>
              <p className="mt-2 font-semibold">
                ${agreement.total.toLocaleString("en-SG", { minimumFractionDigits: 2 })}
              </p>
              <p className="text-xs text-muted-foreground">
                {agreement.dog_count} dog{agreement.dog_count > 1 ? "s" : ""}
              </p>
            </div>
          </div>
          <Separator className="my-3" />
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              Created {new Date(agreement.created_at).toLocaleDateString("en-SG")}
            </span>
            <span className="text-primary group-hover:underline">
              View Details →
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}

function AgreementListSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <Card key={i}>
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-5 w-48" />
                <Skeleton className="h-4 w-36" />
              </div>
              <div className="text-right space-y-2">
                <Skeleton className="h-5 w-20" />
                <Skeleton className="h-6 w-24" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

export default function SalesPage() {
  return (
    <div className="container mx-auto max-w-4xl py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sales Agreements</h1>
          <p className="text-muted-foreground">
            Manage sales agreements and AVS transfers
          </p>
        </div>
        <Link href="/sales/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Agreement
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Total</p>
            <p className="text-2xl font-bold">{mockAgreements.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Draft</p>
            <p className="text-2xl font-bold">
              {mockAgreements.filter(a => a.status === "DRAFT").length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Pending AVS</p>
            <p className="text-2xl font-bold">
              {mockAgreements.filter(a => a.status === "SIGNED").length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Completed</p>
            <p className="text-2xl font-bold">
              {mockAgreements.filter(a => a.status === "COMPLETED").length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-col gap-4 md:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search agreements..."
            className="pl-9"
          />
        </div>
        <Button variant="outline">
          <Filter className="mr-2 h-4 w-4" />
          Filter
        </Button>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="draft">Draft</TabsTrigger>
          <TabsTrigger value="signed">Signed</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
        </TabsList>

        <Suspense fallback={<AgreementListSkeleton />}>
          <TabsContent value="all" className="space-y-4">
            {mockAgreements.map((agreement) => (
              <AgreementCard key={agreement.id} agreement={agreement} />
            ))}
          </TabsContent>

          <TabsContent value="draft" className="space-y-4">
            {mockAgreements
              .filter((a) => a.status === "DRAFT")
              .map((agreement) => (
                <AgreementCard key={agreement.id} agreement={agreement} />
              ))}
          </TabsContent>

          <TabsContent value="signed" className="space-y-4">
            {mockAgreements
              .filter((a) => a.status === "SIGNED")
              .map((agreement) => (
                <AgreementCard key={agreement.id} agreement={agreement} />
              ))}
          </TabsContent>

          <TabsContent value="completed" className="space-y-4">
            {mockAgreements
              .filter((a) => a.status === "COMPLETED")
              .map((agreement) => (
                <AgreementCard key={agreement.id} agreement={agreement} />
              ))}
          </TabsContent>
        </Suspense>
      </Tabs>

      {/* Empty State */}
      {mockAgreements.length === 0 && (
        <Card className="py-12 text-center">
          <CardContent>
            <FileText className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
            <h3 className="text-lg font-semibold">No agreements yet</h3>
            <p className="mb-4 text-sm text-muted-foreground">
              Create your first sales agreement to get started
            </p>
            <Link href="/sales/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Agreement
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
