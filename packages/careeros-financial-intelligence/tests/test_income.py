"""Tests for IncomeRecord / IncomeRepository."""

from __future__ import annotations

from careeros_financial_intelligence import IncomeSource


def test_save_and_load_round_trips(income_repository, salary_record_factory):
    record = salary_record_factory()
    income_repository.save(record)
    assert income_repository.load(record.id) == record


def test_list_by_source_filters(income_repository, salary_record_factory):
    salary = salary_record_factory()
    freelance = salary_record_factory(source=IncomeSource.FREELANCE, source_name="Client A")
    income_repository.save(salary)
    income_repository.save(freelance)
    assert income_repository.list_by_source(IncomeSource.SALARY) == [salary]


def test_list_all_returns_every_record(income_repository, salary_record_factory):
    record = salary_record_factory()
    income_repository.save(record)
    assert income_repository.list_all() == [record]
