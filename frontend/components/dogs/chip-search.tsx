/**
 * Chip Search Component
 * =====================
 * Partial microchip search with live dropdown.
 */

'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Loader2 } from 'lucide-react';

import { useDogSearch } from '@/hooks/use-dogs';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import type { Dog } from '@/lib/types';

interface ChipSearchProps {
  className?: string;
  placeholder?: string;
  onSelect?: (dog: Dog) => void;
}

export function ChipSearch({
  className,
  placeholder = 'Search by chip or name...',
  onSelect,
}: ChipSearchProps) {
  const router = useRouter();
  const { query, setQuery, results, isLoading } = useDogSearch();
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setQuery(e.target.value);
      setIsOpen(true);
      setHighlightedIndex(0);
    },
    [setQuery]
  );

  const handleSelect = useCallback(
    (dog: Dog) => {
      setIsOpen(false);
      setQuery('');
      
      if (onSelect) {
        onSelect(dog);
      } else {
        router.push(`/dogs/${dog.id}`);
      }
    },
    [onSelect, router, setQuery]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!isOpen || results.length === 0) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setHighlightedIndex((prev) =>
            prev < results.length - 1 ? prev + 1 : prev
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (results[highlightedIndex]) {
            handleSelect(results[highlightedIndex]);
          }
          break;
        case 'Escape':
          setIsOpen(false);
          break;
      }
    },
    [isOpen, results, highlightedIndex, handleSelect]
  );

  // Format chip with last 4 bold
  const formatChip = (chip: string) => {
    if (chip.length <= 4) return chip;
    const last4 = chip.slice(-4);
    const rest = chip.slice(0, -4);
    return (
      <>
        <span className="text-muted-foreground">{rest}</span>
        <span className="font-semibold">{last4}</span>
      </>
    );
  };

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          ref={inputRef}
          type="text"
          placeholder={placeholder}
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length >= 2 && setIsOpen(true)}
          className="pl-10 pr-10"
        />
        {isLoading && (
          <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-muted-foreground" />
        )}
      </div>

      {/* Dropdown */}
      {isOpen && results.length > 0 && (
        <div className="absolute z-50 mt-1 w-full rounded-md border border-[#C0D8EE] bg-white shadow-lg">
          <ul className="max-h-60 overflow-auto py-1">
            {results.map((dog, index) => (
              <li
                key={dog.id}
                onClick={() => handleSelect(dog)}
                className={cn(
                  'cursor-pointer px-4 py-2 transition-colors',
                  index === highlightedIndex
                    ? 'bg-[#E8F4FF]'
                    : 'hover:bg-[#E8F4FF]/50'
                )}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-[#0D2030]">
                      {dog.name}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {formatChip(dog.microchip)}
                    </div>
                  </div>
                  <div className="text-right text-xs">
                    <div className="text-[#0D2030]">{dog.breed}</div>
                    {dog.unit && (
                      <div className="mt-0.5 inline-flex items-center rounded bg-[#E8F4FF] px-1.5 py-0.5 text-[10px] font-medium text-[#0891B2]">
                        {dog.unit}
                      </div>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Empty state */}
      {isOpen && query.length >= 2 && !isLoading && results.length === 0 && (
        <div className="absolute z-50 mt-1 w-full rounded-md border border-[#C0D8EE] bg-white py-4 text-center text-sm text-muted-foreground shadow-lg">
          No dogs found
        </div>
      )}
    </div>
  );
}
