"use client"

import { useState } from "react"
import {
  Users,
  Search,
  Filter,
  Plus,
  Mail,
  MessageSquare,
  Send,
  Upload,
  Shield,
  Eye,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

export default function CustomersPage() {
  const [activeTab, setActiveTab] = useState("list")
  const [searchQuery, setSearchQuery] = useState("")
  const [showBlastComposer, setShowBlastComposer] = useState(false)

  return (
    <div className="container mx-auto max-w-6xl py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Customer Database</h1>
          <p className="text-muted-foreground">
            Manage customers and send targeted marketing blasts
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Upload className="mr-2 h-4 w-4" />
            Import CSV
          </Button>
          <Button variant="outline">
            <Plus className="mr-2 h-4 w-4" />
            Add Customer
          </Button>
          <Button onClick={() => setShowBlastComposer(true)}>
            <Send className="mr-2 h-4 w-4" />
            New Blast
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Customers</p>
                <p className="text-2xl font-bold">0</p>
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
                <p className="text-sm text-muted-foreground">PDPA Opted In</p>
                <p className="text-2xl font-bold">0</p>
              </div>
              <div className="rounded-full bg-green-100 p-2">
                <Shield className="h-5 w-5 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Segments</p>
                <p className="text-2xl font-bold">0</p>
              </div>
              <div className="rounded-full bg-purple-100 p-2">
                <Filter className="h-5 w-5 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Blasts</p>
                <p className="text-2xl font-bold">0</p>
              </div>
              <div className="rounded-full bg-orange-100 p-2">
                <Send className="h-5 w-5 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-6">
          <TabsTrigger value="list">All Customers</TabsTrigger>
          <TabsTrigger value="segments">Segments</TabsTrigger>
          <TabsTrigger value="history">Blast History</TabsTrigger>
        </TabsList>

        <TabsContent value="list" className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search customers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <Button variant="outline">
              <Filter className="mr-2 h-4 w-4" />
              Filters
            </Button>
          </div>

          {/* Empty State */}
          <Card className="py-12 text-center">
            <CardContent>
              <Users className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
              <h3 className="text-lg font-semibold">No customers yet</h3>
              <p className="mb-4 text-sm text-muted-foreground">
                Import customers from CSV or add them manually
              </p>
              <div className="flex justify-center gap-2">
                <Button variant="outline">
                  <Upload className="mr-2 h-4 w-4" />
                  Import CSV
                </Button>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Customer
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="segments">
          <Card className="py-12 text-center">
            <CardContent>
              <Filter className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
              <h3 className="text-lg font-semibold">No segments yet</h3>
              <p className="mb-4 text-sm text-muted-foreground">
                Create segments to target specific customer groups
              </p>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Segment
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history">
          <Card className="py-12 text-center">
            <CardContent>
              <Send className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
              <h3 className="text-lg font-semibold">No blast history</h3>
              <p className="mb-4 text-sm text-muted-foreground">
                Send your first marketing blast to customers
              </p>
              <Button onClick={() => setShowBlastComposer(true)}>
                <Send className="mr-2 h-4 w-4" />
                New Blast
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Blast Composer Dialog */}
      <Dialog open={showBlastComposer} onOpenChange={setShowBlastComposer}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>New Marketing Blast</DialogTitle>
            <DialogDescription>
              Compose and send targeted messages to your customers
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* Channel Selection */}
            <div className="space-y-2">
              <Label>Channel</Label>
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1">
                  <Mail className="mr-2 h-4 w-4" />
                  Email
                </Button>
                <Button variant="outline" className="flex-1">
                  <MessageSquare className="mr-2 h-4 w-4" />
                  WhatsApp
                </Button>
                <Button variant="outline" className="flex-1">
                  <Send className="mr-2 h-4 w-4" />
                  Both
                </Button>
              </div>
            </div>

            {/* Subject */}
            <div className="space-y-2">
              <Label htmlFor="subject">Subject</Label>
              <Input id="subject" placeholder="Enter subject line..." />
            </div>

            {/* Message Body */}
            <div className="space-y-2">
              <Label htmlFor="body">Message</Label>
              <Textarea
                id="body"
                placeholder="Enter your message..."
                className="min-h-[150px]"
              />
              <p className="text-xs text-muted-foreground">
                Use merge tags: {"{{name}}"}, {"{{mobile}}"}, {"{{entity}}"}, {"{{housing}}"}
              </p>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowBlastComposer(false)}>
                Cancel
              </Button>
              <Button>
                <Eye className="mr-2 h-4 w-4" />
                Preview
              </Button>
              <Button>
                <Send className="mr-2 h-4 w-4" />
                Send Blast
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
