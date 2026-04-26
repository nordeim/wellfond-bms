"""
Dog Profile Page - Wellfond BMS
================================
7-tab dog profile with role-based access control.
"""

import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowLeft, Edit, Plus, FileText } from 'lucide-react';

import { useDog } from '@/hooks/use-dogs';
import { getSession } from '@/lib/auth';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DOG_STATUS_LABELS, DNA_STATUS_LABELS } from '@/lib/constants';
import type { Role } from '@/lib/types';

interface DogProfilePageProps {
  params: { id: string };
}

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: 'bg-[#4EAD72]',
  RETIRED: 'bg-[#4A7A94]',
  REHOMED: 'bg-[#0891B2]',
  DECEASED: 'bg-[#D94040]',
};

const DNA_STATUS_COLORS: Record<string, string> = {
  PENDING: 'bg-[#D4920A]',
  SUBMITTED: 'bg-[#0891B2]',
  RESULTS_RECEIVED: 'bg-[#4EAD72]',
  EXCLUDED: 'bg-[#D94040]',
};

// Role-based tab access
const TAB_ACCESS: Record<string, Role[]> = {
  overview: ['management', 'admin', 'sales', 'ground', 'vet'],
  health: ['management', 'admin', 'sales', 'ground', 'vet'],
  breeding: ['management', 'admin'], // Locked for Sales/Ground
  litters: ['management', 'admin'], // Locked for Sales/Ground
  media: ['management', 'admin', 'sales', 'ground', 'vet'],
  genetics: ['management', 'admin'], // Locked for Sales/Ground
  activity: ['management', 'admin', 'sales', 'ground', 'vet'],
};

function isTabLocked(tab: string, userRole: Role): boolean {
  if (!TAB_ACCESS[tab]) return false;
  return !TAB_ACCESS[tab].includes(userRole);
}

function getAgeDot(ageYears: number): { color: string; label: string } {
  if (ageYears >= 6) return { color: 'bg-[#D94040]', label: '6+ years' };
  if (ageYears >= 5) return { color: 'bg-[#D4920A]', label: '5-6 years' };
  return { color: 'bg-[#4EAD72]', label: '< 5 years' };
}

export default async function DogProfilePage({ params }: DogProfilePageProps) {
  const { id } = params;

  return (
    <div className="space-y-6">
      {/* Back Link */}
      <Link
        href="/dogs"
        className="inline-flex items-center text-sm text-[#4A7A94] hover:text-[#F97316]"
      >
        <ArrowLeft className="mr-1 h-4 w-4" />
        Back to Dogs
      </Link>

      {/* Dog Profile Content */}
      <DogProfileContent id={id} />
    </div>
  );
}

async function DogProfileContent({ id }: { id: string }) {
  const user = await getSession();
  
  if (!user) {
    return (
      <div className="rounded-lg border border-[#D94040] bg-[#D94040]/10 p-8 text-center">
        <p className="text-[#D94040]">Authentication required</p>
      </div>
    );
  }

  return <DogProfileClient id={id} userRole={user.role as Role} />;
}

