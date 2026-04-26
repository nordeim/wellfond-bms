/**
 * In-Heat Log Page
 * ================
 * Mobile-optimized page for recording Draminski readings.
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
import { DogSelector } from "@/components/ground/dog-selector";
import { DraminskiGauge } from "@/components/ground/draminski-gauge";
import { useOfflineQueue } from "@/hooks/use-offline-queue";
import { useToast } from "@/components/ui/use-toast";
import { api } from "@/lib/api";

export default function HeatLogPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { queueRequest, isOnline } = useOfflineQueue();

  const [dogId, setDogId] = useState<string>("");
  const [reading, setReading] = useState<string>("");
  const [notes, setNotes] = useState<string>("");
  const [interpretation, setInterpretation] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Handle reading change and show interpretation preview
  const handleReadingChange = (value: string) => {
    setReading(value);
    const numValue = parseInt(value, 10);
    if (!isNaN(numValue) && numValue > 0) {
      // Would fetch interpretation from API
      setInterpretation({
        zone: numValue < 200 ? "EARLY" : numValue < 400 ? "RISING" : "FAST",
        trend: [
          { day: -6, value: numValue * 0.6 },
          { day: -5, value: numValue * 0.7 },
          { day: -4, value: numValue * 0.8 },
          { day: -3, value: numValue * 0.9 },
          { day: -2, value: numValue * 0.95 },
          { day: -1, value: numValue * 0.98 },
          { day: 0, value: numValue },
        ],
      });
    }
  };

  // Submit log
  const handleSubmit = async () => {
    if (!dogId || !reading) {
      toast({
        title: "Missing fields",
        description: "Please select a dog and enter a reading",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        draminski_reading: parseInt(reading, 10),
        notes,
      };

      // Use offline queue for resilience
      const response = await queueRequest(() =>
        api.post(`/api/v1/ground-logs/in-heat/${dogId}`, payload)
      );

      toast({
        title: "Log recorded",
        description: `Draminski reading saved for ${response.dog_name || "dog"}`,
      });

      // Reset form
      setDogId("");
      setReading("");
      setNotes("");
      setInterpretation(null);

      // Navigate back to ground dashboard
      router.push("/ground");
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
        <h1 className="text-2xl font-bold text-white">In-Heat Log</h1>
        <p className="text-sm text-[#888888]">Record Draminski reading</p>
      </div>

      {/* Dog Selection */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Select Dog</Label>
        <DogSelector
          gender="female"
          onSelect={(id) => setDogId(id)}
          value={dogId}
        />
      </Card>

      {/* Draminski Reading */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Draminski Reading</Label>
        <Input
          type="number"
          placeholder="Enter reading (e.g., 350)"
          value={reading}
          onChange={(e) => handleReadingChange(e.target.value)}
          className="h-14 text-2xl text-center bg-[#1A1A1A] border-[#F37022] text-white"
        />

        {/* Interpretation Gauge */}
        {interpretation && (
          <div className="mt-4">
            <DraminiGauge
              reading={parseInt(reading, 10)}
              zone={interpretation.zone}
              trend={interpretation.trend}
            />
          </div>
        )}
      </Card>

      {/* Notes */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Notes (Optional)</Label>
        <Textarea
          placeholder="Any observations..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="bg-[#1A1A1A] border-[#444444] text-white min-h-[80px]"
        />
      </Card>

      {/* Submit Button */}
      <Button
        onClick={handleSubmit}
        disabled={isSubmitting || !dogId || !reading}
        className="w-full h-14 text-lg font-semibold bg-[#F37022] hover:bg-[#E56012] text-white disabled:opacity-50"
      >
        {isSubmitting ? "Saving..." : "Save Heat Log"}
      </Button>

      {/* Offline indicator */}
      {!isOnline && (
        <Alert className="mt-4 bg-amber-900/30 border-amber-600 text-amber-100">
          You&apos;re offline. This log will sync when connection is restored.
        </Alert>
      )}
    </div>
  );
}
