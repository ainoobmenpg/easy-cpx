import type { Metadata } from "next";
import { I18nProvider } from './lib/i18n-provider';
import "./globals.css";

export const metadata: Metadata = {
  title: "作戦級CPX - Operational Command Post Exercise",
  description: "Military command post exercise simulation game",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body className="antialiased">
        <I18nProvider>
          {children}
        </I18nProvider>
      </body>
    </html>
  );
}
