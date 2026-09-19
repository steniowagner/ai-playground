import type { Metadata } from "next";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "TriageOps | Incident Triage",
  description: "TriageOps is a live operations workspace for investigating incidents safely.",
  openGraph: {
    title: "TriageOps",
    description: "Incident triage, grounded in evidence.",
    images: [{ url: "/og.png", width: 1200, height: 630, alt: "TriageOps" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "TriageOps",
    description: "Incident triage, grounded in evidence.",
    images: ["/og.png"],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
