-- Q1: Contracts per corporate client
SELECT client_name, COUNT(*) AS contracts FROM contracts GROUP BY client_name ORDER BY contracts DESC, client_name;
-- Q2: Total contracted revenue (EUR, illustrative FX; contracted is NOT recognised revenue)
SELECT ROUND(SUM(c.contract_value * f.rate_to_eur), 2) AS total_contracted_eur, COUNT(*) AS contracts
FROM contracts c JOIN fx f ON f.currency = c.currency;
-- Q3: Payment terms per programme
SELECT programme, COALESCE(payment_terms, 'NOT STATED / NEEDS REVIEW') AS payment_terms, COUNT(*) AS contracts
FROM contracts GROUP BY programme, payment_terms ORDER BY programme;
-- Q4: Contracts with outstanding payments (invoiced minus paid, contract currency)
WITH inv AS (SELECT contract_id, SUM(amount) AS invoiced FROM invoices GROUP BY contract_id),
     pay AS (SELECT contract_id, SUM(amount) AS paid FROM payments GROUP BY contract_id)
SELECT c.contract_id, c.client_name, c.currency, COALESCE(inv.invoiced,0) AS invoiced, COALESCE(pay.paid,0) AS paid,
       COALESCE(inv.invoiced,0) - COALESCE(pay.paid,0) AS outstanding
FROM contracts c LEFT JOIN inv USING (contract_id) LEFT JOIN pay USING (contract_id)
WHERE COALESCE(inv.invoiced,0) - COALESCE(pay.paid,0) > 0.01 ORDER BY outstanding DESC;
-- Q5: Cancellation conditions per contract
SELECT contract_id, client_name, COALESCE(cancellation_terms, 'NOT STATED / NEEDS REVIEW') AS cancellation_terms
FROM contracts ORDER BY contract_id;
-- Q6: Contracted amount vs amount actually received (contract currency)
WITH pay AS (SELECT contract_id, SUM(amount) AS received FROM payments GROUP BY contract_id)
SELECT c.contract_id, c.client_name, c.currency, c.contract_value AS contracted, COALESCE(pay.received,0) AS received,
       c.contract_value - COALESCE(pay.received,0) AS difference
FROM contracts c LEFT JOIN pay USING (contract_id)
WHERE ABS(c.contract_value - COALESCE(pay.received,0)) > 0.01 ORDER BY ABS(difference) DESC;
-- Q7a: Profitability by programme (contracted-revenue basis; contribution = revenue - direct costs)
WITH cost AS (SELECT contract_id, SUM(amount_eur) AS cost_eur FROM costs GROUP BY contract_id)
SELECT c.programme, COUNT(*) AS contracts, ROUND(SUM(c.contract_value*f.rate_to_eur),0) AS revenue_eur,
       ROUND(SUM(cost.cost_eur),0) AS direct_cost_eur,
       ROUND(SUM(c.contract_value*f.rate_to_eur) - SUM(cost.cost_eur),0) AS contribution_eur,
       ROUND(100.0*(SUM(c.contract_value*f.rate_to_eur) - SUM(cost.cost_eur))/SUM(c.contract_value*f.rate_to_eur),1) AS margin_pct
FROM contracts c JOIN fx f ON f.currency=c.currency LEFT JOIN cost USING (contract_id)
GROUP BY c.programme ORDER BY margin_pct DESC;
-- Q7b: Profitability by client
WITH cost AS (SELECT contract_id, SUM(amount_eur) AS cost_eur FROM costs GROUP BY contract_id)
SELECT c.client_name, COUNT(*) AS contracts, ROUND(SUM(c.contract_value*f.rate_to_eur),0) AS revenue_eur,
       ROUND(SUM(cost.cost_eur),0) AS direct_cost_eur,
       ROUND(SUM(c.contract_value*f.rate_to_eur) - SUM(cost.cost_eur),0) AS contribution_eur,
       ROUND(100.0*(SUM(c.contract_value*f.rate_to_eur) - SUM(cost.cost_eur))/SUM(c.contract_value*f.rate_to_eur),1) AS margin_pct
FROM contracts c JOIN fx f ON f.currency=c.currency LEFT JOIN cost USING (contract_id)
GROUP BY c.client_name ORDER BY margin_pct DESC;
