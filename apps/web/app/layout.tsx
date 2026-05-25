import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "SkillBridge AI",
  description: "Career readiness assistant for resume analysis and job matching"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

