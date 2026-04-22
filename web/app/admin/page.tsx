import { redirect } from 'next/navigation';
import { isAdminAuthenticated } from '@/lib/adminAuth';

export const dynamic = 'force-dynamic';

export default function AdminIndexPage() {
  if (!isAdminAuthenticated()) {
    redirect('/admin/login');
  }
  redirect('/admin/inquiries');
}
