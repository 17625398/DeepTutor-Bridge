import UtilitySidebar from "@/components/sidebar/UtilitySidebar";
import { BackgroundImage } from "@/components/BackgroundImage";

export default function UtilityLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="relative flex h-screen overflow-hidden">
      <BackgroundImage />
      <UtilitySidebar />
      <main className="relative flex-1 overflow-hidden bg-[var(--background)]">
        {children}
      </main>
    </div>
  );
}
