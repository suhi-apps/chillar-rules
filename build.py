#!/usr/bin/env python3
"""Rewrites the bank section of rules.json. Run from the repo root: python3 rules/build.py

Bank alert layouts are easier to maintain here, with the amount pattern written once,
than as escaped strings in JSON. Everything else in rules.json is edited there directly.
Sources for each layout are in rules/SOURCES.md."""
import json, os, sys

A = r'(?:Rs\.?|INR|₹) ?(?:INR ?)?([\d,]*\.?\d+)'  # one capture group: the amount
N = r'([\d,]*\.?\d+)'

# (note, regex, via, amount group, payee group or None, vpa group or None)
ALERTS = [
    # ---- UPI from an account
    ('HDFC UPI: debited from account ... to/towards VPA x@y (NAME)', A + r' (?:has been |is |was )?debited from (?:your )?(?:account|a/c)[^@]{0,40}? (?:to|towards) VPA (\S+) ?\(([^)]+)\)', 'UPI', 1, 3, 2),
    ('HDFC UPI: ... to VPA x@y NAME on date (no brackets)', A + r' (?:has been |is |was )?debited from (?:your )?(?:account|a/c)[^@]{0,40}? (?:to|towards) VPA (\S+@\S+) (.+?) on \d', 'UPI', 1, 3, 2),
    ('UPI on a RuPay credit card', A + r' (?:has been|is) debited from your [^@]{0,60}?Card[^@]{0,24}? (?:to|and credited to VPA|Paid to) (\S+@[\w.]+)(?: \(([^)]+)\))?', 'UPI', 1, 3, 2),
    ('UPI debit naming only the handle', A + r' (?:has been |is |was )?debited from (?:your )?(?:account|a/c)[^@]{0,40}? (?:to|towards) (?:VPA )?(\S+@\w+)', 'UPI', 1, None, 2),
    ('HDFC: debited from account N to account M', A + r' has been debited from account \S+ to (account \S+)', 'UPI', 1, 2, None),
    ('Canara UPI', r'An amount of ' + A + r' has been DEBITED on \S+ from your account \S+ to (.+?) with UPI Ref', 'UPI', 1, 2, None),
    ('Kotak811 UPI', r'made a UPI payment of ' + A + r' towards (.+?) through', 'UPI', 1, 2, None),
    ('Jupiter UPI (2023 layout)', r'payment was successful.{0,80}?Paid to (.+?) (\S+@\S+) How much ₹ ?' + N, 'UPI', 3, 1, 2),
    ('Jupiter UPI (2026 layout)', r'You paid \|? ?₹ ?' + N + r' \|? ?Paid to \|? ?(.+?)(?: / | )(\S+@\S+)', 'UPI', 1, 2, 3),
    ('Axis account debit table with a transaction trail', r'Amount Debited: ?' + A + r' Account Number: ?\S+ Date & Time: ?.{0,30}? Transaction Info: ?(.+?)(?: If this|$)', 'UPI', 1, 2, None),
    ('IndusInd account debit', r'Account No\. \S+ has been Debited for ' + A + r' towards (.+?)\. The balance', 'UPI', 1, 2, None),
    ('Axis AutoPay done', r'successful AutoPay transaction: ?Transaction Amount: ?' + A + r' Merchant Name: ?(.+?) AutoPay ID', 'Card', 1, 2, None),
    # ---- Payment apps. The text starts with the subject; "¶" marks where the body begins.
    ('PhonePe: Sent ₹ X to PAYEE (subject)', r'^Sent ₹ ?' + N + r' to ([^¶]+?) ¶', 'UPI', 1, 2, None),
    ('PhonePe: Payment for BILLER of ₹ X is successful (subject)', r'^Payment for ([^¶]+?) of ₹ ?' + N + r' is successful', 'UPI', 2, 1, None),
    ('PhonePe body: Paid To PAYEE ₹ X Txn. ID', r'Paid To (.+?) ₹ ?' + N + r' Txn\. ID', 'UPI', 2, 1, None),
    ('Paytm: You paid Rs. X to PAYEE (subject)', r'^You paid ' + A + r' to ([^¶]+?) ¶', 'UPI', 1, 2, None),
    ('Amazon Pay: Rs X was paid on Amazon.in (subject)', '^' + A + r' was paid on (Amazon)\.in', 'UPI', 1, 2, None),
    ('Amazon Pay: Your payment of ₹ X to MERCHANT was successful (subject)', r'^Your payment of ' + A + r' to ([^¶]+?) was successful', 'UPI', 1, 2, None),
    ('Amazon Pay recharge or bill: Paid to BILLER ... Paid Amount ₹X', r'is successful\. ?Paid to (.+?) Amount:? ?(?:₹|Rs\.?) ?[\d,.]+.{0,60}?Paid Amount:? ?' + A, 'UPI', 2, 1, None),
    ('Amazon Pay: Your payment to MERCHANT was Approved (subject), amount in the body', r'^Your payment to ([^¶]+?) was Approved ¶.{0,200}?₹ ?' + N, 'UPI', 2, 1, None),
    ('Amazon Pay FASTag toll', r'toll payment of ' + A + r' at (Toll gate .+?) was successful', 'UPI', 1, 2, None),
    ('FamApp', r'You have successfully paid ' + A + r' to (.+?) at \d', 'UPI', 1, 2, None),
    ('Razorpay customer receipt: Payment successful for MERCHANT (subject), ₹ X Paid Successfully', r'^Payment successful for ([^¶]+?) ¶.{0,300}?₹ ?([\d,]+)(?: ?\.\d{1,2})? Paid Successfully', 'UPI', 2, 1, None),
    ('HDFC BillPay via BillDesk', r'Your (.+?) bill of ' + A + r' for .{0,80}? has been processed successfully', 'Bank', 2, 1, None),
    # ---- Cards
    ('HDFC card: debited from your ... Card ending N towards/at MERCHANT on date', A + r' (?:has been|is) debited from your [^.@]{0,50}?Card[^.@]{0,30}? (?:towards|at) (.+?),? on \d', 'Card', 1, 2, None),
    ('Thank you for using your ... Card ... for Rs X at MERCHANT on date (HDFC, Axis, BOBCARD)', r'Thank you for using (?:your )?[^.]{0,50}?\b\w*card\b.{0,24}? for (?:a transaction of )?' + A + r' at (.+?),? on \d', 'Card', 1, 2, None),
    ('HDFC card: You made a transaction of Rs X at MERCHANT on date', r'made a transaction of ' + A + r' at (.+?) on \d', 'Card', 1, 2, None),
    ('HDFC e-mandate paid by credit card', r'Your (.+?) bill, set up through E-mandate[^:]{0,160}?Transaction Details: ?Amount: ?' + A, 'Card', 2, 1, None),
    ('ICICI credit card: used for a transaction of X on date. Info: MERCHANT', r'Card \S+ has been used for a transaction of ' + A + r' on [^.]{0,40}?\. Info: (.+?)(?:\. |\.?$)', 'Card', 1, 2, None),
    ('ICICI, HSBC: card used for (a transaction of) X at / for payment to MERCHANT on date', r'card[^.]{0,40}? ?(?:has been|was) used for (?:a transaction of )?' + A + r' (?:for payment to|at) (.+?) on \d', 'Card', 1, 2, None),
    ('ICICI debit card purchase', r'A purchase of ' + A + r' has been made using your Debit Card[^.]{0,60}?\. Info: (.+?)\.(?: |$)', 'Card', 1, 2, None),
    ('Axis credit card summary table', r'Transaction Amount: ?' + A + r' Merchant Name: ?(.+?) Axis Bank Credit Card No', 'Card', 1, 2, None),
    ('SBI Card, IDFC, Yes Bank, Equitas: X spent on your ... Card ... at MERCHANT on date', A + r' (?:has been |was )?spent on (?:your )?[^.]{0,50}?Card[^.]{0,30}? at (.+?) on \d', 'Card', 1, 2, None),
    ('SBI Card e-mandate', r'Transaction of ' + A + r' at (.+?) against E-mandate[^.]{0,120}? has been debited to your', 'Card', 1, 2, None),
    ('Kotak credit card, RBL: X spent at MERCHANT on ...', A + r' spent at (.+?) on (?:\d[^.]{0,30} using your [^.]{0,30}Card|[^.]{0,30}card \(\d+\))', 'Card', 1, 2, None),
    ('Federal Bank credit card', r'You have spent ' + A + r' at (.+?) on \d', 'Card', 1, 2, None),
    ('SBI debit card table', r'Terminal Owner Name \|? ?(.+?) \|? ?Terminal Id\b.{0,200}?Amount \(INR\) \|? ?' + N + r'.{0,160}?Transaction Type \|? ?PURCHASE', 'Card', 2, 1, None),
    ('Kotak debit card', r'Your transaction of ' + A + r' (?:on|at) (.+?) using Kotak Bank Debit Card', 'Card', 1, 2, None),
    ('IndusInd credit card', r'transaction on your [^.]{0,40}?Card ending \d+ for ' + A + r' on [^.]{0,40}? at (.+?) is Approved', 'Card', 1, 2, None),
    ('IndusInd debit card table', r'Debit Card ending \d+ is successful.{0,40}?Merchant Name[ :|]*(.+?) \|? ?Amount.{0,80}?' + A, 'Card', 2, 1, None),
    ('OneCard / BOBCARD One', r'was used to make a payment\. Amount: ?' + A + r' Merchant: ?(.+?) Date:', 'Card', 1, 2, None),
    ('slice credit card', r'Transaction of (?:[A-Z]{3} [\d.,]+ \| )?' + A + r' at (.+?) from your slice credit card \S+ was successful', 'Card', 1, 2, None),
    # ---- Bank transfers and mandates
    ('HDFC NACH', A + r' has been debited from [^.]{0,40}?Account Number \S+ towards (.+?) with UMRN', 'Bank', 1, 2, None),
    ('Kotak NACH/ECS', r'debited towards NACH/ECS transaction[^:]{0,40}?Beneficiary: ?(.+?) UMRN Number: ?\S+ Amount: ?' + A, 'Bank', 2, 1, None),
    ('HDFC net banking transfer to a payee', A + r' has been deducted from your .{0,60}? for a (?:t|T)ransfer to payee (.+?) via ', 'Bank', 1, 2, None),
    ('HDFC RTGS initiated', r'initiated a RTGS transaction of ' + A + r' from your [^.]{0,40}? for a transfer to payee (.+?) using', 'Bank', 1, 2, None),
    ('HDFC IMPS: debited from your account ... and credited to the account ending N', A + r' has been debited from your account ending \S+ on \S+ and credited to the (account ending \S+)', 'Bank', 1, 2, None),
    ('HDFC transfer to PPF / Sukanya', r'You have transferred ' + A + r' to your (PPF\S*)', 'Bank', 1, 2, None),
    ('ICICI online payment (NEFT, IMPS, fund transfer, net banking)', r'You have made an online [^.]{0,30}?payment of ' + A + r' towards (.+?) (?:on [A-Z][a-z]{2} \d|from your)', 'Bank', 1, 2, None),
    ('ICICI account / Axis account: debited with X on date. Info: / by ...', r'(?:Account|A/c no\.) \S+ has been debited with ' + A + r' on [^.]{0,40}?(?:\. Info: | by )(.+?)(?:\.(?: |$)|$)', 'Bank', 1, 2, None),
    ('IDFC FIRST account', r'A/C \S+ has been debited by ' + A + r' on [^.]{0,80}? paid to (.+?)(?: New balance|\.|$)', 'Bank', 1, 2, None),
]

