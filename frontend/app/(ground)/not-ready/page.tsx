/**
 * Not Ready Log Page
 * ==================
 * Record when a dog is not yet ready for breeding.
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
import { useOfflineQueue } from "@/hooks/use-offline-queue";
import { useToast } from "@/components/ui/use-toast";
import { api } from "@/lib/api";

export default function NotReadyPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { queueRequest, isOnline } = useOfflineQueue();

  const [dogId, setDogId] = useState<string>("");
  const [notes, setNotes] = useState<string>("");
  const [expectedDate, setExpectedDate] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!dogId) {
      toast({
        title: "Missing fields",
        description: "Please select a dog",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        notes: notes || undefined,
        expected_date: expectedDate || undefined,
      };

      const response = await queueRequest(() =>
        api.post(`/api/v1/ground-logs/not-ready/${dogId}`, payload)
      );

      toast({
        title: "Not ready recorded",
        description: expectedDate
          ? `Expected ready by ${expectedDate}`
          : "Status recorded",
      });

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

  // Set default expected date to 7 days from now
  const setDefaultDate = () => {
    const date = new Date();
    date.setDate(date.getDate() + 7);
    setExpectedDate(date.toISOString().split("T")[0]);
  };

  return (
    <div className="px-4 py-4">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Not Ready</h1>
        <p className="text-sm text-[#888888]">Mark as not ready for breeding</p>
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

      {/* Reason */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Reason (Optional)</Label>
        <Textarea
          placeholder="Why is this dog not ready?"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="bg-[#1A1A1A] border-[#444444] text-white min-h-[80px]"
        />
      </Card>

      {/* Expected Date */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Expected Ready Date</Label>
        <Input
          type="date"
          value={expectedDate}
          onChange={(e) => setExpectedDate(e.target.value)}
          className="h-14 bg-[#1A1A1A] border-[#444444] text-white"
        />
        <Button
          variant="ghost"
          onClick={setDefaultDate}
          className="mt-2 text-[#888888] hover:text-white"
        >
          Set to +7 days
        </Button>
      </Card>

      {/* Submit */}
      <Button
        onClick={handleSubmit}
        disabled={isSubmitting || !dogId}
        className="w-full h-14 text-lg font-semibold bg-[#F37022] hover:bg-[#E56012] text-white disabled:opacity-50"
      >
        {isSubmitting ? "Saving..." : "Mark Not Ready"}
      </Button>

      {!isOnline && (
        <Alert className="mt-4 bg-amber-900/30 border-amber-600 text-amber-100">
          You&apos;re offline. This log will sync when connection is restored.
        </Alert>
      )}
    </div>
  );
}
