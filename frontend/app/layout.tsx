import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Reliability Lab — LLM Evaluation",
  description: "A research workspace for measuring and improving language-model reliability.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
