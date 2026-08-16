"""Legal page: Terms of Service and Privacy Policy. Operators set the
company name and contact via env (CAREEROS_COMPANY_NAME, CAREEROS_SUPPORT_EMAIL).
This is a starting template — have it reviewed before you rely on it.
"""

from __future__ import annotations

import os
from datetime import date

import streamlit as st

from careeros_dashboard.theme import inject_theme

st.set_page_config(page_title="Legal", page_icon="📜", layout="wide")

inject_theme()

company = os.environ.get("CAREEROS_COMPANY_NAME", "CareerOS")
support = os.environ.get("CAREEROS_SUPPORT_EMAIL", "support@example.com")
today = f"{date.today():%B %d, %Y}"

st.title("Legal")
terms_tab, privacy_tab = st.tabs(["Terms of Service", "Privacy Policy"])

with terms_tab:
    st.markdown(
        f"""
### {company} — Terms of Service
_Last updated: {today}_

**1. The service.** {company} helps you build a career profile, discover
job and freelance opportunities, generate application and outreach
materials, and (optionally) submit applications on your behalf.

**2. Your account.** You are responsible for the accuracy of the
information you provide and for activity under your account. Keep your
password secure.

**3. Acceptable use.** You will only apply to opportunities and contact
businesses you are genuinely interested in, and you will comply with the
terms of any third-party site the service interacts with on your behalf.
You will not use the service to send spam or to misrepresent yourself.

**4. Automated actions.** When you enable autopilot, you authorize
{company} to submit applications using the information in your profile.
The service will not bypass logins, captchas, or bot-detection; those
are handed back to you.

**5. No guarantee.** {company} does not guarantee interviews, offers,
clients, or income. Projections and scores are estimates, not promises.

**6. Billing.** Paid plans renew until canceled. Fees are non-refundable
except where required by law.

**7. Termination.** You may delete your account at any time from the
Account page. We may suspend accounts that violate these terms.

**8. Contact.** {support}
        """
    )

with privacy_tab:
    st.markdown(
        f"""
### {company} — Privacy Policy
_Last updated: {today}_

**What we store.** The career and business information you enter (your
profile, applications, prospects, notes), your account email, and a
hashed password. We never store your password in plain text.

**Isolation.** Your data lives in your own workspace and is not visible
to other customers.

**How we use it.** Solely to provide the service — to generate your
resumes, pitches, and applications, and to show you your own analytics.

**Third parties.** When you search or apply, the service contacts public
job boards and the sites you target. We do not sell your data.

**Your rights.** You can export all your data as JSON and permanently
delete your account at any time from the Account page.

**Contact.** {support}
        """
    )

st.caption("This is a template to get you started — have a lawyer review it before you rely on it.")
