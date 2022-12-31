from __future__ import annotations

import datetime as dt
import math

import numpy as np
import numpy_financial as npf
import pandas as pd


class PrepaymentException(Exception):
    pass


class Loan:
    """
    ## Loan class to create instances of installment loans.

    To be initialized with the following parameters:

    1. `loan_amount:float` - The Original loan amount (principal) disbursed
    on the loan date.
    2. `int_rate:float` - original rate of interest applicable on the
    principal outstanding.
    3. `fees:float` - Origination fees charged at the time of booking,
    expressed as a % of original loan amount.
    4. `term:float` - The original term of the loan per schedule.
    5. `segment:str` - The approx risk category of the loan. Broadly mapped
    to six FICO_score groups. Configurable via config.yaml for categories'
    6. `channel:str` - Indicator variable to identify if the loan was booked
    through a free channel or a paid channel.
    7. `loan_dt:str` - Date of loan disbursement.
    8. `freq:str` - Frequency of repayment. Monthly, Quarterly etc. Valid
    values can be accessed via the class variable loan.valid_pmt_freq


        """

    valid_pmt_freq = {
        'W': 'Weekly payments', '2W': 'Fortnightly payments',
        'M': 'Monthly payments', 'BM': 'Bi-monthly payments',
        'Q': 'Quarterly payments', 'H': 'Semi-annual payments',
        'Y': 'Annual payments',
    }
    freq_offset = {
        'W': pd.DateOffset(days=7, months=0),
        '2W': pd.DateOffset(days=14, months=0),
        'M': pd.DateOffset(days=0, months=1),
        'BM': pd.DateOffset(days=0, months=2),
        'Q': 'Q', 'H': '2Q', 'Y': 'Y',
    }
    period_to_months = {
        'W': 7.0 / 30, '2W': 14.0 / 30,
        'M': 1, 'BM': 2, 'Q': 3, 'H': 6, 'Y': 12,
    }
    cols = [
        'dates', 'period', 'opening_principal', 'opening_accrued_interest',
        'current_period_interest', 'interest_pmt', 'principal_pmt',
        'additional_pmt', 'total_pmt', 'closing_principal',
    ]

    def __init__(
            self, loan_amt: float, interest_rate: float, term_in_months: float,
            loan_dt: str, freq: str = 'M', fees_pct: float = 0.0,
            addl_pmts: dict | None = None, segment: str = 'c', channel: str
            = 'free',
    ):
        self.loan_amt = loan_amt
        self.interest_rate = interest_rate
        self.term_in_months = term_in_months
        self.loan_dt = dt.datetime.strptime(loan_dt, '%Y-%m-%d')
        self.freq = freq
        self.fees_pct = fees_pct
        self.addl_pmts = addl_pmts if addl_pmts else {}
        self.segment = segment
        self.channel = channel
        self._offset = self.freq_offset[self.freq]
        self._periods = math.ceil(
            self.term_in_months / self.period_to_months[self.freq],
        )
        self._period_interest_rate = self.interest_rate * self \
            .period_to_months[self.freq] / 12
        self.pmt = -npf.pmt(
            self._period_interest_rate,
            self._periods, self.loan_amt,
        )
        self.fully_prepaid = 0
        self.updated_cfs = self.original_cfs = self.get_org_cfs()
        self.updated_cfs = self._get_mod_cfs()

    def get_org_cfs(self) -> pd.DataFrame:
        """Method to get the original scheduled of cashflows for a given loan.
        For monthly frequency (most common), it assumes that the dues date are
        on the same day of the month every month.
        Usage: loan.get_schedule()"""
        df = pd.DataFrame()
        df['dates'] = pd.Series(
            pd.date_range(
                self.loan_dt, freq=self._offset, periods=self._periods + 1,
            ),
        ).shift(-1).dropna()
        df['period'] = df.index + 1
        df['interest_pmt'] = - \
            npf.ipmt(
                self._period_interest_rate,
                df['period'], self._periods, self.loan_amt,
            )
        df['principal_pmt'] = - \
            npf.ppmt(
                self._period_interest_rate,
                df['period'], self._periods, self.loan_amt,
            )
        df['closing_principal'] = self.loan_amt - df['principal_pmt'].cumsum()
        df['opening_principal'] = df['closing_principal'].shift(
            1,
        ).fillna(self.loan_amt)
        df['additional_pmt'] = pd.Series(
            self.addl_pmts,
            index=df.index,
        ).fillna(0)
        df['current_period_interest'] = df['interest_pmt']
        df['opening_accrued_interest'] = 0
        df['closing_accrued_interest'] = 0
        df['additional_pmt'] = 0
        df['total_pmt'] = df['interest_pmt'] + df['principal_pmt'] + \
            df['additional_pmt']
        df = df[self.cols]
        return df

    def _wal(self, _df: pd.DataFrame) -> float:
        return ((_df['opening_principal'] - _df['closing_principal']) *
                _df['period']).sum() * \
            self.period_to_months[self.freq] / self.loan_amt

    @property
    def org_wal(self) -> float:
        """Returns the weighted average life of the loan (in months) based on
        a given cashflow schedule.
        The [WAL](https://en.wikipedia.org/wiki/Weighted-average_life) of the
        loan can be defined as the average number of months it takes for the
        principal of the loan
        to be repaid, if the borrower repays by the original schedule."""
        return self._wal(self.get_org_cfs())

    @property
    def org_apr(self) -> float:
        """Returns the Annual percentage rate (APR) of the loan based on the
        original cashflow schedule.
        The [APR](https://en.wikipedia.org/wiki/Annual_percentage_rate) of the
        loan can be defined as the
        total financial cost of the loan (including fees) divided by the WAL of
        the loan."""
        return self.interest_rate + (self.fees_pct / (self.org_wal / 12))

    def _merge_addl_pmt(self, addl_pmt_update: dict) -> dict:
        keys = set(list(self.addl_pmts.keys()) + list(addl_pmt_update.keys()))
        return {
            k: self.addl_pmts.get(k, 0.0) + addl_pmt_update.get(k, 0.0)
            for k in keys
        }

    def _get_mod_cfs(self) -> pd.dataFrame:
        if self.fully_prepaid == 1:
            return self.updated_cfs
        else:
            df = self.updated_cfs
            if self.addl_pmts:
                cl_p = self.loan_amt
                cl_ai = 0  # accrued interest for 1st period
                df['additional_pmt'] = pd.Series(
                    {k-1: v for k, v in self.addl_pmts.items()},
                    index=df.index,
                ).fillna(0)
                for idx, row in df.iterrows():
                    row.loc['opening_principal'] = cl_p
                    row.loc['opening_accrued_interest'] = cl_ai
                    row.loc['current_period_interest'] = \
                        row.loc['opening_principal'] * \
                        self._period_interest_rate
                    row.loc['total_pmt'] = min(
                        row.loc['interest_pmt'] +
                        row.loc['principal_pmt'] +
                        row.loc['additional_pmt'],
                        row.loc['opening_principal'] +
                        row.loc['opening_accrued_interest'] +
                        row.loc['current_period_interest'],
                    )
                    row.loc['closing_accrued_interest'] = \
                        max(
                            0,
                            row.loc['opening_accrued_interest'] +
                            row.loc['current_period_interest'] -
                            row.loc['total_pmt'],
                        )
                    cl_ai = row.loc['closing_accrued_interest']
                    row.loc['closing_principal'] = \
                        max(
                            0,
                            row.loc['opening_principal'] +
                            row.loc['opening_accrued_interest'] +
                            row.loc['current_period_interest'] -
                            row.loc['total_pmt'],
                        )
                    cl_p = row.loc['closing_principal']
                    df.loc[idx, self.cols] = row.loc[self.cols]
            self.updated_cfs = df
            return self.updated_cfs

    @property
    def mod_wal(self) -> float:
        return self._wal(self.updated_cfs)

    @property
    def mod_apr(self) -> float:
        return self.interest_rate + (self.fees_pct / (self.mod_wal / 12))

    def _maturity(self) -> np.int64:
        _cfs = self.updated_cfs
        # numpy_financial precision issue
        return _cfs[_cfs.closing_principal <= 1e-9].period.min()

    @property
    def org_maturity_period(self):
        return self._periods

    @property
    def mod_maturity_period(self):
        return self._maturity()

    def prepay_fully(self, period: int) -> pd.DataFrame:
        if self.fully_prepaid == 1:
            raise PrepaymentException('Loan is already pre-paid fully')
        else:
            df = self.updated_cfs
            prepay_amt = df.loc[period-1, 'closing_principal']
            self.addl_pmts = self._merge_addl_pmt({period: prepay_amt})
            self.updated_cfs = self._get_mod_cfs()
            self.fully_prepaid = 1
            return self.updated_cfs

    def update_addl_pmts(self, addl_pmt_update: dict) -> pd.DataFrame:
        if self.fully_prepaid == 1:
            raise PrepaymentException(
                'Loan already fully pre-paid. Cannot '
                'make additional payments',
            )
        elif self.addl_pmts:
            self.addl_pmts = self._merge_addl_pmt(addl_pmt_update)
            self.updated_cfs = self._get_mod_cfs()
            return self.updated_cfs
        else:
            self.addl_pmts = addl_pmt_update
            self.updated_cfs = self._get_mod_cfs()
            return self.updated_cfs

    def reset_addl_pmts(self) -> None:
        self.addl_pmts = {}
        self.updated_cfs = self._get_mod_cfs()
