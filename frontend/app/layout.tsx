import type { Metadata } from "next";
import { Inter, Barlow_Condensed, Space_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
  variable: "--font-inter",
});

const display = Barlow_Condensed({
  subsets: ["latin"],
  weight: ["700", "800"],
  variable: "--font-display",
});

const mono = Space_Mono({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "WrenchAI — DIY Repair Guides for Your Exact Car",
  description: "AI-powered step-by-step repair guides built from YouTube transcripts, repair manuals, and community knowledge. Tailored to your exact vehicle.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${display.variable} ${mono.variable}`} style={{ background: "#09090f" }}>
      <body style={{ minHeight: "100dvh" }}>{children}</body>
    </html>
  );
}
