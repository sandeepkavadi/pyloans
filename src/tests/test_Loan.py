from __future__ import annotations

import pyloans.Loan as pyl
import pytest


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ((0.0599, 36, 'M', 0.05), (36, 0.0914, 19.04)),
        ((0.1099, 60, 'W', 0.10), (258, 0.1463, 32.97)),
        ((0.1099, 48, 'Q', 0.10), (16, 0.1540, 27.22)),
    ],
)
def test_cf_mechanics(test_input: tuple, expected: tuple) -> None:
    """Test to check the cah-flows generated including, WAL and APR."""
    ir, t, frq, fee = test_input
    exp_rows, exp_apr, exp_wal = expected
    l1 = pyl.Loan(
        loan_amt=10000, interest_rate=ir, term_in_months=t,
        loan_dt='2022-12-12',
        freq=frq, fees_pct=fee,
    )
    df = l1.get_cfsch()
    assert df.shape[0] == exp_rows
    assert round(l1.apr, 4) == exp_apr
    assert round(l1.wal, 2) == exp_wal
