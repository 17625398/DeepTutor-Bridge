import { BackgroundImage } from "@/components/BackgroundImage";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen bg-[var(--background)]">
      <BackgroundImage />
      {children}
    </div>
  );
}
