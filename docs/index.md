# `pyloans`: Analytics for Personal Loans

## Introduction

`pyloans` is a python based package to simplify, analyze and work with
installment based loan obligations. The installments are generally a fixed
amount that the borrower pays to the lender at equally spaced intervals
over the life of the loan.

The `pyloans` package is written with both the borrowers (end-consumer) and
lenders (financial institutions) in mind.

From a borrower's perspective the package offers the following functionality:

1. Original schedule of Cashflows
2. Modified schedule of Cashflows, in case of additional payments or full
   pre-payment
3. Updated date of maturity based on additional payments made
4. Annual Percentage Rate (APR)

<!---
[comment]: <> (5. Compare offers and consolidate multiple financial
   obligations)
-->

From a lenders perspective the package offers the following functionality:

1. Weighted average life of a loan (WAL)

<!---
[comment]: <> (2. Consolidate multiple loan objects into a portfolio)
[comment]: <> (3. Simulate various loan structure to quantify impact to
lender's profitability)

[comment]: <> (4. Simulate an unsecured lending portfolio by creating multiple
   instances of loan objects with random initial parameters based on
   historical distributions for each parameter.)

[comment]: <> (5. Systematic way to understand portfolio profitability based on
   historical distributions of prepayments, charge-offs and loan structures.)
-->

Please see [Quickstart guide](quickstart.md) for basic functionality of the
package.
