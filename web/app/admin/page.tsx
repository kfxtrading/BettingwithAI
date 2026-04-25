import { redirect } from 'next/navigation';
import { requireOwner } from '@/lib/accessAuth';

export const dynamic = 'force-dynamic';

export default async function AdminIndexPage() {
  await requireOwner();
  redirect('/admin/inquiries');
}
