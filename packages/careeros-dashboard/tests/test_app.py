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
