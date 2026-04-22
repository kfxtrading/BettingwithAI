export type SendMailInput = {
  to: string;
  subject: string;
  text: string;
  replyTo?: string;
};

export type SendMailResult =
  | { ok: true; transport: 'webhook' | 'log' }
  | { ok: false; error: string };

/**
 * Minimal mailer with zero runtime dependencies.
 *
 * - If `MAIL_WEBHOOK_URL` is set, POST a JSON envelope to that URL
 *   (works with simple HTTP-to-SMTP bridges, n8n, Zapier, Resend
 *   webhook, etc.). Optional `MAIL_WEBHOOK_TOKEN` adds an auth header.
 * - Otherwise, log the envelope to stderr and return ok (useful in
 *   dev and when running on platforms without outbound SMTP).
 */
export async function sendMail(input: SendMailInput): Promise<SendMailResult> {
  const from = process.env.MAIL_FROM ?? 'no-reply@bettingwithai.app';
  const webhook = process.env.MAIL_WEBHOOK_URL;

  if (webhook) {
    try {
      const headers: Record<string, string> = {
        'content-type': 'application/json',
      };
      if (process.env.MAIL_WEBHOOK_TOKEN) {
        headers.authorization = `Bearer ${process.env.MAIL_WEBHOOK_TOKEN}`;
      }
      const res = await fetch(webhook, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          from,
          to: input.to,
          subject: input.subject,
          text: input.text,
          reply_to: input.replyTo,
        }),
      });
      if (!res.ok) {
        return { ok: false, error: `webhook status ${res.status}` };
      }
      return { ok: true, transport: 'webhook' };
    } catch (err) {
      return { ok: false, error: String(err) };
    }
  }

  console.info(
    '[mailer] (no MAIL_WEBHOOK_URL set — logging instead)',
    JSON.stringify(input),
  );
  return { ok: true, transport: 'log' };
}
