# Where the reading rules come from

The layouts in `rules.json` were written from three kinds of evidence. The first is the only one checked against real mail end to end.

1. **A real mailbox** (one tester, twelve months, read on a device): HDFC UPI alerts, Swiggy, Instamart, Amazon, Apple, Jio, Airtel, FirstCry, Uber and others. Cases from it are in `__tests__/real-layouts-test.ts` and the "layouts found in the reading log" section of `__tests__/resilience-test.ts`.
2. **Public parsers' fixtures and tests.** Their authors replaced names and numbers but kept each bank's wording. Every sample used is a test case in `__tests__/bank-layouts-test.ts`.
3. **Testers' reading logs** (More → Reading health → Share reading log), as they come in.

A layout from the second group is real wording but has not been seen by this app in a real mailbox. When a tester's log shows a bank email that failed, fix the pattern in `build.py`, add the masked text as a test, raise the version and publish.

## Bank and card alerts

| Source | Used for |
|---|---|
| https://github.com/akhilnarang/bank-email-parser | HDFC, ICICI, Axis, SBI, SBI Card, Kotak, IDFC FIRST, IndusInd, Yes Bank, HSBC, OneCard, slice, Jupiter, BOBCARD, Equitas |
| https://github.com/akhilnarang/financial-dashboard | sender addresses |
| https://github.com/ArionMiles/expensor | HDFC and ICICI fixtures (sender, subject, body) |
| https://github.com/girishtare/PersonalExpenseManager_v2 | HDFC, RBL, BOBCARD One, Jupiter, and emails to ignore |
| https://github.com/ashwin-portfolio/personal-finance-tracker | HDFC debit card, OTP, declined and failed emails |
| https://github.com/DevanshRathii/Vyay | HDFC e-mandate and NACH, Canara, SBI Card |
| https://github.com/alokkusingh/email-service | HDFC and Axis credit cards |
| https://github.com/Rrishik/dus-aane-bot | senders and subjects to ignore |
| https://github.com/DroidNinja/finos-public | Axis and ICICI subjects and bodies |
| https://github.com/Suman-Jaiswal/pft-backend | SBI Card on UPI |
| https://github.com/mb-bytes/swipit | Federal Bank credit card |
| https://github.com/CCAgentOrg/bankin-scorecard | registered `.bank.in` domains |

## Subscriptions, bills and payment apps

Evidence here is thinner than for banks: real receipts are rarely public. What was found came from developers' parsers and tests, exported Gmail filters, and printouts of real emails. Each layout used is a case in `__tests__/apps-and-subscriptions-test.ts`.

| Source | Used for |
|---|---|
| https://github.com/hikmahtech/aegis (tests) | Apple renewal receipts, Stripe receipts in rupees, Airtel bill and receipt, Axis AutoPay |
| https://github.com/DroidNinja/finos-public (`parsers/bill_email_parser.py`) | Airtel bills, Amazon Pay bill payments and reminders, Google Pay bill reminders |
| https://github.com/asyncauto/cashflowy, https://github.com/moonblade/Expense-Tracker | Paytm and PhonePe mail types |
| https://github.com/pritam-gembali/passbook (`wallet.gs`) | Amazon Pay subjects |
| Printouts of real emails on scribd.com (documents 997353845, 850073707, 833289019, 968685936, 819652049, 911628814, 896378434) | Apple India tax invoice, Google Play receipt, PhonePe, Amazon Pay recharge, HDFC BillPay, Razorpay |
| Exported Gmail filters (armaanfarshori/my-everyday-email-filters and others) | sender addresses for utilities, housing-society apps and insurers |

Findings that shaped the rules:

