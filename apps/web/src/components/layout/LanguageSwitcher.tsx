'use client';

import { useLocale } from 'next-intl';
import { useRouter, usePathname } from 'next/navigation';
import { Globe } from 'lucide-react';
import { locales } from '@/i18n';

export function LanguageSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  const handleLocaleChange = (newLocale: string) => {
    if (newLocale === locale) return;

    // Strip current locale prefix from pathname if present
    const segments = pathname.split('/');
    if (locales.includes(segments[1] as typeof locales[number])) {
      segments.splice(1, 1);
    }

    // Turkish is the product default; English keeps an explicit prefix.
    const newPath = newLocale === 'tr'
      ? segments.join('/') || '/'
      : `/${newLocale}${segments.join('/') || '/'}`;

    router.replace(newPath);
    router.refresh();
  };

  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-[var(--bg-surface-hover)] border border-[var(--border-surface)] rounded-lg text-sm text-[var(--foreground)]">
      <Globe className="w-4 h-4 text-[var(--color-anthracite-400)]" />
      <select 
        value={locale} 
        onChange={(e) => handleLocaleChange(e.target.value)}
        className="bg-transparent border-0 focus:ring-0 text-[var(--foreground)] outline-none cursor-pointer"
      >
        <option value="en">English</option>
        <option value="tr">Türkçe</option>
      </select>
    </div>
  );
}
