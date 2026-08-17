import type { Metadata } from "next";
import { LegalPage, Section } from "@/app/legal/legal";

export const metadata: Metadata = { title: "Privacy Policy — CareerOS" };

export default function PrivacyPage() {
  return (
    <LegalPage title="Privacy Policy">
      <p>
        This Policy explains what CareerOS, operated by [Your Company], collects, how we use it, and
        the choices you have. We aim to collect the minimum needed to run the Service.
      </p>

      <Section heading="1. What we collect">
        <p>
          <strong>Account data</strong> (name, email, password hash). <strong>Career data</strong>{" "}
          you enter or upload (résumé, experience, skills, projects, clients, income you choose to
          log). <strong>Usage data</strong> (basic logs needed to operate and secure the Service).
        </p>
      </Section>

      <Section heading="2. How we use it">
        <p>
          To provide the Service — storing your Career Brain, generating drafts, running searches —
          to secure and improve it, and to process payments. We do not sell your personal data or
          use it to train third-party models.
        </p>
      </Section>

      <Section heading="3. Third-party processors">
        <p>
          We rely on a small number of providers to run the Service: hosting/database, our payment
          processor for billing, email delivery, and — only if you connect your own key — your
          chosen AI provider, to which the relevant prompt text is sent to generate your drafts.
          Each processes data on our or your behalf under their own terms.
        </p>
      </Section>

      <Section heading="4. Security">
        <p>
          Passwords are hashed, sessions are revocable, and secrets you store (such as an API key)
          are encrypted at rest. No system is perfectly secure, but we work to protect your data and
          isolate each workspace&rsquo;s data from others.
        </p>
      </Section>

      <Section heading="5. Retention and your rights">
        <p>
          We keep your data while your account is active. You can request a copy of your data or its
          deletion at any time; deleting your account removes your workspace data. Depending on your
          location you may have additional rights (access, correction, portability, objection).
        </p>
      </Section>

      <Section heading="6. International transfers &amp; children">
        <p>
          Your data may be processed in countries other than yours. The Service is not directed to
          children under 16.
        </p>
      </Section>

      <Section heading="7. Contact">
        <p>
          For privacy requests, contact us at [privacy@yourdomain.com]. We will respond within a
          reasonable timeframe.
        </p>
      </Section>
    </LegalPage>
  );
}
