import SpaceMiniNav from "@/components/space/SpaceMiniNav";
import { BackgroundImage } from "@/components/BackgroundImage";

export default function SpaceLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="relative flex h-full overflow-hidden">
      <BackgroundImage />
      <SpaceMiniNav />
      <main className="relative flex-1 overflow-y-auto bg-[var(--background)] [scrollbar-gutter:stable]">
        <div className="mx-auto max-w-5xl px-8 py-8 pb-12">{children}</div>
      </main>
    </div>
  );
}
