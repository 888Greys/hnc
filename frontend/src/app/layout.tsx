import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { QuestionnaireProvider } from '@/contexts/QuestionnaireContext';
import { ClientProviders } from './providers';
import { LayoutWrapper } from '@/components/LayoutWrapper';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "HNC Legal Questionnaire System",
  description: "Digital legal questionnaire platform for efficient client data collection and AI-powered proposal generation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gray-50`}
      >
        <ClientProviders>
          <QuestionnaireProvider>
            <LayoutWrapper>
              {children}
            </LayoutWrapper>
          </QuestionnaireProvider>
        </ClientProviders>
      </body>
    </html>
  );
}