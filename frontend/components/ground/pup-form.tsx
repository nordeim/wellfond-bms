"use client";

import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

interface PupData {
  gender: "male" | "female";
  colour: string;
  birth_weight: number;
}

interface PupFormProps {
  index: number;
  data: PupData;
  onChange: (data: Partial<PupData>) => void;
}

export function PupForm({ index, data, onChange }: PupFormProps) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-white font-medium">Pup #{index + 1}</span>
      </div>

      {/* Gender */}
      <div>
        <Label className="text-[#888888] text-sm mb-2 block">Gender</Label>
        <RadioGroup
          value={data.gender}
          onValueChange={(value) => onChange({ gender: value as "male" | "female" })}
          className="flex gap-4"
        >
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="male" id={`male-${index}`} />
            <Label htmlFor={`male-${index}`} className="text-white cursor-pointer">
              Male ♂
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="female" id={`female-${index}`} />
            <Label htmlFor={`female-${index}`} className="text-white cursor-pointer">
              Female ♀
            </Label>
          </div>
        </RadioGroup>
      </div>

      {/* Colour */}
      <div>
        <Label className="text-[#888888] text-sm mb-2 block">Colour</Label>
        <Input
          placeholder="e.g., Golden, Cream, Black"
          value={data.colour}
          onChange={(e) => onChange({ colour: e.target.value })}
          className="bg-[#1A1A1A] border-[#444444] text-white"
        />
      </div>

      {/* Birth Weight */}
      <div>
        <Label className="text-[#888888] text-sm mb-2 block">Birth Weight (g)</Label>
        <Input
          type="number"
          placeholder="e.g., 350"
          value={data.birth_weight || ""}
          onChange={(e) => onChange({ birth_weight: parseInt(e.target.value) || 0 })}
          className="bg-[#1A1A1A] border-[#444444] text-white"
        />
      </div>
    </div>
  );
}
