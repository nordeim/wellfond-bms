/**
 * Mating Log Page
 * ===============
 * Record natural or AI matings with sire resolution by chip.
 */

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Alert } from "@/components/ui/alert";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { DogSelector } from "@/components/ground/dog-selector";
import { useOfflineQueue } from "@/hooks/use-offline-queue";
import { useToast } from "@/components/ui/use-toast";
import { api } from "@/lib/api";

export default function MateLogPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { queueRequest, isOnline } = useOfflineQueue();

  const [dogId, setDogId] = useState<string>("");
  const [sireChip, setSireChip] = useState<string>("");
  const [sire2Chip, setSire2Chip] = useState<string>("");
  const [method, setMethod] = useState<string>("natural");
  const [notes, setNotes] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!dogId || !sireChip) {
      toast({
        title: "Missing fields",
        description: "Please select a dog and enter sire microchip",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        sire_chip: sireChip,
        method: method as "natural" | "ai" | "surgical",
        sire2_chip: sire2Chip || undefined,
        notes,
      };

      await queueRequest(() =>
        api.post(`/api/v1/ground-logs/mated/${dogId}`, payload)
      );

      toast({
        title: "Mating recorded",
        description: `${method === "natural" ? "Natural" : method.toUpperCase()} mating recorded`,
      });

      router.push("/ground");
    } catch (error: any) {
      toast({
        title: "Failed to save",
        description: error.message || "Sire not found or invalid chip",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="px-4 py-4">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Mating Log</h1>
        <p className="text-sm text-[#888888]">Record breeding event</p>
      </div>

      {/* Dog Selection */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Bitch</Label>
        <DogSelector
          gender="female"
          onSelect={(id) => setDogId(id)}
          value={dogId}
        />
      </Card>

      {/* Method Selection */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-3 block">Method</Label>
        <RadioGroup
          value={method}
          onValueChange={setMethod}
          className="flex gap-4"
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="natural" id="natural" />
            <Label htmlFor="natural" className="text-white cursor-pointer">
              Natural
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="ai" id="ai" />
            <Label htmlFor="ai" className="text-white cursor-pointer">
              AI
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="surgical" id="surgical" />
            <Label htmlFor="surgical" className="text-white cursor-pointer">
              Surgical
            </Label>
          </div>
        </RadioGroup>
      </Card>

      {/* Sire Chip */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Sire Microchip</Label>
        <Input
          placeholder="Scan or type chip number"
          value={sireChip}
          onChange={(e) => setSireChip(e.target.value)}
          className="h-14 text-lg bg-[#1A1A1A] border-[#F37022] text-white font-mono"
        />
      </Card>

      {/* Optional Second Sire */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-[#888888] mb-2 block">
          Second Sire (Dual Sire - Optional)
        </Label>
        <Input
          placeholder="Second sire microchip"
          value={sire2Chip}
          onChange={(e) => setSire2Chip(e.target.value)}
          className="h-14 text-lg bg-[#1A1A1A] border-[#444444] text-white font-mono"
        />
      </Card>

      {/* Notes */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Notes (Optional)</Label>
        <Textarea
          placeholder="Tie duration, receptivity signs, etc."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="bg-[#1A1A1A] border-[#444444] text-white min-h-[80px]"
        />
      </Card>

      {/* Submit */}
      <Button
        onClick={handleSubmit}
        disabled={isSubmitting || !dogId || !sireChip}
        className="w-full h-14 text-lg font-semibold bg-[#F37022] hover:bg-[#E56012] text-white disabled:opacity-50"
      >
        {isSubmitting ? "Saving..." : "Record Mating"}
      </Button>

      {!isOnline && (
        <Alert className="mt-4 bg-amber-900/30 border-amber-600 text-amber-100">
          You&apos;re offline. This log will sync when connection is restored.
        </Alert>
      )}
    </div>
  );
}
