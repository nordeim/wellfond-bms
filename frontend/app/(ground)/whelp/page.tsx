/**
 * Whelping Log Page
 * =================
 * Record whelping events with pup details.
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
import { PupForm } from "@/components/ground/pup-form";
import { useOfflineQueue } from "@/hooks/use-offline-queue";
import { useToast } from "@/components/ui/use-toast";
import { api } from "@/lib/api";

interface PupData {
  gender: "male" | "female";
  colour: string;
  birth_weight: number;
}

export default function WhelpLogPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { queueRequest, isOnline } = useOfflineQueue();

  const [dogId, setDogId] = useState<string>("");
  const [method, setMethod] = useState<string>("natural");
  const [aliveCount, setAliveCount] = useState<number>(0);
  const [stillbornCount, setStillbornCount] = useState<number>(0);
  const [pups, setPups] = useState<PupData[]>([]);
  const [notes, setNotes] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Update pups array when count changes
  const handleAliveCountChange = (count: number) => {
    setAliveCount(count);
    const newPups: PupData[] = [];
    for (let i = 0; i < count; i++) {
      newPups.push(
        pups[i] || { gender: "male", colour: "", birth_weight: 0 }
      );
    }
    setPups(newPups);
  };

  const updatePup = (index: number, data: Partial<PupData>) => {
    const newPups = [...pups];
    newPups[index] = { ...newPups[index], ...data };
    setPups(newPups);
  };

  const handleSubmit = async () => {
    if (!dogId || aliveCount === 0) {
      toast({
        title: "Missing information",
        description: "Please select a dog and add at least one pup",
        variant: "destructive",
      });
      return;
    }

    // Validate pup data
    const incompletePups = pups.some(
      (p) => !p.gender || !p.colour || p.birth_weight <= 0
    );
    if (incompletePups) {
      toast({
        title: "Incomplete pup data",
        description: "Please fill in all pup details",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        method: method as "natural" | "c_section" | "assisted",
        alive_count: aliveCount,
        stillborn_count: stillbornCount,
        pups: pups.map((p) => ({
          gender: p.gender,
          colour: p.colour,
          birth_weight: p.birth_weight,
        })),
        notes,
      };

      await queueRequest(() =>
        api.post(`/api/v1/ground-logs/whelped/${dogId}`, payload)
      );

      toast({
        title: "Whelping recorded",
        description: `${aliveCount} pups recorded`,
      });

      router.push("/ground");
    } catch (error: unknown) {
      toast({
        title: "Failed to save",
        description: error instanceof Error ? error.message : "Please try again",
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
        <h1 className="text-2xl font-bold text-white">Whelping Log</h1>
        <p className="text-sm text-[#888888]">Record litter details</p>
      </div>

      {/* Dog Selection */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Dam</Label>
        <DogSelector
          gender="female"
          onSelect={(id) => setDogId(id)}
          value={dogId}
        />
      </Card>

      {/* Method */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-3 block">Method</Label>
        <RadioGroup
          value={method}
          onValueChange={setMethod}
          className="flex flex-wrap gap-4"
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="natural" id="natural" />
            <Label htmlFor="natural" className="text-white cursor-pointer">
              Natural
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="c_section" id="c_section" />
            <Label htmlFor="c_section" className="text-white cursor-pointer">
              C-Section
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="assisted" id="assisted" />
            <Label htmlFor="assisted" className="text-white cursor-pointer">
              Assisted
            </Label>
          </div>
        </RadioGroup>
      </Card>

      {/* Pup Counts */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <div className="flex gap-4">
          <div className="flex-1">
            <Label className="text-white mb-2 block">Alive</Label>
            <Input
              type="number"
              min={0}
              value={aliveCount}
              onChange={(e) =>
                handleAliveCountChange(parseInt(e.target.value) || 0)
              }
              className="h-14 text-2xl text-center bg-[#1A1A1A] border-[#F37022] text-white"
            />
          </div>
          <div className="flex-1">
            <Label className="text-[#888888] mb-2 block">Stillborn</Label>
            <Input
              type="number"
              min={0}
              value={stillbornCount}
              onChange={(e) =>
                setStillbornCount(parseInt(e.target.value) || 0)
              }
              className="h-14 text-2xl text-center bg-[#1A1A1A] border-[#444444] text-white"
            />
          </div>
        </div>
      </Card>

      {/* Pup Forms */}
      {pups.map((pup, index) => (
        <Card
          key={index}
          className="mb-4 bg-[#2A2A2A] border-[#333333] p-4"
        >
          <PupForm
            index={index}
            data={pup}
            onChange={(data) => updatePup(index, data)}
          />
        </Card>
      ))}

      {/* Notes */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Notes (Optional)</Label>
        <Textarea
          placeholder="Complications, observations..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="bg-[#1A1A1A] border-[#444444] text-white min-h-[80px]"
        />
      </Card>

      {/* Submit */}
      <Button
        onClick={handleSubmit}
        disabled={isSubmitting || !dogId || aliveCount === 0}
        className="w-full h-14 text-lg font-semibold bg-[#F37022] hover:bg-[#E56012] text-white disabled:opacity-50"
      >
        {isSubmitting ? "Saving..." : "Record Whelping"}
      </Button>

      {!isOnline && (
        <Alert className="mt-4 bg-amber-900/30 border-amber-600 text-amber-100">
          You&apos;re offline. This log will sync when connection is restored.
        </Alert>
      )}
    </div>
  );
}