- **Netflix and Spotify do not appear to email a receipt for each monthly charge.** Those charges are read from the bank or card alert instead.
- **A bill is not a payment.** Airtel, Jio, electricity boards, housing-society apps and Google Pay / Amazon Pay reminders all send bills with an amount and a due date; many also print "Payment made" for last month. They are ignored; the payment receipt and the bank alert are what count.
- **Services billed in dollars are not counted.** A dollar invoice can carry one rupee figure (the tax, converted), which must not be read as the charge.
- **PhonePe, Paytm, Amazon Pay, FamApp, Razorpay and HDFC BillPay** are read like bank alerts. When the bank also reports the same payment, the two are merged. Card bill payments, loan repayments and wallet top-ups are recorded as transfers and left out of the totals.

## Merchant receipts

Real emails quoted in public repositories and complaint sites; each is a case in `__tests__/merchant-layouts-test.ts`. "Old" means the sample predates 2021 and the current email may differ.

| Platform | Evidence | Source |
|---|---|---|
| Swiggy, Instamart | real emails, 2026 | github.com/pal3dreamer/CraveMate, kevivt/spendsense, theerthalavenkatesh960-netizen/gooddays |
| Zomato | real emails, 2024–2026 | github.com/nikhilx/zomato-spend-analyzer, Akshat293/extractEml |
| Flipkart | real email, 2026 | gooddays; rakesh-singh-dev/orderhub-backend-api |
| Myntra, H&M, Zara | real emails, 2024–2025 | github.com/devansh23/vera_logic |
| AJIO | real email, 2026 | github.com/dhruvsarohaa/Sentinel-Mail-updated |
| Amazon.in, Amazon Pay | real emails, 2026 | gooddays tests; syedateebulislam/openboard |
| Uber | real receipts, 2023–2026 | huggingface.co/datasets/ankur-bohra/automatic-reimbursement-tool-demo-incorrect; openboard |
| Rapido | three parsers and an inbox dump | github.com/sushil-kamble/uber-receipts-dashboard and others |
| IRCTC | real email, 2026 | github.com/sankarsh98/family-utility-app |
| BookMyShow | real email, 2026 | gooddays |
| MakeMyTrip (bus) | real email, 2026 | github.com/rishusatyam/email-scrap |
| Domino's | two parsers; old pastes | rsingh-arenema/order-summary-backend; consumercomplaints.in |
| Ola, Cleartrip, IndiGo | old | github.com/Purva96/PRA; pastebin; KDE/kitinerary |
| Pizza Hut, KFC, BigBasket, Netmeds, Tata 1mg | old pastes | consumercomplaints.in |

What these showed that the reader had to learn: totals on the line after their label; all labels listed before all amounts (IRCTC); several labelled amounts on one row (Domino's); the older rupee sign `₨` (Flipkart); the currency after the number (IndiGo); "Net Paid" and "Amount to be paid" outranking a "Total" row (Myntra, Pizza Hut); a "Fare adjustment" row that is not a total (Uber); and a bare "615.0" with no currency (MakeMyTrip).

Nothing reliable was found for Blinkit, Zepto's own receipts (some arrive as a Razorpay payment mail, which is read), JioMart, PharmEasy, Nykaa, Meesho, Tata CLiQ, Croma, Lenskart, Decathlon, Goibibo, ixigo, redBus, most airlines and hotels, PVR INOX, Namma Yatri, or for cancellation and refund subjects on any platform.

## Not covered yet

No email sample could be found for these, so they are read only if their wording happens to match another bank's: American Express India (sender known, body not), AU Small Finance Bank, Standard Chartered, Bank of Baroda accounts, PNB, IDBI, DBS, Paytm Payments Bank, Airtel Payments Bank, Fi. SBI savings accounts have only the debit-card table. ATM withdrawals, foreign-currency card spends and wallet top-ups are deliberately not counted.

No reliable receipt sample was found for most subscription services (Prime Video, ZEE5, Sony LIV, Audible, YouTube Premium, Microsoft 365 and others), for Vi, BSNL, ACT, Tata Play and DTH operators, for electricity, gas and water payment receipts, for FASTag and insurers, or for MobiKwik, Freecharge, Simpl and LazyPay. They rely on the general total-row reading and on bank alerts.