IGNORE = [
    r'Transaction Status: ?REVERSED',
    r'\bmerchant credit refund\b',
    r'\bfor ATM withdrawal\b',
    r'\bhas been successfully credited\b|\bis successfully credited\b',
    r'\beligible for conversion\b|\bSmartEMI\b',
    r'\bupcoming AutoPay\b|\bTo be debited by\b|\bAmount to be debited\b',
    r'\bis due on .{0,60}will be processed\b',
    r'\badded to your Amazon Pay\b',
    # In the subject only: real receipts advertise cashback in their footers.
    r'^[^¶]*\b(Payment Reminder|Gift Card|cashback|reward points)\b',
    r'^Received ₹|^Razorpay \|',
    r'\bMoney (Added|Received|Refunded|Sent)\b|\bstatement for\b',
]

# Payment apps. Their mail is read like a bank alert: who was paid, and how much.
APPS = ['phonepe.com', 'paytm.com', 'paytmbank.com', 'amazonpay.in', 'payments-messages@amazon.in', 'famapp.in', 'razorpay.com', 'hdfcbankbillpay@billdesk.in']

# Subjects that are never a payment: statements, reminders, failures.
IGNORE_SUBJECTS = [
    r'^e-?bill for\b', r'^bill for your\b', r'\bbill information\b', r'\be-bill of consumer\b', r'\belectricity bill$',
    r'\breservation confirmed\b', r'\bplan active on\b',
    r'\bsubscriptions? (is|are) expiring\b', r'\brefund request\b',
    r'\bunsuccessful\b|\bhas failed\b|\bunable to charge\b',
    r'\b(is|are) due\b|\bdue (tomorrow|today)\b|\bpayment reminder\b|\bpay now\b',
    r'\bmonthly statement\b|\bstatement for\b|\binvoice is available\b',
    r'\bcredit card bill payment was successful\b',
]

