import { BackgroundImage } from "@/components/BackgroundImage";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen flex items-center justify-center bg-[var(--background)]">
      <BackgroundImage />
      {children}
    </div>
  );
}
