# `pyloans`: Quickstart Guide

## Importing the `pyloans` package

```python
import pyloans as pyl
```

## Creating a loan instance
A **Loan** object is the fundamental building block of the `pyloans` package.
The package provides many parameters (attributes) to create complex
loan structures.

The below code provides a quick way to create a loan instance with the
following parameters:

1. Loan Amount (`loan_amt`): **$20,000**
2. Interest rate (`interest_rate`): **10.99%**
3. Term of the loan in months (`term_in_months`): **60**
4. Loan start date (`loan_dt`): **12<sup>th</sup> Dec 2022**
5. Frequency of repayment (`freq`): **Monthly**

```python
l1 = pyl.Loan.Loan(
    loan_amt=20000,
    interest_rate=0.1099,
    term_in_months=60,
    loan_dt="2022-12-12",
    freq="M",
)
```

## Getting the Original schedule of Cashflows
Using the `l1` loan object we previously instantiated, we can get the
original schedule of cashflows calling on the attribute `original_cfs`

```python
l1.original_cfs
```

## Updating additional payments
In case there were payments over and above the scheduled payments, they go
towards reducing the principal outstanding. This reduces the overall debt
burden of the end-consumer/borrower.

The set of additional payments have to be provided as a dictionary. There
are two ways to provide additional payments to a loan object.
First, the additional payments can be provided while instantiating the loan
object using the `addl_pmts` attribute as below:

```python
l1 = pyl.Loan.Loan(
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
The keys indicate the `period` when the payment was made. The period of the
loan depends on the frequency of repayment and is not necessarily the month
in which the payment was made. n the above example we record additional
payments of 200, 300, 400 and 500 made in the period 3, 4, 5 and 6
respectively.

Alternatively, additional payments can also be provided using the
`update_addl_pmts()` method as show below:
```python
l1.update_addl_pmts({3: 200, 4: 300, 5: 400, 6: 500})
```

## Get the updated cashflows

To get update cashflow schedule considering the additional payments made we
can use the below attribute from the loan object:

```python
l1.updated_cfs
```

## Get the Annual Percentage Rate (APR)
To get the apr, the all in annualized financial cost, for the loan
obligation we call on the property:
```python
l1.org_apr  # to get the original apr
l1.mod_apr  # to get the latest apr post additional payments
```

# Get the Weighted Average Life (WAL)

To get the WAL, the average number of months to get back the principal
amount lent to the customer, we call the property:

```python
l1.org_wal  # original wal based on the original schedule of cashflows
l1.mod_wal  # modified wal considering the additional payments
```

For all the methods and attributes available for a loan object, please see
documentation for [Loan (class)](loan.md)
