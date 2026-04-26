/**
 * Ground Operations Layout
 * =========================
 * Mobile-optimized layout for ground staff operations.
 * Large buttons (44px), high-contrast design, offline-aware.
 */

import { Metadata, Viewport } from "next";
import { redirect } from "next/navigation";

import { OfflineBanner } from "@/components/ground/offline-banner";
import { GroundHeader } from "@/components/ground/ground-header";
import { GroundNav } from "@/components/ground/ground-nav";
import { Toaster } from "@/components/ui/toast";
import { getCurrentUser } from "@/lib/api";

export const metadata: Metadata = {
  title: "Ground Ops | Wellfond BMS",
  description: "Mobile-optimized ground operations for breeding management",
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#F37022",
};

export default async function GroundLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Get current user (server-side)
  let user = null;
  try {
    user = await getCurrentUser();
  } catch {
    // User not authenticated
  }

  // Redirect to login if not authenticated
  if (!user) {
    redirect("/login");
  }

  // Only ground and admin roles should access ground ops
  if (user.role !== "ground" && user.role !== "admin" && user.role !== "management") {
    redirect("/dashboard");
  }

  return (
    <div className="min-h-screen bg-[#1A1A1A]">
      {/* Offline connectivity banner */}
      <OfflineBanner />

      {/* Ground ops header */}
      <GroundHeader user={user} />

      {/* Main content - full width mobile optimized */}
      <main className="min-h-[calc(100vh-140px)] pb-20">
        {children}
      </main>

      {/* Bottom navigation for quick log access */}
      <GroundNav />

      {/* Toast notifications */}
      <Toaster />
    </div>
  );
}
