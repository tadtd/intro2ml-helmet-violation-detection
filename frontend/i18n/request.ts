import {getRequestConfig} from 'next-intl/server';
import {routing} from './routing';
import {cookies} from 'next/headers';

export default getRequestConfig(async ({requestLocale}) => {
  let locale = await requestLocale;

  if (!locale) {
    const cookieStore = await cookies();
    locale = cookieStore.get('NEXT_LOCALE')?.value;
  }

  if (!locale || !routing.locales.includes(locale as "vi" | "en")) {
    locale = routing.defaultLocale;
  }

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default
  };
});
