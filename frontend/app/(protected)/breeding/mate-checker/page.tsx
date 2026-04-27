"use client";

/**
 * Mate Checker Page
 * =================
 * Phase 4: Breeding & Genetics Engine
 *
 * Main page for the mate checker tool with form and override history.
 */

import { useState } from "react";
import { motion } from "framer-motion";
import { Calculator, History, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { MateCheckForm } from "@/components/breeding/mate-check-form";
import { COIBadge } from "@/components/breeding/coi-gauge";
import { SaturationBadge } from "@/components/breeding/saturation-bar";
import { useMateCheckHistory } from "@/hooks/use-breeding";

export default function MateCheckerPage() {
  const [showHistory, setShowHistory] = useState(false);

  // Fetch override history
  const { data: historyData, isLoading: isLoadingHistory } = useMateCheckHistory({
    page: 1,
    per_page: 10,
  });

  const overrides = historyData?.overrides || [];

  return (
    <div className="container mx-auto py-6 px-4 max-w-4xl">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <h1 className="text-2xl font-bold text-[#0D2030] flex items-center gap-2">
          <Calculator className="h-6 w-6 text-[#F97316]" />
          Mate Checker
        </h1>
        <p className="text-sm text-[#0D2030]/60 mt-1">
          Calculate COI and farm saturation before breeding. Supports dual-sire
          breeding scenarios.
        </p>
      </motion.div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Mate Check Form */}
        <div className="lg:col-span-2">
          <MateCheckForm />
        </div>

        {/* Right Column - Info Cards */}
        <div className="space-y-4">
          {/* COI Info Card */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">COI Thresholds</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[#4EAD72]" />
                    <span>SAFE</span>
                  </div>
                  <span className="text-gray-500">&lt; 6.25%</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[#D4920A]" />
                    <span>CAUTION</span>
                  </div>
                  <span className="text-gray-500">6.25% - 12.5%</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[#D94040]" />
                    <span>HIGH RISK</span>
                  </div>
                  <span className="text-gray-500">&gt; 12.5%</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Saturation Info Card */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">
                Saturation Thresholds
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[#4EAD72]" />
                    <span>SAFE</span>
                  </div>
                  <span className="text-gray-500">&lt; 15%</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[#D4920A]" />
                    <span>CAUTION</span>
                  </div>
                  <span className="text-gray-500">15% - 30%</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[#D94040]" />
                    <span>HIGH RISK</span>
                  </div>
                  <span className="text-gray-500">&gt; 30%</span>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-3">
                % of active dogs in entity sharing sire ancestry
              </p>
            </CardContent>
          </Card>

          {/* Info Note */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
            <p className="font-medium mb-1">Why check before mating?</p>
            <p className="text-xs">
              High COI increases risk of genetic disorders. Monitoring saturation
              prevents overuse of popular sires.
            </p>
          </div>
        </div>
      </div>

      {/* Override History Section */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="mt-8"
      >
        <Button
          variant="ghost"
          className="w-full flex items-center justify-center gap-2 py-4"
          onClick={() => setShowHistory(!showHistory)}
        >
          <History className="h-4 w-4" />
          <span>Override History</span>
          {showHistory ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </Button>

        {showHistory && (
          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="text-lg">Recent Overrides</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoadingHistory ? (
                <div className="text-center py-8 text-gray-500">
                  Loading history...
                </div>
              ) : overrides.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No overrides recorded yet.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Date</TableHead>
                        <TableHead>Mating</TableHead>
                        <TableHead>COI</TableHead>
                        <TableHead>Saturation</TableHead>
                        <TableHead>Staff</TableHead>
                        <TableHead>Reason</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {overrides.map((override) => (
                        <TableRow key={override.id}>
                          <TableCell className="text-xs whitespace-nowrap">
                            {new Date(override.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <div className="text-sm">
                              {override.dam_name} × {override.sire1_name}
                              {override.sire2_name && ` / ${override.sire2_name}`}
                            </div>
                          </TableCell>
                          <TableCell>
                            <COIBadge percentage={override.coi_pct} />
                          </TableCell>
                          <TableCell>
                            <SaturationBadge percentage={override.saturation_pct} />
                          </TableCell>
                          <TableCell>
                            <div className="text-sm">{override.staff_name}</div>
                            <div className="text-xs text-gray-500">
                              {override.staff_role}
                            </div>
                          </TableCell>
                          <TableCell>
                            <span
                              className="text-xs truncate max-w-[150px] block"
                              title={override.override_reason}
                            >
                              {override.override_reason}
                            </span>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </motion.div>
    </div>
  );
}
