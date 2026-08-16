"""Learning Lab page: run A/B tests on your resumes, cold emails, and
subject lines, and see which variant wins."""

from __future__ import annotations

import streamlit as st

from careeros_dashboard.auth_gate import require_account
from careeros_dashboard.theme import inject_theme
from careeros_learning_lab import (
    Experiment,
    ExperimentRepository,
    ExperimentType,
    LearningLabDivision,
    OutcomeEvent,
    OutcomeEventRepository,
    OutcomeType,
    Variant,
    VariantRepository,
)

st.set_page_config(page_title="Learning Lab", page_icon="🧪", layout="wide")

inject_theme()
account = require_account()
store = account.store
division = LearningLabDivision(
    ExperimentRepository(store), VariantRepository(store), OutcomeEventRepository(store)
)

st.title("Learning Lab")

_has_experiments = bool(ExperimentRepository(store).list_all())
with st.expander("New experiment", expanded=not _has_experiments), st.form("new_experiment"):
    exp_type = st.selectbox("What are you testing?", [t.value for t in ExperimentType])
    exp_name = st.text_input("Name (e.g. 'Cold email subject line')")
    if st.form_submit_button("Create experiment") and exp_name:
        division.create_experiment(
            Experiment(experiment_type=ExperimentType(exp_type), name=exp_name)
        )
        st.rerun()

experiments = ExperimentRepository(store).list_all()
if not experiments:
    st.info("Create an experiment above to start testing.")
for experiment in experiments:
    with st.expander(f"{experiment.name} ({experiment.experiment_type.value})", expanded=True):
        variants = VariantRepository(store).list_for_experiment(experiment.id)
        for variant in variants:
            metrics = division.metrics_for_variant(variant.id)
            cols = st.columns([2, 1, 1, 1])
            cols[0].write(f"**{variant.label}**")
            cols[1].metric("Sent", metrics.sent_count)
            cols[2].metric("Responses", metrics.response_count)
            if cols[3].button("Log a response", key=f"resp_{variant.id}"):
                division.record_outcome(
                    OutcomeEvent(variant_id=variant.id, outcome_type=OutcomeType.RESPONSE)
                )
                st.rerun()
            if st.button("Log a send", key=f"sent_{variant.id}"):
                division.record_outcome(
                    OutcomeEvent(variant_id=variant.id, outcome_type=OutcomeType.SENT)
                )
                st.rerun()

        with st.form(f"variant_{experiment.id}"):
            label = st.text_input("New variant label (e.g. A, B)")
            if st.form_submit_button("Add variant") and label:
                division.add_variant(Variant(experiment_id=experiment.id, label=label))
                st.rerun()

        winner = division.winner_for_experiment(experiment.id)
        if winner:
            winning = next((v for v in variants if v.id == winner), None)
            if winning:
                st.success(f"Current winner: variant {winning.label}")