TOTAL_LABELS = [r'\bnet payment\b', r'\bnet paid\b', r'\bfinal total\b', r'\bamount to be paid\b', r'\bselected price\b', r'\btotal bill\b', r'\btotal charge\b', r'\bpaid online\b', r'\btotal amount is\b', r'\breceipt amount\b', r'\btotal amount paid\b']

DOMAINS = [
    # HDFC, ICICI, Axis
    'hdfcbank.bank.in', 'hdfc.bank.in', 'hdfcbank.net', 'hdfcbank.com', 'icici.bank.in', 'icicibank.com', 'axis.bank.in', 'axisbank.com',
    # SBI and SBI Card
    'sbi.co.in', 'sbi.bank.in', 'sbicard.com',
    # Kotak, Yes, IDFC FIRST, IndusInd, Federal, AU, RBL
    'kotak.com', 'kotak.bank.in', 'kotak811.bank.in', 'yesbank.in', 'yes.bank.in', 'idfcfirstbank.com', 'idfcfirst.bank.in', 'indusind.com', 'indusind.bank.in',
    'federalbank.co.in', 'federal.bank.in', 'aubank.in', 'au.bank.in', 'rblbank.com', 'rbl.bank.in',
    # Public sector
    'bankofbaroda.bank.in', 'bobcard.in', 'bobcard.co.in', 'pnb.bank.in', 'canarabank.com', 'canarabank.bank.in', 'unionbankofindia.bank.in', 'idbi.bank.in', 'mahabank.co.in',
    # Foreign banks and card issuers
    'hsbc.co.in', 'hsbc.bank.in', 'sc.com', 'americanexpress.com', 'dbs.bank.in',
    # Card and neo-bank apps
    'getonecard.app', 'slice.bank.in', 'sliceit.com', 'jupiter.money', 'equitas.bank.in', 'csb.bank.in',
]

