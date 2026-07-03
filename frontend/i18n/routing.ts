import {defineRouting} from 'next-intl/routing';
import {createNavigation} from 'next-intl/navigation';

export const routing = defineRouting({
  locales: ['vi', 'en'],
  defaultLocale: 'vi',
  localePrefix: 'as-needed' // Removes locale prefix for default locale if desired
});

export const {Link, redirect, usePathname, useRouter} = createNavigation(routing);
