"use client";

/**
 * Breeding Records Page
 * =====================
 * Phase 4: Breeding & Genetics Engine
 *
 * List and manage breeding records with filters and detail view.
 */

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Plus, Search, Filter, Calendar, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useBreedingRecords } from "@/hooks/use-breeding";
import type { BreedingRecordListItem } from "@/hooks/use-breeding";

export default function BreedingRecordsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "has_litter">("all");
  const [selectedRecord, setSelectedRecord] = useState<BreedingRecordListItem | null>(null);

  const { data: recordsData, isLoading } = useBreedingRecords({
    has_litter: statusFilter === "has_litter" ? true : undefined,
  });

  const records = recordsData?.records || [];

  const filteredRecords = useMemo(() => {
    let filtered = records;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (record) =>
          record.dam_name.toLowerCase().includes(query) ||
          record.dam_microchip.includes(query) ||
          record.sire1_name.toLowerCase().includes(query) ||
          record.sire1_microchip.includes(query)
      );
    }
    return filtered;
  }, [records, searchQuery]);

  return (
    <div className="container mx-auto py-6 px-4">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <h1 className="text-2xl font-bold text-[#0D2030] flex items-center gap-2">
          <Calendar className="h-6 w-6 text-[#F97316]" />
          Breeding Records
        </h1>
        <p className="text-sm text-[#0D2030]/60 mt-1">
          Track breeding events and manage litters
        </p>
      </motion.div>

      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search by name or microchip..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        <Select
          value={statusFilter}
          onValueChange={(value: "all" | "has_litter") => setStatusFilter(value)}
        >
          <SelectTrigger className="w-[160px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Records</SelectItem>
            <SelectItem value="has_litter">With Litter</SelectItem>
          </SelectContent>
        </Select>

        <Button>
          <Plus className="h-4 w-4 mr-2" />
          New Breeding
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Dam</TableHead>
                <TableHead>Sire</TableHead>
                <TableHead>Method</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto text-gray-400" />
                  </TableCell>
                </TableRow>
              ) : filteredRecords.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                    No breeding records found
                  </TableCell>
                </TableRow>
              ) : (
                filteredRecords.map((record) => (
                  <TableRow
                    key={record.id}
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => setSelectedRecord(record)}
                  >
                    <TableCell>{new Date(record.date).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <div className="font-medium">{record.dam_name}</div>
                      <div className="text-xs text-gray-500">{record.dam_microchip}</div>
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">{record.sire1_name}</div>
                      <div className="text-xs text-gray-500">{record.sire1_microchip}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{record.method}</Badge>
                    </TableCell>
                    <TableCell>
                      {record.has_litter ? (
                        <Badge className="bg-[#4EAD72]">Litter</Badge>
                      ) : (
                        <Badge variant="secondary">Pending</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={!!selectedRecord} onOpenChange={() => setSelectedRecord(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Breeding Record</DialogTitle>
          </DialogHeader>
          {selectedRecord && (
            <div className="space-y-4">
              <div className="text-sm">
                <span className="text-gray-500">Date:</span>{" "}
                {new Date(selectedRecord.date).toLocaleDateString()}
              </div>
              <div className="text-sm">
                <span className="text-gray-500">Dam:</span>{" "}
                {selectedRecord.dam_name}
              </div>
              <div className="text-sm">
                <span className="text-gray-500">Sire:</span>{" "}
                {selectedRecord.sire1_name}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
