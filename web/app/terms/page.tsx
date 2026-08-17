import type { Metadata } from "next";
import { LegalPage, Section } from "@/app/legal/legal";

export const metadata: Metadata = { title: "Terms of Service — CareerOS" };

export default function TermsPage() {
  return (
    <LegalPage title="Terms of Service">
      <p>
        These Terms govern your access to and use of CareerOS (the &ldquo;Service&rdquo;), operated
        by [Your Company] (&ldquo;we&rdquo;, &ldquo;us&rdquo;). By creating an account or using the
        Service, you agree to these Terms. If you do not agree, do not use the Service.
      </p>

      <Section heading="1. Your account">
        <p>
          You must provide accurate information and are responsible for keeping your credentials
          secure and for all activity under your account. You must be at least 16 years old (or the
          age of digital consent in your country).
        </p>
      </Section>

      <Section heading="2. Acceptable use">
        <p>
          You agree not to misuse the Service — including attempting to breach security, scraping
          other users&rsquo; data, sending spam, infringing others&rsquo; rights, or using the
          Service to violate any law. You are responsible for the content you submit and for how you
          use materials the Service generates.
        </p>
      </Section>

      <Section heading="3. AI-generated content">
        <p>
          The Service can generate drafts (cover letters, proposals, summaries) from your data.
          These are drafts to review and edit — you are responsible for verifying accuracy before
          you send or publish anything. Where you connect your own third-party AI key, your use of
          that provider is also subject to their terms.
        </p>
      </Section>

      <Section heading="4. Plans, billing, and refunds">
        <p>
          Paid plans are billed in advance on a recurring basis through our payment processor. You
          can cancel at any time; access continues until the end of the current billing period.
          Except where required by law, fees are non-refundable. We may change pricing with prior
          notice for future billing periods.
        </p>
      </Section>

      <Section heading="5. Your content and ownership">
        <p>
          You retain ownership of the information you put into the Service. You grant us a limited
          license to process it solely to operate and improve the Service for you. We do not sell
          your personal data.
        </p>
      </Section>

      <Section heading="6. Availability and disclaimers">
        <p>
          The Service is provided &ldquo;as is&rdquo; without warranties of any kind. We do not
          guarantee employment, income, interview, or client outcomes. To the maximum extent
          permitted by law, we are not liable for indirect or consequential damages, and our total
          liability is limited to the amount you paid us in the 12 months before the claim.
        </p>
      </Section>

      <Section heading="7. Termination">
        <p>
          You may stop using the Service at any time. We may suspend or terminate access for breach
          of these Terms or to comply with law. On termination you may request export or deletion of
          your data as described in our Privacy Policy.
        </p>
      </Section>

      <Section heading="8. Changes and contact">
        <p>
          We may update these Terms; material changes will be posted here with a new date. Questions?
          Contact us at [support@yourdomain.com].
        </p>
      </Section>
    </LegalPage>
  );
}
