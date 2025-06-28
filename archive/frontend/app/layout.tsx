import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";

export const metadata: Metadata = {
  title: "Next Top Model - Sports Analytics",
  description: "Elite sports performance analytics and player ranking platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Sidebar />
        <main className="ml-72 p-8 min-h-screen bg-gradient-to-br from-background via-background to-purple-900/20">
          {children}
        </main>
      </body>
    </html>
  );
}