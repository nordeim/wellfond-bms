"use client";

import { useState, useEffect } from "react";
import { Search, Dog } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useToast } from "@/components/ui/use-toast";
import { api } from "@/lib/api";

interface Dog {
  id: string;
  name: string;
  microchip: string;
  breed: string;
  gender: string;
}

interface DogSelectorProps {
  gender?: "male" | "female" | "all";
  value?: string;
  onSelect: (id: string, dog?: Dog) => void;
}

export function DogSelector({ gender = "all", value, onSelect }: DogSelectorProps) {
  const { toast } = useToast();
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [dogs, setDogs] = useState<Dog[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedDog, setSelectedDog] = useState<Dog | null>(null);

  // Fetch dogs on open
  useEffect(() => {
    if (!isOpen) return;

    const fetchDogs = async () => {
      setLoading(true);
      try {
        const response = await api.get("/api/v1/dogs/");
        let filtered = response.items || [];

        // Filter by gender if specified
        if (gender !== "all") {
          filtered = filtered.filter((d: Dog) => d.gender === gender);
        }

        setDogs(filtered);
      } catch (error) {
        toast({
          title: "Failed to load dogs",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDogs();
  }, [isOpen, gender, toast]);

  // Load selected dog info
  useEffect(() => {
    if (!value) {
      setSelectedDog(null);
      return;
    }

    const fetchDog = async () => {
      try {
        const dog = await api.get(`/api/v1/dogs/${value}`);
        setSelectedDog(dog);
      } catch (error) {
        // Ignore error for selected dog
      }
    };

    fetchDog();
  }, [value]);

  const filteredDogs = dogs.filter(
    (dog) =>
      dog.name.toLowerCase().includes(search.toLowerCase()) ||
      dog.microchip.toLowerCase().includes(search.toLowerCase())
  );

  const handleSelect = (dog: Dog) => {
    setSelectedDog(dog);
    onSelect(dog.id, dog);
    setIsOpen(false);
    setSearch("");
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          className="w-full h-14 justify-start gap-3 bg-[#1A1A1A] border-[#444444] text-white hover:bg-[#333333]"
        >
          <Dog className="w-5 h-5 text-[#888888]" />
          <span className="truncate">
            {selectedDog ? `${selectedDog.name} (${selectedDog.microchip})` : "Select dog..."}
          </span>
        </Button>
      </DialogTrigger>

      <DialogContent className="bg-[#2A2A2A] border-[#444444] text-white max-w-sm">
        <DialogHeader>
          <DialogTitle className="text-white">Select Dog</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#888888]" />
            <Input
              placeholder="Search by name or chip..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 bg-[#1A1A1A] border-[#444444] text-white"
              autoFocus
            />
          </div>

          {/* Dog list */}
          <div className="max-h-[300px] overflow-y-auto space-y-2">
            {loading ? (
              <div className="text-center py-4 text-[#888888]">Loading...</div>
            ) : filteredDogs.length === 0 ? (
              <div className="text-center py-4 text-[#888888]">No dogs found</div>
            ) : (
              filteredDogs.map((dog) => (
                <Button
                  key={dog.id}
                  variant="ghost"
                  onClick={() => handleSelect(dog)}
                  className="w-full justify-start gap-3 h-auto py-3 px-3 hover:bg-[#333333]"
                >
                  <div className="w-10 h-10 rounded-full bg-[#F37022]/20 flex items-center justify-center">
                    <Dog className="w-5 h-5 text-[#F37022]" />
                  </div>
                  <div className="text-left flex-1 min-w-0">
                    <div className="font-medium text-white truncate">{dog.name}</div>
                    <div className="text-xs text-[#888888]">
                      {dog.breed} • {dog.microchip}
                    </div>
                  </div>
                </Button>
              ))
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
