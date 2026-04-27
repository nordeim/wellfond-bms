"use client";

/**
 * Mate Check Form Component
 * ========================
 * Phase 4: Breeding & Genetics Engine
 *
 * Form for checking COI and saturation for proposed matings.
 * Supports dual-sire breeding with optional second sire.
 */

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Loader2, AlertCircle, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { COIGauge } from "./coi-gauge";
import { SaturationBar } from "./saturation-bar";
import { useMateCheck, useMateCheckOverride, MateCheckResult } from "@/hooks/use-breeding";

// Override reasons
const OVERRIDE_REASONS = [
  "Line breeding for specific trait",
  "Preserving rare bloodline",
  "Veterinary recommendation",
  "Genetic testing shows clear",
  "Customer request (documented)",
  "Other (specify in notes)",
];

// Verdict display config
const VERDICT_CONFIG = {
  SAFE: {
    icon: Check,
    color: "text-green-600",
    bg: "bg-green-50",
    border: "border-green-200",
    title: "Safe to Mate",
    description: "COI and saturation are within acceptable ranges.",
  },
  CAUTION: {
    icon: AlertCircle,
    color: "text-amber-600",
    bg: "bg-amber-50",
    border: "border-amber-200",
    title: "Caution Advised",
    description: "Review shared ancestors and consider alternatives.",
  },
  HIGH_RISK: {
    icon: X,
    color: "text-red-600",
    bg: "bg-red-50",
    border: "border-red-200",
    title: "High Risk",
    description: "Mating not recommended. Significant inbreeding detected.",
  },
};

