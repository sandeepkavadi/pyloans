from __future__ import annotations

import pytest

from src.pyloans import Loan as pyl


@pytest.mark.parametrize(
    'test_input, expected',
    [
        (
            (0.0599, 36, 'M', 0, {3: 0, 4: 0, 5: 0, 6: 0}),
            (19.04, 36, 19.04, 36, 0.0599, 0.0599),
        ), (
            (0.1099, 48, 'M', 0, {3: 0, 4: 0, 5: 0, 6: 0}),
            (26.24, 48, 26.24, 48, 0.1099, 0.1099),
        ), (
            (0.0599, 60, 'M', 0.05, {3: 0, 4: 0, 5: 0, 6: 0}),
            (31.99, 60, 31.99, 60, 0.0787, 0.0787),
        ), (
            (0.1099, 72, 'M', 0.05, {3: 200, 4: 300, 5: 400, 6: 500}),
            (40.41, 72, 34.32, 66, 0.1247, 0.1274),
        ), (
            (0.0599, 36, 'M', 0.05, {3: 200, 4: 300, 5: 400, 6: 500}),
            (19.04, 36, 16.76, 34, 0.0914, 0.0957),
        ), (
            (0.1099, 84, 'Q', 0.05, {3: 500, 4: 400, 5: 300, 6: 200}),
            (48.76, 28, 42.12, 26, 0.1222, 0.1241),
        ), (
            (0.0599, 60, 'W', 0.1, {3: 500, 4: 400, 5: 300, 6: 200}),
            (31.72, 258, 27.12, 238, 0.0977, 0.1042),
        ), (
            (0.1099, 90, 'Y', 0.1, {3: 500, 4: 400, 5: 300, 6: 200}),
            (60.49, 8, 56.64, 8, 0.1297, 0.1311),
        ), (
            (0.0599, 36, '2W', 0.1, {3: 0, 4: 0, 5: 0, 6: 0}),
            (18.98, 78, 18.98, 78, 0.1231, 0.1231),
        ), (
            (0.1099, 48, 'BM', 0.1, {3: 200, 4: 300, 5: 400, 6: 500}),
            (26.73, 24, 23.65, 23, 0.1548, 0.1606),
        ),
    ],
)
def test_cf_mechanics(test_input: tuple, expected: tuple) -> None:
    """Test to check the cash-flows generated including, WAL and APR."""
    irt, trm, frq, fee, adp = test_input
    owal, omat, mowal, momat, oapr, moapr = expected
    l1 = pyl.Loan(
        loan_amt=20000, interest_rate=irt, term_in_months=trm,
        loan_dt='2022-12-12',
        freq=frq, fees_pct=fee, addl_pmts=adp,
    )
    df = l1.updated_cfs
    assert df.iloc[:, 1:].all().all() >= 0  # all values in the cashflows

    # dataframe,
    # including dates
    # and periods have to be non-negative
    assert round(l1.org_wal, 2) == owal
    assert round(l1.org_apr, 4) == oapr
    assert round(l1.org_maturity_period, 2) == omat
    assert round(l1.mod_wal, 2) == mowal
    assert round(l1.mod_apr, 4) == moapr
    assert round(l1.mod_maturity_period, 2) == momat


@pytest.mark.parametrize(
    'test_input, expected',
    [
        (
            ('20000', 0.0599, 36, '2022-10-10', 'M', 0, {3: 0}),
            'NA',
        ), (
            (20000, '0.0599', 36, '2022-10-10', 'M', 0, {3: 0}),
            'NA',
        ), (
            (20000, 0.0599, [36], '2022-10-10', 'M', 0, {3: 0}),
            'NA',
        ), (
            (20000, 0.0599, '36', '2022-10-10', 'M', 0, {3: 0}),
            'NA',
        ), (
            (20000, 0.0599, 36, '2022-10-10', 'M', 0, '{}'),
            'NA',
        ), (
            ('20000', '0.0599', '36', '2022-10-10', 'M', '0', '{3: 0}'),
            'NA',
        ),
    ],
)
def test_invalid_input_type(test_input: tuple, expected: tuple) -> None:
    """Test to check the inputs provided by the user conform to the
    mentioned type specifications."""
    amt, irt, trm, ln_dt, frq, fee, adp = test_input
    with pytest.raises(TypeError):
        l1 = pyl.Loan(      # noqa F841
            loan_amt=amt, interest_rate=irt, term_in_months=trm,
            loan_dt=ln_dt,
            freq=frq, fees_pct=fee, addl_pmts=adp,
        )


@pytest.mark.parametrize(
    'test_input, expected',
    [
        (
            (20e9, 0.0599, 36, '2022-10-10', 'M', 0, {3: 0}),
            'NA',
        ), (
            (20000, 1.0599, 36, '2022-10-10', 'M', 0, {3: 0}),
            'NA',
        ), (
            (20000, 2.0599, 36, '2022-13-10', 'M', 0, {3: 0}),
            'NA',
        ), (
            (20000, 0.0599, 36, '2022-10-10', 'MM', 0, {3: 0}),
            'NA',
        ), (
            (20000, 0.0599, 36, '2022-10-10', 'Month', 5, {3: 0}),
            'NA',
        ), (
            (20000, 0.0599, 36, '2022-10-10', 'M', 1.01, {36: 500}),
            'NA',
        ),
    ],
)
def test_invalid_input_value(test_input: tuple, expected: tuple) -> None:
    """Test to check the inputs provided by the user conform to the
    mentioned value range specifications."""
    amt, irt, trm, ln_dt, frq, fee, adp = test_input
    with pytest.raises(ValueError):
        l1 = pyl.Loan(      # noqa F841
            loan_amt=amt, interest_rate=irt, term_in_months=trm,
            loan_dt=ln_dt,
            freq=frq, fees_pct=fee, addl_pmts=adp,
        )


def test_full_prepayment() -> None:
    """Test to check the fully_prepay method"""
    amt, irt, trm, ln_dt, frq, fee, adp = (
        20000, 0.0599, 60, '2022-12-12',
        'W', 0.1, {3: 500, 4: 400, 6: 200},
    )
    # Instantiate a test loan object
    l1 = pyl.Loan(
            loan_amt=amt, interest_rate=irt, term_in_months=trm,
            loan_dt=ln_dt,
            freq=frq, fees_pct=fee, addl_pmts=adp,
    )
    l1.prepay_fully(10)
    assert l1.fully_prepaid == 1
    with pytest.raises(
        pyl.PrepaymentException,
        match=r'Loan is already pre-paid fully',
    ):
        l1.prepay_fully(10)
    with pytest.raises(
        pyl.PrepaymentException,
        match=r'Loan already fully pre-paid. Cannot make additional payments',
    ):
        l1.update_addl_pmts({5: 100})


def test_reset_addl_pmts() -> None:
    """Test to check the reset_addl_pmts method"""
    amt, irt, trm, ln_dt, frq, fee, adp = (
        20000, 0.0599, 60, '2022-12-12',
        'W', 0.1, {3: 500, 4: 400, 6: 200},
    )
    # Instantiate a test loan object
    l1 = pyl.Loan(
            loan_amt=amt, interest_rate=irt, term_in_months=trm,
            loan_dt=ln_dt,
            freq=frq, fees_pct=fee, addl_pmts=adp,
    )
    l1.prepay_fully(10)
    assert l1.fully_prepaid == 1
    l1.reset_addl_pmts()
    assert l1.fully_prepaid == 0
    l1.prepay_fully(10)
    assert l1.fully_prepaid == 1