SUBJECT_WORDS = ['approved', 'toll', 'txn', 'transaction', 'debited', 'debit', 'spent', 'UPI', 'alert', 'payment', 'paid', 'sent', 'purchase', 'used', 'update', 'NEFT', 'RTGS', 'IMPS', 'notification', 'swiped', 'successful', 'recharge']

path = 'rules.json' if os.path.exists('rules.json') else 'rules/rules.json'
pack = json.load(open(path))
# A name is never long, and an unbounded match makes long promotional mail slow to scan.
ALERTS = [(n, r.replace('(.+?)', '(.{1,80}?)').replace('([^¶]+?)', '([^¶]{1,80}?)'), v, a, p, x) for n, r, v, a, p, x in ALERTS]
pack['bankAlerts'] = [dict(note=n, re=r, via=v, amount=a, **({'payee': p} if p else {}), **({'vpa': x} if x else {})) for n, r, v, a, p, x in ALERTS]
pack['bankIgnore'] = IGNORE
pack['bankDomains'] = DOMAINS
pack['bankSubjectWords'] = SUBJECT_WORDS
pack['paymentApps'] = APPS
pack['ignoreSubjects'] = IGNORE_SUBJECTS
pack['totalLabels'] = TOTAL_LABELS
if os.path.exists('.scratch/merchants.json'):
    pack['merchants'] = json.load(open('.scratch/merchants.json'))
if os.path.exists('.scratch/subjectWords.json'):
    pack['subjectWords'] = json.load(open('.scratch/subjectWords.json'))
if len(sys.argv) > 1:
    pack['version'] = int(sys.argv[1])

def row(v):
    return json.dumps(v, ensure_ascii=False)

keys = ['subjectWords', 'totalLabels', 'paidSentences', 'ignoreSubjects', 'bankDomains', 'paymentApps', 'bankSubjectWords', 'bankIgnore']
out = ['{', f'  "version": {pack["version"]},', '  "merchants": [', ',\n'.join('    ' + row(m) for m in pack['merchants']), '  ],']
out += [f'  {row(k)}: {row(pack.get(k, []))},' for k in keys]
out += ['  "bankAlerts": [', ',\n'.join('    ' + row(b) for b in pack['bankAlerts']), '  ]', '}', '']
open(path, 'w').write('\n'.join(out))
print(f'version {pack["version"]}: {len(pack["bankAlerts"])} bank layouts, {len(DOMAINS)} bank domains, {len(pack["merchants"])} platforms')
