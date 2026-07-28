import { Sidebar } from "@/components/layout/Sidebar";

export default function ProtectedLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="flex h-screen overflow-hidden bg-[var(--background)] text-[var(--foreground)]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto relative z-10 flex flex-col pt-16 md:pt-0">
        {/* Top Header would go here eventually */}
        <div className="flex-1 overflow-auto p-6 lg:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
