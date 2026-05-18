import WorkspaceSidebar from "@/components/sidebar/WorkspaceSidebar";
import { UnifiedChatProvider } from "@/context/UnifiedChatContext";
import { BackgroundImage } from "@/components/BackgroundImage";

export default function WorkspaceLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <UnifiedChatProvider>
      <div className="relative flex h-screen overflow-hidden">
        <BackgroundImage />
        <WorkspaceSidebar />
        <main className="relative flex-1 overflow-hidden bg-[var(--background)]">
          {children}
        </main>
      </div>
    </UnifiedChatProvider>
  );
}
