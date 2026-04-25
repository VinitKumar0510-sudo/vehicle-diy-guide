import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Vehicle DIY Guide",
  description: "AI-powered repair guides for your exact vehicle",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" style={{ background: "#09090f" }}>
      <body style={{ minHeight: "100dvh" }}>{children}</body>
    </html>
  );
}
