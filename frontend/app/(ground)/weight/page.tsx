/**
 * Weight Log Page
 * ===============
 * Quick weight recording for dogs and pups.
 */

"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Alert } from "@/components/ui/alert";
import { DogSelector } from "@/components/ground/dog-selector";
import { useOfflineQueue } from "@/hooks/use-offline-queue";
import { useToast } from "@/components/ui/use-toast";
import { api } from "@/lib/api";

export default function WeightLogPage() {
  const { toast } = useToast();
  const { queueRequest, isOnline } = useOfflineQueue();

  const [dogId, setDogId] = useState<string>("");
  const [weight, setWeight] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!dogId || !weight) {
      toast({
        title: "Missing fields",
        description: "Please select a dog and enter weight",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        weight: parseFloat(weight),
      };

      await queueRequest(() =>
        api.post(`/api/v1/ground-logs/weight/${dogId}`, payload)
      );

      toast({
        title: "Weight recorded",
        description: `${weight}kg saved`,
      });

      // Reset for next entry
      setWeight("");
      setDogId("");
    } catch (error: any) {
      toast({
        title: "Failed to save",
        description: error.message || "Please try again",
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
        <h1 className="text-2xl font-bold text-white">Weight Log</h1>
        <p className="text-sm text-[#888888]">Quick weight recording</p>
      </div>

      {/* Dog Selection */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Select Dog</Label>
        <DogSelector onSelect={(id) => setDogId(id)} value={dogId} />
      </Card>

      {/* Weight Input */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Weight (kg)</Label>
        <Input
          type="number"
          step="0.1"
          placeholder="Enter weight"
          value={weight}
          onChange={(e) => setWeight(e.target.value)}
          className="h-20 text-4xl text-center bg-[#1A1A1A] border-[#F37022] text-white"
          autoFocus
        />
      </Card>

      {/* Quick weights */}
      <div className="grid grid-cols-4 gap-2 mb-4">
        {[0.5, 1.0, 2.0, 5.0, 10.0, 15.0, 20.0, 25.0].map((w) => (
          <Button
            key={w}
            variant="outline"
            onClick={() => setWeight(w.toString())}
            className="h-12 bg-[#2A2A2A] border-[#444444] text-white hover:bg-[#333333]"
          >
            {w}kg
          </Button>
        ))}
      </div>

      {/* Submit */}
      <Button
        onClick={handleSubmit}
        disabled={isSubmitting || !dogId || !weight}
        className="w-full h-14 text-lg font-semibold bg-[#F37022] hover:bg-[#E56012] text-white disabled:opacity-50"
      >
        {isSubmitting ? "Saving..." : "Save Weight"}
      </Button>

      {!isOnline && (
        <Alert className="mt-4 bg-amber-900/30 border-amber-600 text-amber-100">
          You&apos;re offline. This log will sync when connection is restored.
        </Alert>
      )}
    </div>
  );
}