function DogProfileClient({ id, userRole }: { id: string; userRole: Role }) {
  const { data: dog, isLoading } = useDog(id);

  if (isLoading) {
    return <DogProfileSkeleton />;
  }

  if (!dog) {
    notFound();
  }

  const ageDot = getAgeDot(dog.ageYears || 0);
  const isFemale = dog.gender === 'F';

  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <Card className="overflow-hidden">
        <CardContent className="p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            {/* Left: Name & Chip */}
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-[#0D2030]">{dog.name}</h1>
                <div
                  className={`h-3 w-3 rounded-full ${ageDot.color}`}
                  title={ageDot.label}
                />
              </div>
              <div className="mt-1 font-mono text-lg text-[#4A7A94]">
                {dog.microchip}
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                <Badge
                  className={`${
                    STATUS_COLORS[dog.status] || 'bg-[#4A7A94]'
                  } text-white`}
                >
                  {DOG_STATUS_LABELS[dog.status] || dog.status}
                </Badge>
                <Badge
                  className={`${
                    DNA_STATUS_COLORS[dog.dnaStatus] || 'bg-[#4A7A94]'
                  } text-white`}
                >
                  {DNA_STATUS_LABELS[dog.dnaStatus] || dog.dnaStatus}
                </Badge>
                <Badge variant="outline">{dog.breed}</Badge>
                <Badge variant="secondary">{dog.gender === 'M' ? 'Male' : 'Female'}</Badge>
                {dog.unit && <Badge variant="secondary">{dog.unit}</Badge>}
              </div>
            </div>

            {/* Right: Stats */}
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <StatCard label="Age" value={dog.ageDisplay || '-'} />
              <StatCard label="Weight" value="-" /> {/* TODO: Latest weight */}
              <StatCard label="Vaccines" value="-" /> {/* TODO: Vaccine status */}
              <StatCard label="Litters" value="-" /> {/* TODO: Litter count */}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="mt-6 flex flex-wrap gap-2">
            <Link href={`/dogs/${id}/edit`}>
              <Button variant="outline" size="sm">
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </Button>
            </Link>
            <Link href={`/dogs/${id}/health/new`}>
              <Button variant="outline" size="sm">
                <Plus className="mr-2 h-4 w-4" />
                Add Health Record
              </Button>
            </Link>
            <Link href={`/dogs/${id}/vaccines/new`}>
              <Button variant="outline" size="sm">
                <Plus className="mr-2 h-4 w-4" />
                Add Vaccine
              </Button>
            </Link>
          </div>

          {/* Pedigree Info */}
          {(dog.damId || dog.sireId) && (
            <div className="mt-6 grid gap-4 border-t border-[#C0D8EE] pt-4 sm:grid-cols-2">
              {dog.damId && (
                <div>
                  <span className="text-sm text-[#4A7A94]">Dam</span>
                  <div className="font-medium">
                    <Link
                      href={`/dogs/${dog.damId}`}
                      className="text-[#0D2030] hover:text-[#F97316] hover:underline"
                    >
                      {dog.damName || dog.damId}
                    </Link>
                  </div>
                </div>
              )}
              {dog.sireId && (
                <div>
                  <span className="text-sm text-[#4A7A94]">Sire</span>
                  <div className="font-medium">
                    <Link
                      href={`/dogs/${dog.sireId}`}
                      className="text-[#0D2030] hover:text-[#F97316] hover:underline"
                    >
                      {dog.sireName || dog.sireId}
                    </Link>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="flex-wrap">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="health">Health & Vaccines</TabsTrigger>
          {isFemale && (
            <TabsTrigger value="breeding" disabled={isTabLocked('breeding', userRole)}>
              Breeding {isTabLocked('breeding', userRole) && '🔒'}
            </TabsTrigger>
          )}
          <TabsTrigger value="litters" disabled={isTabLocked('litters', userRole)}>
            Litters & Pups {isTabLocked('litters', userRole) && '🔒'}
          </TabsTrigger>
          <TabsTrigger value="media">Media</TabsTrigger>
          <TabsTrigger value="genetics" disabled={isTabLocked('genetics', userRole)}>
            Genetics {isTabLocked('genetics', userRole) && '🔒'}
          </TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <OverviewTab dog={dog} />
        </TabsContent>

        <TabsContent value="health" className="space-y-4">
          <HealthTab dogId={id} />
        </TabsContent>

        {isFemale && (
          <TabsContent value="breeding" className="space-y-4">
            {!isTabLocked('breeding', userRole) ? (
              <BreedingTab dogId={id} />
            ) : (
              <LockedTabMessage />
            )}
          </TabsContent>
        )}

        <TabsContent value="litters" className="space-y-4">
          {!isTabLocked('litters', userRole) ? (
            <LittersTab dogId={id} />
          ) : (
            <LockedTabMessage />
          )}
        </TabsContent>

        <TabsContent value="media" className="space-y-4">
          <MediaTab dogId={id} />
        </TabsContent>

        <TabsContent value="genetics" className="space-y-4">
          {!isTabLocked('genetics', userRole) ? (
            <GeneticsTab dogId={id} />
          ) : (
            <LockedTabMessage />
          )}
        </TabsContent>

        <TabsContent value="activity" className="space-y-4">
          <ActivityTab dogId={id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center">
      <div className="text-2xl font-bold text-[#0D2030]">{value}</div>
      <div className="text-xs text-[#4A7A94]">{label}</div>
    </div>
  );
}

function LockedTabMessage() {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center p-12 text-center">
        <div className="rounded-full bg-[#C0D8EE] p-3">
          <FileText className="h-6 w-6 text-[#4A7A94]" />
        </div>
        <h3 className="mt-4 text-lg font-medium text-[#0D2030]">
          Access Restricted
        </h3>
        <p className="mt-2 text-sm text-[#4A7A94]">
          This tab requires management or admin access
        </p>
      </CardContent>
    </Card>
  );
}

function DogProfileSkeleton() {
  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <Skeleton className="h-8 w-48" />
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-6 w-24" />
            </div>
            <div className="grid grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-20" />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
      <Skeleton className="h-12 w-full" />
      <Skeleton className="h-64 w-full" />
    </div>
  );
}

// Placeholder tab components
function OverviewTab({ dog }: { dog: any }) {
  return (
    <Card>
      <CardContent className="p-6">
        <h3 className="text-lg font-medium text-[#0D2030]">Overview</h3>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm text-[#4A7A94]">Name</dt>
            <dd className="text-[#0D2030]">{dog.name}</dd>
          </div>
          <div>
            <dt className="text-sm text-[#4A7A94]">Breed</dt>
            <dd className="text-[#0D2030]">{dog.breed}</dd>
          </div>
          <div>
            <dt className="text-sm text-[#4A7A94]">Date of Birth</dt>
            <dd className="text-[#0D2030]">{dog.dob}</dd>
          </div>
          <div>
            <dt className="text-sm text-[#4A7A94]">Gender</dt>
            <dd className="text-[#0D2030]">{dog.gender === 'M' ? 'Male' : 'Female'}</dd>
          </div>
          <div>
            <dt className="text-sm text-[#4A7A94]">Colour</dt>
            <dd className="text-[#0D2030]">{dog.colour || '-'}</dd>
          </div>
          <div>
            <dt className="text-sm text-[#4A7A94]">Unit</dt>
            <dd className="text-[#0D2030]">{dog.unit || '-'}</dd>
          </div>
          {dog.notes && (
            <div className="col-span-2">
              <dt className="text-sm text-[#4A7A94]">Notes</dt>
              <dd className="text-[#0D2030]">{dog.notes}</dd>
            </div>
          )}
        </dl>
      </CardContent>
    </Card>
  );
}

function HealthTab({ dogId }: { dogId: string }) {
  return (
    <Card>
      <CardContent className="p-12 text-center">
        <p className="text-[#4A7A94]">Health records will be displayed here</p>
      </CardContent>
    </Card>
  );
}

function BreedingTab({ dogId }: { dogId: string }) {
  return (
    <Card>
      <CardContent className="p-12 text-center">
        <p className="text-[#4A7A94]">Breeding records will be displayed here</p>
      </CardContent>
    </Card>
  );
}

function LittersTab({ dogId }: { dogId: string }) {
  return (
    <Card>
      <CardContent className="p-12 text-center">
        <p className="text-[#4A7A94]">Litter records will be displayed here</p>
      </CardContent>
    </Card>
  );
}

function MediaTab({ dogId }: { dogId: string }) {
  return (
    <Card>
      <CardContent className="p-12 text-center">
        <p className="text-[#4A7A94]">Photo gallery will be displayed here</p>
      </CardContent>
    </Card>
  );
}

function GeneticsTab({ dogId }: { dogId: string }) {
  return (
    <Card>
      <CardContent className="p-12 text-center">
        <p className="text-[#4A7A94]">Genetics and COI information will be displayed here</p>
      </CardContent>
    </Card>
  );
}

function ActivityTab({ dogId }: { dogId: string }) {
  return (
    <Card>
      <CardContent className="p-12 text-center">
        <p className="text-[#4A7A94]">Activity log will be displayed here</p>
      </CardContent>
    </Card>
  );
}
