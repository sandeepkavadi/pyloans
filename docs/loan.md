## Loan class to create instances of installment loans.

To be initialized with the following **required** parameters:

??? info inline end ""
        - type: (float, int)
        - min: 0.0
        - max: 10e9
        - hint: typical range is 0 - 100,000 for personal loans
`loan_amount`: The original loan amount (principal) disbursed on the loan date.

??? info "`int_rate`"
    The original rate of interest applicable on the principal outstanding.

        - type: (float, int)
        - min: 0.0
        - max: 1.0
        - hint: suggested range: 0.0% - 24.99%
??? info "`term_in_months`"
    The original term of the loan per schedule.

        - type: (float, int)
        - min: 0.0
        - max: 1200
        - hint: Typically  <= 80 for personal loans, most common terms are
          multiples of 6 months
??? info "`loan_dt`"
    Date of loan disbursement.

        - type: str
        - min: None
        - max: None
        - hint: Any valid dates strings in 'YYY-mm-dd' format, recommended
          to be after 1970-01-01 to avoid any unexpected errors.

Additionally, the object also accepts the following **optional** parameters:
??? info "`freq`"
    Frequency of repayment.

        - type: str
        - min: None
        - max: None
        - valid input strings: ('W', '2W', 'M', 'BM', 'Q', 'H', 'Y')
            Valid inputs to the frequency variable
                - W: Weekly payments
                - 2W: Fortnightly payments
                - M: Monthly payments
                - BM: Bi-monthly payments
                - Q: Quarterly payments
                - H: Semi-annual payments
                - Y: Annual payments
        - hint: Please use `Loan.valid_pmt_freq` to check for accepted payment
          frequencies.
??? info "`fees_pct`"
    Origination fees charged at the time of booking, expressed as a % of
    original loan amount.

        - type: (float, int)
        - min: 0.0
        - max: 1.0
        - hint: range is 0% - 100% (typically < 15%)
??? info "`addl_pmts`"
    A dictionary containing all additional payments made over and above the
    scheduled payments for the loan obligation.

        - type: (dict, None)
        - min: None
        - max: None
        - hint: No additional payments once the loan is fully pre-paid.
          Please also ensure that the amount paid in a particular period is
          less than or equal to the closing principal for the current
          period after considering all additional payments.
??? info "`segment`"
    The approx risk category of the loan. Broadly mapped to six FICO_score
    groups. Configurable via config.yaml for categories.

        - type: str
        - min: None
        - max: None
        - hint: Please check config file for defined segments.
??? info "`channel`"
    Indicator variable to identify if the loan was booked through a free
    channel or a paid channel.

        - type: str
        - min: None
        - max: None
        - hint: Please check config file for defined channels.  By default
          we have two specified channels.

Once the `Loan` object has been instantiated with the user provided inputs,
the following calculated attributes would be made available attributes:

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
