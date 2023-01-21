The `Loan` class is the fundamental building block of the pyloans packages. It
enables us to created instances of installment loans. Once a `Loan` object is
created, we can run analyze the properties of the loan such as generating a
Cashflow schedule, compute the Weighted Average Life of the loans etc.

Please see below for basic CRUD (no deletion) operations concerning the `Loan`
class.

### **Instantiation**: Creating a Loan object

An instance of the `Loan` class can be created using the following
**required** parameters:

1. `#!python loan_amount: float`: The original loan amount (principal)
   disbursed  on the loan  date. Typical range is 0 - 100,000 for
   personal loans.
2. `#!python int_rate: float`: The original rate of interest applicable on the
   principal outstanding. Suggested range: 0.0% - 24.99%
3. `#!python term_in_months`: The original term of the loan per schedule. Typically,
   <= 80 for personal loans, most common terms are multiples of 6 months
4. `#!python loan_dt: str`: Date of loan disbursement. Any valid dates
   strings in 'YYYY-mm-dd' format, recommended to be after 1970-01-01 to avoid
   any unexpected errors.

Additionally, the object also accepts the following **optional** parameters:

1. `#!python freq: str`: Frequency of repayment.
   Please use `Loan.valid_pmt_freq` to check for accepted payment
   frequencies.
2. `#!python fees_pct: float`: Origination fees charged at the time of
   booking, expressed as a % of original loan amount. Range is 0% - 100%
   (typically < 15%)
3. `#!python addl_pmts: dict`: A dictionary containing all additional payments
   made over and above the scheduled payments for the loan obligation. No
     additional payments once the loan is fully pre-paid. Please also
     ensure that the amount paid in a particular period is less than or
     equal to the closing principal for the current period after
     considering all additional payments.
4. `#!python segment: str`: The approx risk category of the loan. Broadly
   mapped to six FICO_score<br>groups. Configurable via config.yaml for
   categories.
5. `#!python channel: str`: Indicator variable to identify if the loan was
   booked through a free channel or a paid channel. By default, we have two
   specified channels.

??? info "Additional information on parameters"

    |     Parameter    |       Optional?       |           Type          |  Min |  Max |
    |:----------------:|:---------------------:|:-----------------------:|:----:|:----:|
    |    `loan_amt`    |           No          | `#!python (float, int)` |  0.0 | 10e9 |
    |    `int_rate`    |           No          | `#!python (float, int)` |  0.0 |  1.0 |
    | `term_in_months` |           No          | `#!python (float, int)` |  1.0 | 1200 |
    |     `loan_dt`    |           No          |      `#!python str`     | None | None |
    |      `freq`      |   Yes (default: 'M')  |      `#!python str`     | None | None |
    |    `fees_pct`    |   Yes (default: 0.0)  | `#!python (float, int)` |  0.0 |  1.0 |
    |    `addl_pmts`   |  Yes (default: None)  | `#!python (float, int)` | None | None |
    |     `segment`    |   Yes (default: 'c')  |      `#!python str`     | None | None |
    |     `channel`    | Yes (default: 'free') |      `#!python str`     | None | None |

!!! Example "*Example: Instantiating a Loan object*"

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
    ```

### **Loan Properties**: Retrieving calculated loan properties & attributes

Once a `Loan` object has been instantiated, with user inputs,
the following properties/attributes would be available:

1. `#!python pmt: float` - Based on the initial parameters of the loan,
the attribute reflects the original equated installment amount.
2.  `#!python original_cfs: pandas.DataFrame` - A dataframe with the original
schedule of cashflows based on the loan parameters is returned. This
does not include the additional payments made.
3. `#!python updated_cfs: pandas.DataFrame` - A dataframe with the modified
schedule of cashflows based on the loan parameters is returned. This
considers the additional payments made.
4.

!!! Example "*Example: Retrieving key properties of the Loan*"

     ```python
     # Once an instance of Loan is created, we can retrieve various
     # attributes of the instance as shown below:

     l1 = pyl.Loan(
         loan_amt=20000,
         interest_rate=0.1099,
         term_in_months=60,
         loan_dt="2022-12-12",
     )

     # Get un-modified loan roperties/attributes

     l1.pmt  # installment amount on the loan
     l1.original_cfs  # original un-modified schedule of cashflows
     l1.original_wal  # original un-modified weihted average life
     l1.original_apr  # original un-modified annual percentage rate
     l1.org_maturity_period  # number of periods corresponding to term

     # Incase there were additional paymemnts provided  or if the loan was
     # updated (see below), the modified properties can be retrieved as below:

     l1.mod_cfs  # modified schedule of cashflows after an update
     l1.mod_wal  # modified weihted average life after an update
     l1.mod_apr  # modified annual percentage rate after an update
     l1.mod_maturity_period  # number of periods after an update
     ```

### **Updating**: Modifying an existing Loan instance

4. `fully_prepaid: int` - A flag to indicate of the loan was fully pre-paid.
In case the loan in fully pre-paid, no additional payments can be specified
and hence there cannot be further modifications to the cashflows.


### **Re-setting**: Re-setting additional payments for a Loan instance