export function MateCheckForm() {
  // Form state
  const [damChip, setDamChip] = useState("");
  const [sire1Chip, setSire1Chip] = useState("");
  const [sire2Chip, setSire2Chip] = useState("");
  const [useDualSire, setUseDualSire] = useState(false);

  // Results state
  const [result, setResult] = useState<MateCheckResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Override modal state
  const [showOverride, setShowOverride] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");
  const [overrideNotes, setOverrideNotes] = useState("");

  // Mutations
  const { mutate: checkMate, isPending: isChecking } = useMateCheck();
  const { mutate: createOverride, isPending: isOverriding } = useMateCheckOverride();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (!damChip || !sire1Chip) {
      setError("Please enter both dam and sire microchips");
      return;
    }

    const checkData: { dam_chip: string; sire1_chip: string; sire2_chip?: string } = {
      dam_chip: damChip,
      sire1_chip: sire1Chip,
    };
    if (useDualSire && sire2Chip) {
      checkData.sire2_chip = sire2Chip;
    }

    checkMate(
      checkData,
      {
        onSuccess: (data) => {
          setResult(data);
        },
        onError: (err: any) => {
          setError(err?.message || "Failed to perform mate check");
        },
      }
    );
  };

  const handleOverride = () => {
    if (!result || !overrideReason) return;

    const overrideData: {
      dam_id: string;
      sire1_id: string;
      sire2_id?: string;
      coi_pct: number;
      saturation_pct: number;
      verdict: string;
      reason: string;
      notes?: string;
    } = {
      dam_id: result.dam_id,
      sire1_id: result.sire1_id,
      coi_pct: result.coi_pct,
      saturation_pct: result.saturation_pct,
      verdict: result.verdict,
      reason: overrideReason,
    };
    if (result.sire2_id) {
      overrideData.sire2_id = result.sire2_id;
    }
    if (overrideNotes) {
      overrideData.notes = overrideNotes;
    }

    createOverride(
      overrideData,
      {
        onSuccess: () => {
          setShowOverride(false);
          setOverrideReason("");
          setOverrideNotes("");
        },
      }
    );
  };

  const verdictConfig = result ? VERDICT_CONFIG[result.verdict] : null;
  const VerdictIcon = verdictConfig?.icon;

  return (
    <div className="space-y-6">
      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle>Mate Compatibility Check</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Dam */}
            <div className="space-y-2">
              <Label htmlFor="dam-chip">
                Dam Microchip <span className="text-red-500">*</span>
              </Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  id="dam-chip"
                  placeholder="Enter dam microchip (9-15 digits)"
                  value={damChip}
                  onChange={(e) => setDamChip(e.target.value)}
                  className="pl-10"
                  pattern="\d{9,15}"
                  required
                />
              </div>
            </div>

            {/* Sire 1 */}
            <div className="space-y-2">
              <Label htmlFor="sire1-chip">
                Sire 1 Microchip <span className="text-red-500">*</span>
              </Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  id="sire1-chip"
                  placeholder="Enter sire microchip (9-15 digits)"
                  value={sire1Chip}
                  onChange={(e) => setSire1Chip(e.target.value)}
                  className="pl-10"
                  pattern="\d{9,15}"
                  required
                />
              </div>
            </div>

            {/* Dual Sire Toggle */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="dual-sire"
                checked={useDualSire}
                onChange={(e) => setUseDualSire(e.target.checked)}
                className="rounded border-gray-300"
              />
              <Label htmlFor="dual-sire" className="text-sm cursor-pointer">
                Dual-sire breeding (add second sire)
              </Label>
            </div>

            {/* Sire 2 (conditional) */}
            <AnimatePresence>
              {useDualSire && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-2"
                >
                  <Label htmlFor="sire2-chip">Sire 2 Microchip (optional)</Label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="sire2-chip"
                      placeholder="Enter second sire microchip"
                      value={sire2Chip}
                      onChange={(e) => setSire2Chip(e.target.value)}
                      className="pl-10"
                      pattern="\d{9,15}"
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Error */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              className="w-full"
              disabled={isChecking || !damChip || !sire1Chip}
            >
              {isChecking ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Checking...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Check Compatibility
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      <AnimatePresence>
        {result && verdictConfig && VerdictIcon && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            {/* Verdict Card */}
            <Card className={cn("border-2", verdictConfig.border)}>
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className={cn("p-3 rounded-full", verdictConfig.bg)}>
                    <VerdictIcon className={cn("h-6 w-6", verdictConfig.color)} />
                  </div>
                  <div className="flex-1">
                    <h3 className={cn("text-lg font-semibold", verdictConfig.color)}>
                      {verdictConfig.title}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {verdictConfig.description}
                    </p>

                    {/* Dog Names */}
                    <div className="mt-3 text-sm">
                      <span className="font-medium">{result.dam_name}</span>
                      <span className="mx-2 text-gray-400">×</span>
                      <span className="font-medium">{result.sire1_name}</span>
                      {result.sire2_name && (
                        <>
                          <span className="mx-2 text-gray-400">/</span>
                          <span className="font-medium">{result.sire2_name}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* COI Gauge */}
              <Card>
                <CardContent className="p-6 flex justify-center">
                  <COIGauge percentage={result.coi_pct} />
                </CardContent>
              </Card>

              {/* Saturation Bar */}
              <Card>
                <CardContent className="p-6">
                  <SaturationBar
                    percentage={result.saturation_pct}
                    showLabel={true}
                  />
                </CardContent>
              </Card>
            </div>

            {/* Shared Ancestors */}
            {result.shared_ancestors.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Shared Ancestors</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {result.shared_ancestors.map((ancestor, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-2 bg-gray-50 rounded-lg text-sm"
                      >
                        <div>
                          <span className="font-medium">{ancestor.name}</span>
                          <span className="text-gray-500 ml-2">
                            ({ancestor.microchip})
                          </span>
                        </div>
                        <div className="text-right text-xs text-gray-500">
                          <div>{ancestor.relationship}</div>
                          <div>{ancestor.generations_back} gen back</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Override Button (for non-SAFE results) */}
            {result.verdict !== "SAFE" && (
              <Button
                variant="outline"
                className="w-full"
                onClick={() => setShowOverride(true)}
              >
                <AlertCircle className="mr-2 h-4 w-4" />
                Override Verdict (requires reason)
              </Button>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Override Dialog */}
      <Dialog open={showOverride} onOpenChange={setShowOverride}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Override Mate Check Verdict</DialogTitle>
            <DialogDescription>
              You are overriding a {result?.verdict} verdict. This will be logged
              to the audit trail.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Reason Select */}
            <div className="space-y-2">
              <Label htmlFor="override-reason">
                Reason <span className="text-red-500">*</span>
              </Label>
              <Select value={overrideReason} onValueChange={setOverrideReason}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a reason" />
                </SelectTrigger>
                <SelectContent>
                  {OVERRIDE_REASONS.map((reason) => (
                    <SelectItem key={reason} value={reason}>
                      {reason}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Notes */}
            <div className="space-y-2">
              <Label htmlFor="override-notes">Additional Notes</Label>
              <Textarea
                id="override-notes"
                placeholder="Provide additional context for the override..."
                value={overrideNotes}
                onChange={(e) => setOverrideNotes(e.target.value)}
                rows={4}
              />
            </div>

            {/* Current Values Display */}
            <div className="p-3 bg-gray-50 rounded-lg text-sm">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-gray-500">COI:</span>{" "}
                  <span className="font-medium">{result?.coi_pct.toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-gray-500">Saturation:</span>{" "}
                  <span className="font-medium">
                    {result?.saturation_pct.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => setShowOverride(false)}
            >
              Cancel
            </Button>
            <Button
              className="flex-1"
              onClick={handleOverride}
              disabled={!overrideReason || isOverriding}
            >
              {isOverriding ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Confirm Override"
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
