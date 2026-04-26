"use client";

import { useState, useRef } from "react";
import { Camera, X, Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/use-toast";

interface PhotoUploadProps {
  photos: string[];
  onChange: (photos: string[]) => void;
  maxPhotos?: number;
}

export function PhotoUpload({ photos, onChange, maxPhotos = 5 }: PhotoUploadProps) {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    if (photos.length + files.length > maxPhotos) {
      toast({
        title: "Too many photos",
        description: `Maximum ${maxPhotos} photos allowed`,
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);

    try {
      // In a real implementation, upload to storage
      // For now, simulate with data URLs
      const newPhotos: string[] = [];

      for (const file of Array.from(files)) {
        const dataUrl = await readFileAsDataURL(file);
        newPhotos.push(dataUrl);
      }

      onChange([...photos, ...newPhotos]);
    } catch (error) {
      toast({
        title: "Upload failed",
        description: "Could not process photos",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const readFileAsDataURL = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const removePhoto = (index: number) => {
    onChange(photos.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-3">
      {/* Photo grid */}
      {photos.length > 0 && (
        <div className="grid grid-cols-3 gap-2">
          {photos.map((photo, index) => (
            <div key={index} className="relative aspect-square rounded-lg overflow-hidden">
              <img
                src={photo}
                alt={`Photo ${index + 1}`}
                className="w-full h-full object-cover"
              />
              <Button
                variant="destructive"
                size="icon"
                onClick={() => removePhoto(index)}
                className="absolute top-1 right-1 w-6 h-6 rounded-full"
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Add photo button */}
      {photos.length < maxPhotos && (
        <Button
          type="button"
          variant="outline"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="w-full h-20 border-dashed border-2 border-[#444444] bg-[#1A1A1A] hover:bg-[#333333] text-[#888888]"
        >
          {isUploading ? (
            <span>Uploading...</span>
          ) : (
            <>
              <Camera className="w-5 h-5 mr-2" />
              <span>Add Photo ({photos.length}/{maxPhotos})</span>
            </>
          )}
        </Button>
      )}

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        multiple
        capture="environment"
        onChange={handleFileSelect}
        className="hidden"
      />
    </div>
  );
}
