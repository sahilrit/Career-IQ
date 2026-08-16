"""Headless tests for the Streamlit pages via streamlit.testing.v1.AppTest
— runs the real page scripts in-process, no browser required.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "careeros_dashboard"


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    path = tmp_path / "data"
    monkeypatch.setenv("CAREEROS_DATA_DIR", str(path))
    # These tests cover page behavior, not the auth gate — run them in the
    # self-hosted single-user mode (test_auth_flow.py covers SaaS mode).
    monkeypatch.setenv("CAREEROS_SINGLE_USER", "1")
    yield path


def test_home_page_renders_with_no_data(data_dir):
    at = AppTest.from_file(str(_PACKAGE_ROOT / "app.py")).run()
    assert not at.exception
    assert "CareerOS" in at.title[0].value


def test_home_page_shows_create_brain_prompt_with_no_data(data_dir):
    at = AppTest.from_file(str(_PACKAGE_ROOT / "app.py")).run()
    assert any("No Career Brain yet" in info.value for info in at.info)


def test_opportunities_page_renders_with_no_data(data_dir):
    at = AppTest.from_file(str(_PACKAGE_ROOT / "pages" / "1_Opportunities.py")).run()
    assert not at.exception
    assert "Opportunities" in at.title[0].value
    assert any("Create your Career Brain first" in info.value for info in at.info)


def test_opportunities_page_shows_search_form_with_a_brain(data_dir):
    from careeros_career_brain import CareerBrain, CareerBrainRepository, Identity
    from careeros_dashboard.data_access import open_store

    store = open_store(data_dir)
    CareerBrainRepository(store).save(
        CareerBrain(identity=Identity(full_name="Ada Lovelace", email="ada@example.com"))
    )
    store.close()

    at = AppTest.from_file(str(_PACKAGE_ROOT / "pages" / "1_Opportunities.py")).run()
    assert not at.exception
    assert len(at.text_input) == 1
    assert len(at.checkbox) == 1
    assert len(at.number_input) == 1
    assert any("No applications yet" in info.value for info in at.info)


def test_career_brain_page_renders_create_form_with_no_data(data_dir):
    at = AppTest.from_file(str(_PACKAGE_ROOT / "pages" / "2_Career_Brain.py")).run()
    assert not at.exception
    assert "Career Brain" in at.title[0].value
    assert len(at.text_input) == 2


def test_career_brain_page_create_brain_form_submits(data_dir):
    at = AppTest.from_file(str(_PACKAGE_ROOT / "pages" / "2_Career_Brain.py")).run()
    at.text_input[0].input("Ada Lovelace")
    at.text_input[1].input("ada@example.com")
    at.button[0].click().run()
    assert not at.exception
    assert "ada@example.com" in at.caption[0].value


def test_dashboard_reflects_data_written_by_other_packages(data_dir):
    from careeros_career_brain import Application, CareerBrain, CareerBrainRepository, Identity
    from careeros_dashboard.data_access import open_store

    store = open_store(data_dir)
    brain = CareerBrain(
        identity=Identity(full_name="Ada Lovelace", email="ada@example.com"),
        applications=[Application(job_title="Engineer", company_name="Acme")],
    )
    CareerBrainRepository(store).save(brain)
    store.close()

    at = AppTest.from_file(str(_PACKAGE_ROOT / "app.py")).run()
    assert not at.exception
    metric_values = {metric.label: metric.value for metric in at.metric}
    assert metric_values["Applications"] == "1"


def test_freelance_page_renders(data_dir):
    at = AppTest.from_file(str(_PACKAGE_ROOT / "pages" / "7_Freelance.py")).run()
    assert not at.exception
    assert "Freelance" in at.title[0].value


def test_analytics_page_renders(data_dir):
    at = AppTest.from_file(str(_PACKAGE_ROOT / "pages" / "8_Analytics.py")).run()
    assert not at.exception
    assert "Analytics" in at.title[0].value


def test_interview_prep_page_renders(data_dir):
    at = AppTest.from_file(str(_PACKAGE_ROOT / "pages" / "9_Interview_Prep.py")).run()
    assert not at.exception


def test_offers_page_renders(data_dir):
    at = AppTest.from_file(str(_PACKAGE_ROOT / "pages" / "10_Offers.py")).run()
    assert not at.exception
    assert "Offers" in at.title[0].value


def test_network_page_renders(data_dir):
    at = AppTest.from_file(str(_PACKAGE_ROOT / "pages" / "11_Network.py")).run()
    assert not at.exception
    assert "Network" in at.title[0].value


def test_legal_page_renders(data_dir):
    at = AppTest.from_file(str(_PACKAGE_ROOT / "pages" / "12_Legal.py")).run()
    assert not at.exception
    assert "Legal" in at.title[0].value


def test_career_brain_page_shows_resume_upload_with_no_data(data_dir):
    at = AppTest.from_file(str(_PACKAGE_ROOT / "pages" / "2_Career_Brain.py")).run()
    assert not at.exception
    assert any("resume" in caption.value.lower() for caption in at.caption)
