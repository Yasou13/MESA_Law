import type { Metadata } from "next";
import "../globals.css";
import { Providers } from "./providers";
import {NextIntlClientProvider} from 'next-intl';
import {getMessages} from 'next-intl/server';
import { Toaster } from "react-hot-toast";
import "@fontsource-variable/ibm-plex-sans";
import "@fontsource-variable/source-serif-4";

export const metadata: Metadata = {
  title: "MESA Law",
  description: "Matter-scoped legal document review and sourced Q&A",
};

export default async function RootLayout({
  children,
  params,
}: Readonly<{
  children: React.ReactNode;
  params: Promise<{locale: string}>;
}>) {
  const { locale } = await params;
  const messages = await getMessages();

  return (
    <html
      lang={locale}
      className="h-full w-full antialiased"
      suppressHydrationWarning
    >
      <body className="min-h-full w-full flex flex-col" suppressHydrationWarning>
        <NextIntlClientProvider messages={messages}>
          <Providers>
          <div className="flex h-screen w-full overflow-hidden">
            <div className="flex-1 w-full overflow-y-auto relative z-10 bg-background text-foreground">
              {children}
            </div>
          </div>
          <Toaster
            position="bottom-right"
            toastOptions={{
              style: {
                background: 'var(--surface-raised)',
                color: 'var(--foreground)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                boxShadow: 'var(--shadow-sm)',
              },
            }}
          />
          </Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
