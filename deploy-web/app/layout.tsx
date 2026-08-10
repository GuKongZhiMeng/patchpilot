import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host") ?? "localhost";
  const protocol = requestHeaders.get("x-forwarded-proto") ?? (host.startsWith("localhost") ? "http" : "https");
  const image = `${protocol}://${host}/og.png`;
  return {
    title: "PatchPilot · Coding Agent Harness",
    description: "A deterministic, auditable coding-agent harness built for AI4SE.",
    icons: { icon: "/favicon.svg", shortcut: "/favicon.svg" },
    openGraph: { title: "PatchPilot", description: "Governance, feedback and stopping — implemented in code.", images: [{ url: image, width: 1536, height: 1024 }] },
    twitter: { card: "summary_large_image", title: "PatchPilot", description: "A deterministic coding-agent harness.", images: [image] },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
