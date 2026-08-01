import type { Metadata } from "next";
import "../globals.css";
import { Providers } from "./providers";
import {NextIntlClientProvider} from 'next-intl';
import {getMessages} from 'next-intl/server';
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "MESA Law",
  description: "AI-powered legal intelligence platform",
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
    >
      <body className="min-h-full w-full flex flex-col" suppressHydrationWarning>
        <NextIntlClientProvider messages={messages}>
          <Providers>
          <div className="flex h-screen w-full overflow-hidden">
            <main className="flex-1 w-full overflow-y-auto relative z-10 bg-background text-foreground">
              {children}
            </main>
          </div>
          <Toaster 
            position="bottom-right"
            toastOptions={{
              style: {
                background: '#18181b',
                color: '#fff',
                border: '1px solid #27272a',
              },
            }}
          />
          </Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
