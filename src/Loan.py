from __future__ import annotations

import math

import arrow
import numpy_financial as npf
import pandas as pd


class Loan:
    """Loan class to create loan instances. To be initialized with the
    following parameters:
        1. loan_amount:float - The Original loan amount (principal) disbursed
        on the loan date.
        2. int_rate:float - original rate of interest applicable on the
        principal outstanding.
        3. fees:float - Origination fees charged at the time of booking,
        expressed as a % of original loan amount.
        4. term:float - The original term of the loan per schedule.
        5. segment:str - The approx risk category of the loan. Broadly mapped
        to six FICO_score groups. Configurable via config.yaml for categories'
        6. channel:str - Indicator variable to identify if the loan was booked
        through a free channel or a paid channel.
        7. loan_dt:str - Date of loan disbursement.
        8. freq:str - Frequency of repayment. Monthly, Quarterly etc. Valid
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
    period_offset = {
        'W': 7.0/30, '2W': 14.0/30,
        'M': 1, 'BM': 2, 'Q': 3, 'H': 6, 'Y': 12,
    }

    def __init__(
        self, loan_amt: float, int_rate: float, fees_pct: float, term: float,
        segment: str, channel: str, loan_dt: str, freq: str = 'M',
    ):
        self.loan_amt = loan_amt
        self.int_rate = int_rate
        self.fees_pct = fees_pct
        self.term = term
        self.segment = segment
        self.channel = channel
        self.loan_dt = arrow.get(loan_dt).datetime
        self.freq = freq
        self._offset = self.freq_offset[self.freq]
        self._periods = math.ceil(self.term/self.period_offset[self.freq])
        self._period_int_rate = self.int_rate*self.period_offset[self.freq]/12
        self.pmt = -npf.pmt(
            self._period_int_rate,
            self._periods, self.loan_amt,
        )

    def get_cfsch(self) -> pd.DataFrame:
        """Method to get the original scheduled of cashflows for a given loan.
        For monthly frequency (most common), it assumes that the dues date are
        on the same day of the month every month.
        Usage: loan.get_schedule()"""
        df = pd.DataFrame()
        df['dates'] = pd.Series(
            pd.date_range(
                self.loan_dt, freq=self._offset, periods=self._periods+1,
            ),
        ).shift(-1).dropna()
        df['period'] = df.index
        df['interest_pmt'] = - \
            npf.ipmt(
                self._period_int_rate,
                df['period']+1, self._periods, self.loan_amt,
            )
        df['principal_pmt'] = - \
            npf.ppmt(
                self._period_int_rate,
                df['period']+1, self._periods, self.loan_amt,
            )
        df['closing_principal'] = self.loan_amt-df['principal_pmt'].cumsum()
        df['opening_principal'] = df['closing_principal'].shift(
            1,
        ).fillna(self.loan_amt)
        return df

    @property
    def wal(self) -> float:
        """Returns the weighted average life of the loan (in months) based on
        the original cashflow schedule.
        The [WAL](https://en.wikipedia.org/wiki/Weighted-average_life) of the
        loan can be defined as the average number of months it takes for the
        principal of the loan
        to be repaid, if the borrower repays by the original schedule."""
        _cfs = self.get_cfsch()
        return (_cfs['principal_pmt']*_cfs['period']).sum() * \
            self.period_offset[self.freq]/self.loan_amt

    @property
    def apr(self) -> float:
        """Returns the Annual percentage rate (APR) of the loan based on the
        original cashflow schedule.
        The [APR](https://en.wikipedia.org/wiki/Annual_percentage_rate) of the
        loan can be defined as the
        total financial cost of the loan (including fees) divided by the WAL of
        the loan."""
        return self.int_rate+(self.fees_pct/self.wal)
