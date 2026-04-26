/**
 * Nursing Flag Log Page
 * =====================
 * Record nursing/concern flags with photos.
 */

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Alert } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { DogSelector } from "@/components/ground/dog-selector";
import { PhotoUpload } from "@/components/ground/photo-upload";
import { useOfflineQueue } from "@/hooks/use-offline-queue";
import { useToast } from "@/components/ui/use-toast";
import { api } from "@/lib/api";

const FLAG_TYPES = [
  { value: "not_nursing", label: "Not Nursing" },
  { value: "fading", label: "Fading Pup" },
  { value: "injury", label: "Injury" },
  { value: "abnormal", label: "Abnormal Behavior" },
  { value: "other", label: "Other Concern" },
];

const SECTIONS = ["A", "B", "C", "D", "E", "F", "G", "H"];

export default function NursingFlagPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { queueRequest, isOnline } = useOfflineQueue();

  const [dogId, setDogId] = useState<string>("");
  const [section, setSection] = useState<string>("");
  const [pupNumber, setPupNumber] = useState<string>("");
  const [flagType, setFlagType] = useState<string>("");
  const [severity, setSeverity] = useState<string>("info");
  const [photos, setPhotos] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!dogId || !section || !flagType) {
      toast({
        title: "Missing fields",
        description: "Please select a dog, section, and flag type",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        section,
        pup_number: pupNumber ? parseInt(pupNumber, 10) : undefined,
        flag_type: flagType,
        severity: severity as "info" | "warning" | "serious",
        photos: photos.length > 0 ? photos : undefined,
      };

      const response = await queueRequest(() =>
        api.post(`/api/v1/ground-logs/nursing-flag/${dogId}`, payload)
      );

      toast({
        title: severity === "serious" ? "🚨 Alert Sent" : "Flag recorded",
        description: `${flagType} in Section ${section}`,
        variant: severity === "serious" ? "destructive" : "default",
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

  return (
    <div className="px-4 py-4">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Nursing Flag</h1>
        <p className="text-sm text-[#888888]">Record pup concern</p>
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

      {/* Section & Pup */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <div className="flex gap-4">
          <div className="flex-1">
            <Label className="text-white mb-2 block">Section</Label>
            <Select value={section} onValueChange={setSection}>
              <SelectTrigger className="h-14 bg-[#1A1A1A] border-[#444444] text-white">
                <SelectValue placeholder="Sec" />
              </SelectTrigger>
              <SelectContent className="bg-[#2A2A2A] border-[#444444]">
                {SECTIONS.map((s) => (
                  <SelectItem
                    key={s}
                    value={s}
                    className="text-white hover:bg-[#333333]"
                  >
                    {s}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex-1">
            <Label className="text-[#888888] mb-2 block">Pup #</Label>
            <Input
              type="number"
              placeholder="#"
              value={pupNumber}
              onChange={(e) => setPupNumber(e.target.value)}
              className="h-14 text-center bg-[#1A1A1A] border-[#444444] text-white"
            />
          </div>
        </div>
      </Card>

      {/* Flag Type */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Concern Type</Label>
        <Select value={flagType} onValueChange={setFlagType}>
          <SelectTrigger className="h-14 bg-[#1A1A1A] border-[#444444] text-white">
            <SelectValue placeholder="Select type" />
          </SelectTrigger>
          <SelectContent className="bg-[#2A2A2A] border-[#444444]">
            {FLAG_TYPES.map((type) => (
              <SelectItem
                key={type.value}
                value={type.value}
                className="text-white hover:bg-[#333333]"
              >
                {type.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </Card>

      {/* Severity */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-3 block">Severity</Label>
        <RadioGroup
          value={severity}
          onValueChange={setSeverity}
          className="flex gap-4"
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="info" id="info" />
            <Label htmlFor="info" className="text-[#888888] cursor-pointer">
              Info
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="warning" id="warning" />
            <Label htmlFor="warning" className="text-amber-400 cursor-pointer">
              Warning
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="serious" id="serious" />
            <Label htmlFor="serious" className="text-red-400 cursor-pointer">
              Serious 🚨
            </Label>
          </div>
        </RadioGroup>
      </Card>

      {/* Photos */}
      <Card className="mb-4 bg-[#2A2A2A] border-[#333333] p-4">
        <Label className="text-white mb-2 block">Photos (Optional)</Label>
        <PhotoUpload
          photos={photos}
          onChange={setPhotos}
          maxPhotos={3}
        />
      </Card>

      {/* Submit */}
      <Button
        onClick={handleSubmit}
        disabled={isSubmitting || !dogId || !section || !flagType}
        className={`w-full h-14 text-lg font-semibold text-white disabled:opacity-50 ${
          severity === "serious"
            ? "bg-red-600 hover:bg-red-700"
            : "bg-[#F37022] hover:bg-[#E56012]"
        }`}
      >
        {isSubmitting ? "Saving..." : severity === "serious" ? "🚨 Send Alert" : "Record Flag"}
      </Button>

      {!isOnline && (
        <Alert className="mt-4 bg-amber-900/30 border-amber-600 text-amber-100">
          You&apos;re offline. This log will sync when connection is restored.
        </Alert>
      )}
    </div>
  );
}
