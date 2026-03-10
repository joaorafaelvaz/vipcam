import type { Metadata } from "next";
import localFont from "next/font/local";

import { AppShell } from "@/components/layout/AppShell";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "VIPCam - Barbearia VIP",
  description: "Sistema de Análise Facial em Tempo Real",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className="dark">
      <body className={`${geistSans.variable} font-sans antialiased bg-zinc-950 text-zinc-100`}>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
