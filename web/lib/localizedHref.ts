import { localizedPath } from './seo';
import type { Locale } from './i18n';

/**
 * Pure helper that converts a locale-agnostic in-app path
 * (e.g. "/leagues/PL") into a locale-prefixed one ("/de/leagues/PL").
 *
 * External URLs and anchor/hash-only paths are returned unchanged.
 */
export function localizedHref(locale: Locale, path: string): string {
  if (!path) return `/${locale}`;
  if (
    path.startsWith('http://') ||
    path.startsWith('https://') ||
    path.startsWith('mailto:') ||
    path.startsWith('tel:') ||
    path.startsWith('#')
  ) {
    return path;
  }
  return localizedPath(locale, path);
}
