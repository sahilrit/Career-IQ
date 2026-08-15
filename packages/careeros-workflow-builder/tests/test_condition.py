"""Tests for evaluate_condition."""

from __future__ import annotations

from careeros_workflow_builder import ComparisonOperator, Condition, evaluate_condition


def test_gt_matches():
    condition = Condition(field="score", operator=ComparisonOperator.GT, value=90)
    assert evaluate_condition(condition, {"score": 95}) is True
    assert evaluate_condition(condition, {"score": 85}) is False


def test_eq_matches_strings():
    condition = Condition(field="status", operator=ComparisonOperator.EQ, value="confirmed")
    assert evaluate_condition(condition, {"status": "confirmed"}) is True
    assert evaluate_condition(condition, {"status": "pending"}) is False


def test_missing_field_is_false():
    condition = Condition(field="score", operator=ComparisonOperator.GT, value=90)
    assert evaluate_condition(condition, {}) is False


def test_dot_path_navigates_nested_dicts():
    condition = Condition(field="company.industry", operator=ComparisonOperator.EQ, value="retail")
    payload = {"company": {"industry": "retail"}}
    assert evaluate_condition(condition, payload) is True


def test_dot_path_with_non_dict_intermediate_is_false():
    condition = Condition(field="company.industry", operator=ComparisonOperator.EQ, value="retail")
    payload = {"company": "not a dict"}
    assert evaluate_condition(condition, payload) is False


def test_type_mismatch_is_false_not_an_error():
    condition = Condition(field="score", operator=ComparisonOperator.GT, value="not a number")
    assert evaluate_condition(condition, {"score": 95}) is False


def test_lte_and_neq():
    lte = Condition(field="score", operator=ComparisonOperator.LTE, value=90)
    assert evaluate_condition(lte, {"score": 90}) is True
    neq = Condition(field="score", operator=ComparisonOperator.NEQ, value=90)
    assert evaluate_condition(neq, {"score": 85}) is True
