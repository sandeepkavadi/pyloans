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

    1. `loan_amount:float` - [Required] The original loan amount (principal)
    disbursed
    on the loan date.
    2. `int_rate:float` - [Required] original rate of interest applicable on
    the principal outstanding.
    3. `term_in_months:float` - [Required] The original term of the loan per
    schedule.
    4. `loan_dt:str` - Date of loan disbursement.
    5. `freq:str` - [Optional; default value:'M'] Frequency of repayment.
    Monthly, Quarterly etc. Valid values can be accessed via the class variable
    `Loan.valid_pmt_freq`.

        >    Valid inputs to the frequency variable include the below:

            - 'W': 'Weekly payments'
            - '2W': 'Fortnightly payments'
            - 'M': 'Monthly payments'
            - 'BM': 'Bi-monthly payments'
            - 'Q': 'Quarterly payments'
            - 'H': 'Semi-annual payments'
            - 'Y': 'Annual payments'

    6. `fees:float` - [Optional; default value: 0.0] Origination fees charged
    at the time of booking, expressed as a % of original loan amount.
    7. `addl_pmts: dict` - [Optional; default value: None] A dictionary
    containing all additional payments made over and above the scheduled
    payments for the loan obligation.
    8. `segment:str` - [Optional; default value: 'c'] The approx risk
    category of the loan. Broadly mapped to six FICO_score groups.
    Configurable via config.yaml for categories'
    9. `channel:str` - [Optional; default value: 'free'] Indicator variable to
    identify if the loan was booked through a free channel or a paid channel.

    Apart from the initialization parameters mentioned above, the loan
    object also has the following attributes:

    1. `pmt: float` - Based on the initial parameters of the loan,
    the attribute reflects the original equated installment amount.
    2.  `original_cfs: pd.DataFrame` - A dataframe with the original
    schedule of cashflows based on the loan parameters is returned. This
    does not include the additional payments made.
    3. `updated_cfs: pd.DataFrame` - A dataframe with the modified
    schedule of cashflows based on the loan parameters is returned. This
    considers the additional payments made.
    4. `fully_prepaid: int` - A flag like parameter to indicate of the loan
    was fully pre-paid. In case the loan in fully pre-paid, no additional
    payments can be specified and hence there cannot be further
    modifications to the cashflows.

    >**Examples:**
    ```python
    from pyloans import Loan as pyl

    l1 = pyl.Loan(
        loan_amt=20000,
        interest_rate=0.1099,
        term_in_months=60,
        loan_dt="2022-12-12",
        freq="M",
        addl_pmts={
            3: 200,
            4: 300,
            5: 400,
            6: 500,
        },
    )

    # Get the original schedule of cashflows without considering additional
    # payments, if any:

    l1.original_cfs

    # Get the modified schedule of cashflows considering addition payments,
    # if any:

    l1.updated_cfs
    ```
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

    valid_inputs = {
        'loan_amt': {
            'type': (float, int), 'min': 0.0, 'max': 10e9,
            'vals': (), 'msg': """typical range is 0 - 100,000 for
                     personal loans""",
        },
        'interest_rate': {
            'type': (float, int), 'min': 0.0, 'max': 1.0,
            'vals': (), 'msg': """suggested range: 0.0% -
                          24.99% (typically < 100%)""",
        },
        'term_in_months': {
            'type': (float, int), 'min': 0.0, 'max': 1200,
            'vals': (), 'msg': """typically  <= 80 for personal
                           loans, most common terms are multiples of 6 months
                           """,
        },
        'loan_dt': {
            'type': (dt.datetime, dt.date), 'min': None, 'max': None,
            'vals': (), 'msg': """Any valid dates strings in
                    'YYY-mm-dd' format, recommended to be after 1970-01-01
                    to avoid any unexpected errors.""",
        },
        'freq': {
            'type': str, 'min': None, 'max': None,
            'vals': ('W', '2W', 'M', 'BM', 'Q', 'H', 'Y'),
            'msg': """Please use `Loan.valid_pmt_freq` to check for
                 accepted payment frequencies.""",
        },
        'fees_pct': {
            'type': (float, int), 'min': 0.0, 'max': 1.0,
            'vals': (),
            'msg': """range: 0% - 100% (typically < 15%)""",
        },
        'addl_pmts': {
            'type': (dict, None), 'min': None, 'max': None,
            'vals': (),
            'msg': """No additional payments once the loan is
                      fully pre-paid. Please also ensure that the amount
                      paid in a particular period is less than or equal to
                      the closing principal for the current period after
                      considering all additional payments.
                      """,
        },
        'segment': {
            'type': str, 'min': None, 'max': None,
            'vals': (),
            'msg': """Please check config file for defined segments.
                      """,
        },
        'channel': {
            'type': str, 'min': None, 'max': None,
            'vals': ('free', 'paid'),
            'msg': """Please check config file for defined channels.
                        By default we have two specified channels.
                      """,
        },
    }

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
        self._check_inputs()    # check all inputs provided by user
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
        self.original_cfs = self.get_org_cfs()
        self.updated_cfs = self.get_org_cfs()
        self.updated_cfs = self._get_mod_cfs()

    def _check_inputs(self):
        """
        Method to check the validity of the inputs with helpful
        prompts around expected types and ranges for the inputs.
        Specifically the function check for the inputs types fo the
        following instance attributes:
            1. loan_amt: float, range: 0 - 10^9 (typically 0 - 100,000 for
                personal loans)
            2. interest_rate: float, suggested range: 0.0% - 24.99% (
                typically < 100%)
            3. term_in_months: float, range: typically positive integer < 80
                for personal loans. bonds or other fixed income securities
                may have longer terms up to 360
            4. loan_dt: str, range: Any valid dates strings, recommended to
                be after 1970-01-01 to avoid any unexpected errors
            5. freq: str (default = 'M'), range: {
                    'W': 'Weekly payments', '2W': 'Fortnightly payments',
                    'M': 'Monthly payments', 'BM': 'Bi-monthly payments',
                    'Q': 'Quarterly payments', 'H': 'Semi-annual payments',
                    'Y': 'Annual payments',
                    }
            6. fees_pct: float = 0.0, range: 0% - 100% (typically < 15%)
            7. addl_pmts: dict | None (default = None), individual values
                for payments in a particular period cannot be more than the
                principal outstanding amount
            8. segment: str (default = 'c'), range: please check config file
                for number of acceptable segments defined by the user
            9. channel: str (default = 'free'), please check config file,
            commonly has only two values by default ['free', 'paid']
        """
        inputs = Loan.valid_inputs
        for atr in inputs.keys():
            user_val = getattr(self, atr)
            try:
                if not isinstance(user_val, inputs[atr]['type']):
                    raise TypeError
                elif inputs[atr]['min'] is not None:
                    if (user_val < inputs[atr]['min']) | (
                            user_val > inputs[atr]['max']
                    ):
                        raise ValueError
                elif inputs[atr]['vals']:
                    if user_val not in inputs[atr]['vals']:
                        raise ValueError
                    else:
                        pass
            except TypeError:
                raise TypeError(
                    f'Expected type for {atr} is'
                    f' {inputs[atr]["type"]} but provided input '
                    f'is {type(atr)}.'
                    f' {inputs[atr]["msg"]}',
                )
            except ValueError:
                raise ValueError(
                    f'Provided value for {atr} is out of range.'
                    f' {inputs[atr]["msg"]}',
                )

    def get_org_cfs(self) -> pd.DataFrame:
        """Method to get the original scheduled of cashflows for a given loan.
        For monthly frequency (most common), it assumes that the dues date are
        on the same day of the month every month.

        === "Usage"
            ```python
            l1.get_org_cfs()

            # Alternatively
            l1.original_cfs
            ```

        === "Output"
            | dates      |period |opening_principal |....|  closing_principal |
            |:-----------|------:|-----------------:|---:|-------------------:|
            | 2023-01-12 |     1 |          20000   |....|            19802.6 |
            | 2023-02-12 |     2 |          19802.6 |....|            19603.4 |
            | 2023-03-12 |     3 |          19603.4 |....|            19202.3 |
            | 2023-04-12 |     4 |          19202.3 |....|            18697.6 |
            | 2023-05-12 |     5 |          18697.6 |....|            18088.3 |
            .....

            """
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
        principal of the loan to be repaid, if the borrower repays by the
        original schedule.
        >**Usage**:
            ```python
            l1.org_wal
            ```
        """
        return self._wal(self.get_org_cfs())

    @property
    def org_apr(self) -> float:
        """Returns the Annual percentage rate (APR) of the loan based on the
        original cashflow schedule.
        The [APR](https://en.wikipedia.org/wiki/Annual_percentage_rate) of the
        loan can be defined as the total financial cost of the loan (
        including fees) divided by the WAL of the loan.
        >**Usage**:
            ```python
            l1.org_apr
            ```
        """
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
            else:
                df = self.get_org_cfs()
            self.updated_cfs = df
            return self.updated_cfs

    @property
    def mod_wal(self) -> float:
        """
        Returns the WAL of the loan object based on the additional payments
        provided. The WAL is based on the `updated_cfs` attribute of the loan
        object.
        > **Usage:**
            ```python
            l1.mod_wal
            ```
        """
        return self._wal(self.updated_cfs)

    @property
    def mod_apr(self) -> float:
        """
        Returns the APR of the loan object based on the additional payments
        provided. The APR is based on the `updated_cfs` attribute of the loan
        object.
        > **Usage:**
            ```python
            l1.mod_apr
            ```
        """
        return self.interest_rate + (self.fees_pct / (self.mod_wal / 12))

    def _maturity(self) -> np.int64:
        _cfs = self.updated_cfs
        # numpy_financial precision issue
        return _cfs[_cfs.closing_principal <= 1e-9].period.min()

    @property
    def org_maturity_period(self) -> float:
        """
        Returns the original maturity in periods, which is same as the
        term_in_months, converted to the corresponding periods based on the
        payment frequency.
        > **Usage:**
            ```python
            l1.org_maturity_period()
            ```
        """
        return self._periods

    @property
    def mod_maturity_period(self) -> float:
        """
        Returns the modified maturity after considering additional payments,
        if any.
        > **Usage:**
            ```python
            l1.org_maturity_period()
            ```
        """
        return self._maturity()

    def prepay_fully(self, period: int) -> pd.DataFrame:
        """
        The method checks the status of the loan if it is already fully
        pre-paid. If the loan is already fully pre-paid, we raise an
        exception notifying the same.
        Else, the outstanding principal amount is considered as the
        additional payment amount and the closing balance of the loan is
        zero-ed out in the period specified as the input. The `fully_prepaid`
        flag is also set to 1.
        > **Usage:**
            ```python
            l1.org_maturity_period(6)
            ```
        """
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
        """
        The method checks the status of the loan if it is already fully
        pre-paid. If the loan is already fully pre-paid, we raise an
        exception notifying the same.
        Else, the `addl_pmts` attribute of the loan object is merged to
        include the additional payment passed to the method.
        > **Usage:**
            ```python
            l1.update_addl_pmts({7: 700})
            ```
        """
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
        """
        Since the `update_addl_pmts` method merges the input with the
        existing attribute `addl_pmts` of the loan object. The method provides
        a way to reset the `addl_pmts` attribute in case of any errors.
        > **Usage:**
            ```python
            l1.reset_addl_pmts()
            ```
        """
        self.addl_pmts = {}
        self.fully_prepaid = 0
        self.updated_cfs = self._get_mod_cfs()
