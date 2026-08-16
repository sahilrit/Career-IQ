"""Client Success page: track contracts, invoices, and outstanding
balance per client, with a computed lifecycle stage."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from careeros_client_success import (
    ClientSuccessDivision,
    Contract,
    ContractRepository,
    DeliverableRepository,
    Invoice,
    InvoiceRepository,
    InvoiceStatus,
    MeetingNoteRepository,
    ReferralRepository,
)
from careeros_dashboard.auth_gate import require_account
from careeros_dashboard.theme import inject_theme
from careeros_opportunity_intelligence import ClientRepository

st.set_page_config(page_title="Client Success", page_icon="📈", layout="wide")

inject_theme()
account = require_account()
store = account.store
contract_repo = ContractRepository(store)
division = ClientSuccessDivision(
    contract_repo,
    DeliverableRepository(store),
    MeetingNoteRepository(store),
    InvoiceRepository(store),
    ReferralRepository(store),
)

st.title("Client success")

clients = ClientRepository(store).list_all()
if not clients:
    st.info("Promote a prospect to a client on the Freelance page first.")
    st.stop()

client_names = {client.name: client for client in clients}

with st.expander("Add a contract"), st.form("add_contract"):
    client_name = st.selectbox("Client", list(client_names))
    title = st.text_input("Contract title")
    rate = st.number_input("Rate / value", min_value=0.0, step=500.0)
    start = st.date_input("Start date", value=date.today())
    if st.form_submit_button("Add contract") and title:
        division.add_contract(
            Contract(
                client_id=client_names[client_name].id, title=title, rate=rate, start_date=start
            )
        )
        st.rerun()

for client in clients:
    contracts = contract_repo.list_for_client(client.id)
    if not contracts:
        continue
    lifecycle = division.lifecycle_stage_for(client.id)
    label = lifecycle.value.replace("_", " ") if lifecycle else "new"
    st.subheader(f"{client.name} — {label}")
    for contract in contracts:
        outstanding = division.outstanding_balance_for_contract(contract.id)
        st.write(
            f"**{contract.title}** — rate ${contract.rate:,.0f} · outstanding ${outstanding:,.0f}"
        )
        with st.form(f"invoice_{contract.id}"):
            amount = st.number_input(
                "Invoice amount", min_value=0.0, step=500.0, key=f"amt_{contract.id}"
            )
            if st.form_submit_button("Add sent invoice") and amount > 0:
                division.add_invoice(
                    Invoice(
                        contract_id=contract.id,
                        amount=amount,
                        issued_date=date.today(),
                        due_date=date.today() + timedelta(days=30),
                        status=InvoiceStatus.SENT,
                    )
                )
                st.rerun()
