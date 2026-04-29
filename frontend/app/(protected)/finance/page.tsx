/**
 * Finance Page
 * ============
 * Phase 8: Finance Module
 *
 * Tabs:
 * - P&L: Monthly profit & loss statements with YTD rollup
 * - GST: Quarterly GST reports for IRAS filing
 * - Transactions: Transaction list with filters
 * - Intercompany: Intercompany transfer management
 */

"use client"

import { useState } from "react"
import {
  DollarSign,
  TrendingUp,
  FileText,
  Download,
  ArrowRightLeft,
  Plus,
  Filter,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

import {
  usePNL,
  useGSTReport,
  useTransactions,
  useIntercompanyTransfers,
  exportPNLExcel,
  exportGSTExcel,
  formatCurrency,
  formatDate,
  getCurrentQuarter,
  getCurrentMonth,
} from "@/hooks/use-finance"

// Entity selector for demo
const ENTITIES = [
  { id: "holdings", name: "Holdings", code: "HOLDINGS" },
  { id: "katong", name: "Katong", code: "KATONG" },
  { id: "thomson", name: "Thomson", code: "THOMSON" },
]

export default function FinancePage() {
  const [activeTab, setActiveTab] = useState("pnl")
  const [selectedEntity, setSelectedEntity] = useState(ENTITIES[0].id)
  const [selectedMonth, setSelectedMonth] = useState(getCurrentMonth())
  const [selectedQuarter, setSelectedQuarter] = useState(getCurrentQuarter())

  // Queries
  const { data: pnlData, isLoading: pnlLoading } = usePNL(
    selectedEntity,
    selectedMonth
  )
  const { data: gstData, isLoading: gstLoading } = useGSTReport(
    selectedEntity,
    selectedQuarter
  )
  const { data: transactionsData } = useTransactions({ entity_id: selectedEntity })
  const { data: intercompanyData } = useIntercompanyTransfers(selectedEntity)

  // Export handlers
  const handleExportPNL = async () => {
    try {
      await exportPNLExcel(selectedEntity, selectedMonth)
    } catch (error) {
      console.error("Export failed:", error)
    }
  }

  const handleExportGST = async () => {
    try {
      await exportGSTExcel(selectedEntity, selectedQuarter)
    } catch (error) {
      console.error("Export failed:", error)
    }
  }

  return (
    <div className="container mx-auto max-w-6xl py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Finance</h1>
        <p className="text-muted-foreground">
          P&L statements, GST reports, and transaction management
        </p>
      </div>

      {/* Entity Selector */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Label htmlFor="entity">Entity</Label>
              <Select value={selectedEntity} onValueChange={setSelectedEntity}>
                <SelectTrigger id="entity">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ENTITIES.map((entity) => (
                    <SelectItem key={entity.id} value={entity.id}>
                      {entity.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-6">
          <TabsTrigger value="pnl">
            <TrendingUp className="mr-2 h-4 w-4" />
            P&L Statement
          </TabsTrigger>
          <TabsTrigger value="gst">
            <FileText className="mr-2 h-4 w-4" />
            GST Report
          </TabsTrigger>
          <TabsTrigger value="transactions">
            <DollarSign className="mr-2 h-4 w-4" />
            Transactions
          </TabsTrigger>
          <TabsTrigger value="intercompany">
            <ArrowRightLeft className="mr-2 h-4 w-4" />
            Intercompany
          </TabsTrigger>
        </TabsList>

        {/* P&L Tab */}
        <TabsContent value="pnl">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Profit & Loss Statement</CardTitle>
                <p className="text-sm text-muted-foreground">
                  Singapore fiscal year: April - March
                </p>
              </div>
              <div className="flex items-center gap-4">
                <div>
                  <Label htmlFor="month">Month</Label>
                  <Input
                    id="month"
                    type="month"
                    value={selectedMonth}
                    onChange={(e) => setSelectedMonth(e.target.value)}
                  />
                </div>
                <Button
                  variant="outline"
                  onClick={handleExportPNL}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Export Excel
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {pnlLoading ? (
                <div className="py-8 text-center">Loading...</div>
              ) : pnlData ? (
                <div className="space-y-6">
                  {/* Summary Cards */}
                  <div className="grid gap-4 md:grid-cols-4">
                    <Card>
                      <CardContent className="pt-6">
                        <p className="text-sm text-muted-foreground">Revenue</p>
                        <p className="text-2xl font-bold">
                          {formatCurrency(pnlData.revenue)}
                        </p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6">
                        <p className="text-sm text-muted-foreground">COGS</p>
                        <p className="text-2xl font-bold text-red-600">
                          {formatCurrency(pnlData.cogs)}
                        </p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6">
                        <p className="text-sm text-muted-foreground">Expenses</p>
                        <p className="text-2xl font-bold text-red-600">
                          {formatCurrency(pnlData.expenses)}
                        </p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6">
                        <p className="text-sm text-muted-foreground">Net</p>
                        <p
                          className={`text-2xl font-bold ${
                            parseFloat(pnlData.net) >= 0
                              ? "text-green-600"
                              : "text-red-600"
                          }`}
                        >
                          {formatCurrency(pnlData.net)}
                        </p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* P&L Table */}
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Item</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell className="font-medium">Revenue</TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(pnlData.revenue)}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell className="pl-8">Less: Cost of Goods Sold</TableCell>
                        <TableCell className="text-right text-red-600">
                          -{formatCurrency(pnlData.cogs)}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell className="pl-8">Less: Operating Expenses</TableCell>
                        <TableCell className="text-right text-red-600">
                          -{formatCurrency(pnlData.expenses)}
                        </TableCell>
                      </TableRow>
                      <TableRow className="font-bold">
                        <TableCell>Net Profit/(Loss)</TableCell>
                        <TableCell
                          className={`text-right ${
                            parseFloat(pnlData.net) >= 0
                              ? "text-green-600"
                              : "text-red-600"
                          }`}
                        >
                          {formatCurrency(pnlData.net)}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>

                  {/* YTD Section */}
                  <div className="rounded-lg bg-muted p-4">
                    <h4 className="mb-2 font-semibold">Year-to-Date (YTD)</h4>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <p className="text-sm text-muted-foreground">YTD Revenue</p>
                        <p className="text-xl font-semibold">
                          {formatCurrency(pnlData.ytd_revenue)}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">YTD Net</p>
                        <p
                          className={`text-xl font-semibold ${
                            parseFloat(pnlData.ytd_net) >= 0
                              ? "text-green-600"
                              : "text-red-600"
                          }`}
                        >
                          {formatCurrency(pnlData.ytd_net)}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-8 text-center text-muted-foreground">
                  No P&L data available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* GST Tab */}
        <TabsContent value="gst">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>GST Report</CardTitle>
                <p className="text-sm text-muted-foreground">
                  IRAS GST9/GST109 format
                </p>
              </div>
              <div className="flex items-center gap-4">
                <div>
                  <Label htmlFor="quarter">Quarter</Label>
                  <Select value={selectedQuarter} onValueChange={setSelectedQuarter}>
                    <SelectTrigger id="quarter" className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="2026-Q1">2026 Q1</SelectItem>
                      <SelectItem value="2026-Q2">2026 Q2</SelectItem>
                      <SelectItem value="2026-Q3">2026 Q3</SelectItem>
                      <SelectItem value="2026-Q4">2026 Q4</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  variant="outline"
                  onClick={handleExportGST}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Export Excel
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {gstLoading ? (
                <div className="py-8 text-center">Loading...</div>
              ) : gstData ? (
                <div className="space-y-6">
                  {/* GST Summary */}
                  <div className="grid gap-4 md:grid-cols-2">
                    <Card>
                      <CardContent className="pt-6">
                        <p className="text-sm text-muted-foreground">Total Sales (Excl. GST)</p>
                        <p className="text-2xl font-bold">
                          {formatCurrency(gstData.total_sales)}
                        </p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6">
                        <p className="text-sm text-muted-foreground">Total GST</p>
                        <p className="text-2xl font-bold">
                          {formatCurrency(gstData.total_gst)}
                          {gstData.entity_name === "Thomson" && (
                            <Badge variant="secondary" className="ml-2">
                              GST Exempt
                            </Badge>
                          )}
                        </p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* GST Formula Note */}
                  <div className="rounded-lg bg-blue-50 p-4 text-sm text-blue-800">
                    <p className="font-semibold">GST Formula Applied:</p>
                    <p>GST = price × 9 / 109, rounded to nearest cent (ROUND_HALF_UP)</p>
                    <p className="mt-1 text-xs">
                      Example: $109.00 → $9.00 GST | $50.00 → $4.13 GST
                    </p>
                  </div>

                  {/* Transactions Table */}
                  {gstData.transactions && gstData.transactions.length > 0 ? (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Date</TableHead>
                          <TableHead>Description</TableHead>
                          <TableHead className="text-right">Value (Excl. GST)</TableHead>
                          <TableHead className="text-right">GST Amount</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {gstData.transactions.slice(0, 10).map((txn) => (
                          <TableRow key={txn.id}>
                            <TableCell>{formatDate(txn.date)}</TableCell>
                            <TableCell>{txn.description}</TableCell>
                            <TableCell className="text-right">
                              {formatCurrency(txn.amount)}
                            </TableCell>
                            <TableCell className="text-right">
                              {formatCurrency(txn.gst_component)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  ) : (
                    <div className="py-8 text-center text-muted-foreground">
                      No transactions for this quarter
                    </div>
                  )}
                </div>
              ) : (
                <div className="py-8 text-center text-muted-foreground">
                  No GST data available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Transactions Tab */}
        <TabsContent value="transactions">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Transactions</CardTitle>
              <Button variant="outline">
                <Filter className="mr-2 h-4 w-4" />
                Filter
              </Button>
            </CardHeader>
            <CardContent>
              {transactionsData?.items && transactionsData.items.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {transactionsData.items.map((txn) => (
                      <TableRow key={txn.id}>
                        <TableCell>{formatDate(txn.date)}</TableCell>
                        <TableCell>
                        <Badge
                          variant={
                            txn.type === "REVENUE"
                              ? "default"
                              : txn.type === "EXPENSE"
                                ? "error"
                                : "secondary"
                          }
                        >
                            {txn.type}
                          </Badge>
                        </TableCell>
                        <TableCell>{txn.category}</TableCell>
                        <TableCell className="max-w-xs truncate">
                          {txn.description || "-"}
                        </TableCell>
                        <TableCell
                          className={`text-right ${
                            txn.type === "REVENUE" ? "text-green-600" : "text-red-600"
                          }`}
                        >
                          {txn.type === "REVENUE" ? "+" : "-"}
                          {formatCurrency(txn.amount)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="py-8 text-center text-muted-foreground">
                  No transactions found
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Intercompany Tab */}
        <TabsContent value="intercompany">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Intercompany Transfers</CardTitle>
              <Button variant="outline">
                <Plus className="mr-2 h-4 w-4" />
                New Transfer
              </Button>
            </CardHeader>
            <CardContent>
              {intercompanyData?.items && intercompanyData.items.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>From</TableHead>
                      <TableHead>To</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Description</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {intercompanyData.items.map((transfer) => (
                      <TableRow key={transfer.id}>
                        <TableCell>{formatDate(transfer.date)}</TableCell>
                        <TableCell>{transfer.from_entity_name}</TableCell>
                        <TableCell>{transfer.to_entity_name}</TableCell>
                        <TableCell className="font-medium">
                          {formatCurrency(transfer.amount)}
                        </TableCell>
                        <TableCell>{transfer.description}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="py-8 text-center text-muted-foreground">
                  No intercompany transfers found
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
