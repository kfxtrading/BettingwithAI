import { redirect } from 'next/navigation';
import { AdminLoginForm } from '@/components/AdminLoginForm';
import { isAdminAuthenticated } from '@/lib/adminAuth';

export const dynamic = 'force-dynamic';

type PageProps = {
  searchParams?: { next?: string; error?: string };
};

export default function AdminLoginPage({ searchParams }: PageProps) {
  if (isAdminAuthenticated()) {
    redirect(searchParams?.next ?? '/admin/inquiries');
  }
  return (
    <div className="mx-auto max-w-sm">
      <h1 className="text-xl font-medium tracking-tight">Admin sign-in</h1>
      <p className="mt-2 text-sm text-muted">
        Enter the admin password to manage investor inquiries.
      </p>
      <div className="mt-6">
        <AdminLoginForm
          next={searchParams?.next}
          errored={searchParams?.error === '1'}
        />
      </div>
    </div>
  );
}
