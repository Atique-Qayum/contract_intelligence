# Contract Intelligence demo report (synthetic data)

## Q1: Contracts per corporate client
```
   client_name  contracts
    Alpha Bank          2
Beta Logistics          2
 Delta Telecom          2
Epsilon Pharma          2
  Gamma Energy          2
     Zeta Bank          1
```

## Q2: Total contracted revenue (EUR, illustrative FX; contracted is NOT recognised revenue)
```
 total_contracted_eur  contracts
            2222450.0         11
```

## Q3: Payment terms per programme
```
                     programme                                          payment_terms  contracts
 Advanced Management Programme                              NOT STATED / NEEDS REVIEW          1
 Advanced Management Programme 50% on signing; 50% within 30 days of programme start.          3
Leading Digital Transformation                              NOT STATED / NEEDS REVIEW          1
Leading Digital Transformation           100% payable 60 days before programme start.          1
Leading Digital Transformation                         Net 30 days from invoice date.          2
 Strategic Finance for Leaders 50% on signing; 50% within 30 days of programme start.          1
 Strategic Finance for Leaders                         Net 30 days from invoice date.          2
```

## Q4: Contracts with outstanding payments (invoiced minus paid, contract currency)
```
contract_id    client_name currency  invoiced     paid  outstanding
      C-007  Delta Telecom      SGD  175000.0      0.0     175000.0
      C-003 Beta Logistics      USD  240000.0 120000.0     120000.0
      C-005   Gamma Energy      EUR  330000.0 325000.0       5000.0
```

## Q5: Cancellation conditions per contract
```
contract_id    client_name                                                                                 cancellation_terms
      C-001     Alpha Bank      More than 60 days before start: full refund. 30 to 60 days: 50% fee. Under 30 days: 100% fee.
      C-002     Alpha Bank Written notice 45 days or more before start: full refund. Later cancellation: 75% of fees payable.
      C-003 Beta Logistics      More than 60 days before start: full refund. 30 to 60 days: 50% fee. Under 30 days: 100% fee.
      C-004 Beta Logistics Written notice 45 days or more before start: full refund. Later cancellation: 75% of fees payable.
      C-005   Gamma Energy      More than 60 days before start: full refund. 30 to 60 days: 50% fee. Under 30 days: 100% fee.
      C-006   Gamma Energy Written notice 45 days or more before start: full refund. Later cancellation: 75% of fees payable.
      C-007  Delta Telecom      More than 60 days before start: full refund. 30 to 60 days: 50% fee. Under 30 days: 100% fee.
      C-008  Delta Telecom Written notice 45 days or more before start: full refund. Later cancellation: 75% of fees payable.
      C-009 Epsilon Pharma      More than 60 days before start: full refund. 30 to 60 days: 50% fee. Under 30 days: 100% fee.
      C-010 Epsilon Pharma Written notice 45 days or more before start: full refund. Later cancellation: 75% of fees payable.
      C-012      Zeta Bank                                                                          NOT STATED / NEEDS REVIEW
```

## Q6: Contracted amount vs amount actually received (contract currency)
```
contract_id    client_name currency  contracted  received  difference
      C-007  Delta Telecom      SGD    175000.0       0.0    175000.0
      C-003 Beta Logistics      USD    240000.0  120000.0    120000.0
      C-010 Epsilon Pharma      EUR    270000.0  252000.0     18000.0
      C-005   Gamma Energy      EUR    330000.0  325000.0      5000.0
```

## Q7a: Profitability by programme (contracted-revenue basis; contribution = revenue - direct costs)
```
                     programme  contracts  revenue_eur  direct_cost_eur  contribution_eur  margin_pct
Leading Digital Transformation          4     576900.0         295474.0          281426.0        48.8
 Advanced Management Programme          4    1164000.0         692294.0          471706.0        40.5
 Strategic Finance for Leaders          3     481550.0         297509.0          184041.0        38.2
```

## Q7b: Profitability by client
```
   client_name  contracts  revenue_eur  direct_cost_eur  contribution_eur  margin_pct
Epsilon Pharma          2     390000.0         190631.0          199369.0        51.1
Beta Logistics          2     365700.0         183436.0          182264.0        49.8
    Alpha Bank          2     450000.0         230763.0          219237.0        48.7
     Zeta Bank          1     140000.0          72020.0           67980.0        48.6
  Gamma Energy          2     480000.0         256153.0          223847.0        46.6
 Delta Telecom          2     396750.0         352276.0           44474.0        11.2
```

## Data-quality flags needing human review
```
                         source_file contract_id                             flag
              C-005_Gamma_Energy.pdf       C-005                HIGH_VALUE_REVIEW
        C-008_Delta_Telecom_Inc.docx       C-008      MISSING_FIELD:payment_terms
        C-009_Epsilon_Pharma_Ltd.pdf       C-009      MISSING_FIELD:payment_terms
       C-010_Epsilon_Pharma_Ltd.docx       C-010                   VALUE_CONFLICT
C-011_Beta_Logistics_Group_copy.docx       C-003              DUPLICATE_IDENTICAL
                 C-012_Zeta_Bank.pdf       C-012 MISSING_FIELD:cancellation_terms
```

## Extraction accuracy vs hand-written ground truth
```
contract_id          12/12
client_name          12/12
programme            12/12
start_date           12/12
end_date             12/12
participants         12/12
currency             12/12
contract_value       12/12
payment_terms        11/12
cancellation_terms   12/12
Misses: ['C-008_Delta_Telecom_Inc.docx: payment_terms']
```
