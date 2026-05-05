/**
 * Health Observation Log Page
 * ===========================
 * Record health observations with photos.
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DogSelector } from "@/components/ground/dog-selector";
import { PhotoUpload } from "@/components/ground/photo-upload";
import { useOfflineQueue } from "@/hooks/use-offline-queue";
import { useToast } from "@/components/ui/use-toast";
import { api } from "@/lib/api";

const HEALTH_CATEGORIES = [
  { value: "vomiting", label: "Vomiting" },
  { value: "diarrhoea", label: "Diarrhoea" },
  { value: "lethargy", label: "Lethargy" },
  { value: "appetite_loss", label: "Appetite Loss" },
  { value: "lameness", label: "Lameness" },
  { value: "skin_issue", label: "Skin Issue" },
  { value: "eye_issue", label: "Eye Issue" },
  { value: "ear_issue", label: "Ear Issue" },
  { value: "breathing_issue", label: "Breathing Issue" },
  { value: "other", label: "Other" },
];

export default function HealthLogPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { queueRequest, isOnline } = useOfflineQueue();

  const [dogId, setDogId] = useState<string>("");
  const [category, setCategory] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [temperature, setTemperature] = useState<string>("");
  const [weight, setWeight] = useState<string>("");
  const [photos, setPhotos] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!dogId || !category || !description) {
      toast({
        title: "Missing fields",
        description: "Please select a dog, category, and describe the observation",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        category,
        description,
        temperature: temperature ? parseFloat(temperature) : undefined,
        weight: weight ? parseFloat(weight) : undefined,
        photos: photos.length > 0 ? photos : undefined,
      };

      await queueRequest(() =>
        api.post(`/api/v1/ground-logs/health-obs/${dogId}`, payload)
      );

      toast({
        title: "Health log recorded",
        description: `${category} observation saved`,
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
        <h1 className="text-2xl font-bold text-white">Health Observation</h1>
        <p className="text-sm text-[#888888]">Record health concern</p>
      </div>

      {/* Dog Selection */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Select Dog</Label>
        <DogSelector onSelect={(id) => setDogId(id)} value={dogId} />
      </Card>

      {/* Category */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Category</Label>
        <Select value={category} onValueChange={setCategory}>
          <SelectTrigger className="h-14 bg-[#1A1A1A] border-[#444444] text-white">
            <SelectValue placeholder="Select category" />
          </SelectTrigger>
          <SelectContent className="bg-[#2A2A2A] border-[#444444]">
            {HEALTH_CATEGORIES.map((cat) => (
              <SelectItem
                key={cat.value}
                value={cat.value}
                className="text-white hover:bg-[#333333]"
              >
                {cat.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </Card>

      {/* Description */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Description</Label>
        <Textarea
          placeholder="Describe what you observed..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="bg-[#1A1A1A] border-[#444444] text-white min-h-[100px]"
        />
      </Card>

      {/* Vitals */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <div className="flex gap-4">
          <div className="flex-1">
            <Label className="text-[#888888] mb-2 block">Temperature (°C)</Label>
            <Input
              type="number"
              step="0.1"
              placeholder="38.5"
              value={temperature}
              onChange={(e) => setTemperature(e.target.value)}
              className="h-12 bg-[#1A1A1A] border-[#444444] text-white"
            />
          </div>
          <div className="flex-1">
            <Label className="text-[#888888] mb-2 block">Weight (kg)</Label>
            <Input
              type="number"
              step="0.1"
              placeholder="28.5"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              className="h-12 bg-[#1A1A1A] border-[#444444] text-white"
            />
          </div>
        </div>
      </Card>

      {/* Photos */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Photos (Optional)</Label>
        <PhotoUpload
          photos={photos}
          onChange={setPhotos}
          maxPhotos={5}
        />
      </Card>

      {/* Submit */}
      <Button
        onClick={handleSubmit}
        disabled={isSubmitting || !dogId || !category || !description}
        className="w-full h-14 text-lg font-semibold bg-[#F37022] hover:bg-[#E56012] text-white disabled:opacity-50"
      >
        {isSubmitting ? "Saving..." : "Record Observation"}
      </Button>

      {!isOnline && (
        <Alert className="mt-4 bg-amber-900/30 border-amber-600 text-amber-100">
          You&apos;re offline. This log will sync when connection is restored.
        </Alert>
      )}
    </div>
  );
}
