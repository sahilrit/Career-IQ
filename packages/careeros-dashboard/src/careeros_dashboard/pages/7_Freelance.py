"""Freelance page: find and win client work. Add prospect businesses,
run a real audit of their public website, get a personalized pitch to
send, and track each prospect from lead to paying client.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from careeros_client_acquisition import ClientAcquisitionProgressRepository
from careeros_dashboard.auth_gate import require_account
from careeros_dashboard.data_access import primary_brain
from careeros_dashboard.freelance_actions import (
    add_company,
    audit_company,
    generate_deep_deliverables,
    list_companies,
    mark_outreach_sent,
    parse_ad_lines,
    promote_to_client,
    record_client_income,
)
from careeros_dashboard.theme import badge, inject_theme
from careeros_opportunity_intelligence import ClientRepository, RelationshipStage

st.set_page_config(page_title="Freelance", page_icon="💼", layout="wide")

inject_theme()
account = require_account()
store = account.store

st.title("Freelance")
st.caption(
    "Win client work: add a prospect business, audit their public website for "
    "fixable problems, and get a personalized pitch citing what you'd improve. "
    "Outreach is drafted for you to send — nothing is messaged automatically."
)

brain = primary_brain(store)
if brain is None:
    st.info("Create your Career Brain first, on the Career Brain page.")
    st.stop()

tab_prospects, tab_clients = st.tabs(["Prospects", "Clients & income"])

with tab_prospects:
    with st.expander("Add a prospect", expanded=not list_companies(store)):
        with st.form("add_prospect"):
            name = st.text_input("Business name")
            website = st.text_input("Website (e.g. brand.com)")
            industry = st.text_input("Industry (optional, e.g. ecommerce)")
            if st.form_submit_button("Add prospect") and name and website:
                add_company(store, name=name, website=website, industry=industry)
                st.rerun()
        st.caption("Tip: DTC / Shopify brands running ads are ideal clients for a media buyer.")

    companies = list_companies(store)
    progress_repo = ClientAcquisitionProgressRepository(store)

    if not companies:
        st.info("No prospects yet — add one above.")
    for company in companies:
        stage = progress_repo.load(company.id).current_stage
        stage_label = stage.value.replace("_", " ") if stage else "new"
        with st.expander(f"{company.name} — {stage_label}"):
            st.write(f"🌐 [{company.website}]({company.website})")

            if st.button("Run website audit & draft pitch", key=f"audit_{company.id}"):
                with st.spinner(f"Auditing {company.website} …"):
                    try:
                        outcome = audit_company(store, brain, company)
                        st.session_state[f"audit_{company.id}"] = outcome
                    except Exception as error:
                        st.error(f"Could not audit that site: {error}")

            outcome = st.session_state.get(f"audit_{company.id}")
            if outcome is not None:
                tone = "green" if outcome.qualified else "yellow"
                st.markdown(
                    f"{badge('opportunity ' + f'{outcome.opportunity_score:.0f}/100', tone)} "
                    + badge("qualified" if outcome.qualified else "low signal", tone),
                    unsafe_allow_html=True,
                )
                if outcome.signals:
                    st.write("**Findings on their site:**")
                    for finding in outcome.report.findings:
                        st.write(f"- {finding.detail} → *{finding.recommendation}*")
                else:
                    st.write("No obvious problems detected on the homepage.")
                st.text_area(
                    "Pitch (edit, then send yourself)",
                    outcome.outreach_message,
                    height=180,
                    key=f"pitch_{company.id}",
                )
                st.download_button(
                    "Download pitch (.txt)",
                    outcome.outreach_message,
                    file_name=f"pitch-{company.name}.txt",
                    key=f"dl_pitch_{company.id}",
                )
                cols = st.columns(2)
                if cols[0].button("Mark outreach sent", key=f"sent_{company.id}"):
                    mark_outreach_sent(store, company)
                    st.rerun()
                if cols[1].button("Promote to client", key=f"promote_{company.id}"):
                    promote_to_client(store, company)
                    st.success(f"{company.name} added to Clients.")

            st.divider()
            st.markdown(
                "**Full pitch kit** — deep Shopify audit, ROI projection, and a PDF proposal."
            )
            with st.form(f"deep_{company.id}"):
                st.caption("Their rough numbers (estimates are fine) power the ROI projection:")
                dcols = st.columns(3)
                monthly_visitors = dcols[0].number_input(
                    "Monthly visitors", min_value=0, value=10000, step=1000, key=f"mv_{company.id}"
                )
                conversion_rate = dcols[1].number_input(
                    "Conversion rate %", min_value=0.0, value=2.0, step=0.1, key=f"cr_{company.id}"
                )
                aov = dcols[2].number_input(
                    "Avg order value ($)",
                    min_value=0.0,
                    value=50.0,
                    step=5.0,
                    key=f"aov_{company.id}",
                )
                ads_text = st.text_area(
                    "Their Meta ads (optional) — one per line: "
                    "headline | body | CTA | landing page URL",
                    height=110,
                    key=f"ads_{company.id}",
                    help=(
                        "Copy their live ads from Meta's public Ad Library "
                        "(facebook.com/ads/library). Each ad you paste is audited for "
                        "creative, messaging, offer, and landing-page problems and folded "
                        "into the pitch."
                    ),
                )
                if st.form_submit_button("Generate full pitch kit"):
                    with st.spinner(f"Auditing {company.website} and building the pitch kit …"):
                        try:
                            st.session_state[f"kit_{company.id}"] = generate_deep_deliverables(
                                store,
                                brain,
                                company,
                                monthly_visitors=int(monthly_visitors),
                                conversion_rate=conversion_rate / 100.0,
                                average_order_value=aov,
                                ads=parse_ad_lines(ads_text),
                            )
                        except Exception as error:
                            st.error(f"Could not build the pitch kit: {error}")

            kit = st.session_state.get(f"kit_{company.id}")
            if kit is not None:
                st.write(f"**{len(kit.findings)} findings** folded into the pitch:")
                for finding in kit.findings:
                    st.write(
                        f"- _{finding.category}_ — {finding.detail} → *{finding.recommendation}*"
                    )
                if kit.roi_estimate is not None:
                    roi = kit.roi_estimate
                    rcols = st.columns(2)
                    rcols[0].metric(
                        "Projected extra monthly revenue",
                        f"${roi.projected_additional_monthly_revenue:,.0f}",
                    )
                    rcols[1].metric(
                        "Projected extra annual revenue",
                        f"${roi.projected_additional_annual_revenue:,.0f}",
                    )
                    st.caption(roi.disclaimer)
                kit_email, kit_li, kit_loom, kit_proposal = st.tabs(
                    ["Email", "LinkedIn DM", "Loom script", "Proposal"]
                )
                kit_email.text_area("Audit email", kit.email, height=220, key=f"ke_{company.id}")
                kit_li.text_area(
                    "LinkedIn message", kit.linkedin_message, height=160, key=f"kl_{company.id}"
                )
                kit_loom.text_area(
                    "Loom walkthrough script",
                    kit.loom_script,
                    height=220,
                    key=f"kloom_{company.id}",
                )
                kit_proposal.text_area(
                    "Written proposal", kit.proposal, height=260, key=f"kp_{company.id}"
                )
                try:
                    pdf_bytes = kit.pdf_path.read_bytes()
                    st.download_button(
                        "Download PDF proposal",
                        pdf_bytes,
                        file_name=f"{company.name}-proposal.pdf",
                        mime="application/pdf",
                        key=f"kpdf_{company.id}",
                    )
                except OSError:
                    st.caption("PDF was generated but could not be read back for download.")

with tab_clients:
    clients = ClientRepository(store).list_all()
    st.subheader("Clients")
    if not clients:
        st.caption("No clients yet — promote a prospect once they reply.")
    for client in clients:
        tone = {
            RelationshipStage.PROSPECT: "mute",
            RelationshipStage.CONTACTED: "blue",
            RelationshipStage.PROPOSAL_SENT: "yellow",
            RelationshipStage.ACTIVE: "green",
            RelationshipStage.PAST: "mute",
        }.get(client.stage, "mute")
        st.markdown(f"{badge(client.stage.value, tone)} **{client.name}**", unsafe_allow_html=True)

    st.divider()
    st.subheader("Record income")
    with st.form("record_income"):
        client_name = st.text_input("Client name")
        amount = st.number_input("Amount (USD)", min_value=0.0, step=100.0)
        received = st.date_input("Received date", value=date.today())
        hours = st.number_input("Hours worked (optional)", min_value=0.0, step=1.0)
        if st.form_submit_button("Add income") and client_name and amount > 0:
            record_client_income(
                store,
                client_name=client_name,
                amount=amount,
                received_date=received,
                hours_worked=hours or None,
            )
            st.success(f"Recorded ${amount:,.0f} from {client_name}.")
            st.rerun()
