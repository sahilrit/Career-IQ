"""Offers page: add each job offer and compare them on one number — an
after-tax, quality-adjusted Opportunity Value."""

from __future__ import annotations

import streamlit as st

from careeros_dashboard.auth_gate import require_account
from careeros_dashboard.theme import inject_theme
from careeros_offer_negotiation import Offer, OfferNegotiationDivision, OfferRepository

st.set_page_config(page_title="Offers", page_icon="⚖️", layout="wide")

inject_theme()
account = require_account()
division = OfferNegotiationDivision(OfferRepository(account.store))

st.title("Offers")

_has_offers = bool(OfferRepository(account.store).list_all())
with st.expander("Add an offer", expanded=not _has_offers), st.form("add_offer"):
    cols = st.columns(2)
    company = cols[0].text_input("Company")
    title = cols[1].text_input("Job title")
    base = cols[0].number_input("Base salary", min_value=0.0, step=5000.0)
    bonus = cols[1].number_input("Bonus", min_value=0.0, step=1000.0)
    equity = cols[0].number_input("Equity value (per year)", min_value=0.0, step=1000.0)
    benefits = cols[1].number_input("Benefits value", min_value=0.0, step=1000.0)
    remote = cols[0].text_input("Remote policy (e.g. remote, hybrid)")
    scols = st.columns(3)
    stability = scols[0].slider("Stability", 1, 5, 3)
    growth = scols[1].slider("Growth", 1, 5, 3)
    reputation = scols[2].slider("Reputation", 1, 5, 3)
    if st.form_submit_button("Add offer") and company and title:
        division.add_offer(
            Offer(
                company_name=company,
                job_title=title,
                base_salary=base,
                bonus=bonus,
                equity_value=equity,
                benefits_value=benefits,
                remote_policy=remote,
                stability_score=stability,
                growth_score=growth,
                reputation_score=reputation,
            )
        )
        st.rerun()

ranked = division.compare_all()
if not ranked:
    st.info("No offers yet — add one above to compare them.")
else:
    st.subheader("Ranked by Opportunity Value")
    st.dataframe(
        [
            {
                "Rank": index + 1,
                "Company": row.offer.company_name,
                "Role": row.offer.job_title,
                "Base": f"${row.offer.base_salary:,.0f}",
                "Opportunity Value": f"${row.breakdown.opportunity_value:,.0f}",
            }
            for index, row in enumerate(ranked)
        ],
        width="stretch",
    )
    st.caption(ranked[0].breakdown.disclaimer)
