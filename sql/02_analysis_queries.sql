-- ============================================================
-- E-Commerce Sales Analysis - Analysis & Insight Queries
-- Target: SQLite
-- Run:  sqlite3 outputs/ecommerce.db < sql/02_analysis_queries.sql
--
-- Every query below is verified against the Python pipeline by
-- src/05_build_database.py, which cross-checks the SQL totals
-- against the pandas totals and fails loudly on any mismatch.
-- ============================================================

.mode column
.headers on


-- ============================================================
-- STEP 2 - KEY PERFORMANCE INDICATORS
-- ============================================================
SELECT '--- STEP 2: KPIs ---' AS section;

SELECT
    ROUND(SUM(Sales_Amount), 2)                        AS Total_Sales,
    ROUND(SUM(Profit), 2)                              AS Total_Profit,
    COUNT(DISTINCT Order_ID)                           AS Total_Orders,
    SUM(Quantity)                                      AS Total_Quantity_Sold,
    ROUND(AVG(Discount), 4)                            AS Average_Discount,
    COUNT(DISTINCT Customer_ID)                        AS Unique_Customers,
    ROUND(AVG(Sales_Amount), 2)                        AS Average_Order_Value,
    ROUND(SUM(Profit) * 1.0 / SUM(Sales_Amount), 4)    AS Overall_Profit_Margin
FROM sales;


-- ============================================================
-- STEP 3 - BUSINESS INSIGHTS
-- ============================================================

-- Q1. Which state generates the highest sales?
SELECT '--- Q1: Sales by State ---' AS section;

SELECT
    State,
    ROUND(SUM(Sales_Amount), 2)                     AS Total_Sales,
    ROUND(SUM(Profit), 2)                           AS Total_Profit,
    COUNT(DISTINCT Order_ID)                        AS Total_Orders,
    SUM(Quantity)                                   AS Total_Quantity,
    ROUND(SUM(Profit) * 1.0 / SUM(Sales_Amount), 4) AS Profit_Margin,
    ROUND(SUM(Sales_Amount) * 100.0 /
          (SELECT SUM(Sales_Amount) FROM sales), 2) AS Pct_Of_Total_Sales
FROM sales
GROUP BY State
ORDER BY Total_Sales DESC;


-- Q2. Which product category is most profitable?
SELECT '--- Q2: Profit by Category ---' AS section;

SELECT
    Product_Category,
    ROUND(SUM(Sales_Amount), 2)                     AS Total_Sales,
    ROUND(SUM(Profit), 2)                           AS Total_Profit,
    ROUND(SUM(Profit) * 1.0 / SUM(Sales_Amount), 4) AS Profit_Margin,
    COUNT(DISTINCT Order_ID)                        AS Total_Orders,
    ROUND(AVG(Discount), 4)                         AS Avg_Discount
FROM sales
GROUP BY Product_Category
ORDER BY Total_Profit DESC;


-- Q3. Which products generate the highest revenue? (Top 10)
SELECT '--- Q3: Top 10 Products by Sales ---' AS section;

SELECT
    Product_Name,
    Product_Category,
    ROUND(SUM(Sales_Amount), 2)                     AS Total_Sales,
    ROUND(SUM(Profit), 2)                           AS Total_Profit,
    SUM(Quantity)                                   AS Units_Sold,
    COUNT(DISTINCT Order_ID)                        AS Total_Orders
FROM sales
GROUP BY Product_Name, Product_Category
ORDER BY Total_Sales DESC
LIMIT 10;


-- Q4. Which payment method is used the most?
SELECT '--- Q4: Payment Mode Popularity ---' AS section;

SELECT
    Payment_Mode,
    COUNT(DISTINCT Order_ID)                        AS Total_Orders,
    ROUND(COUNT(*) * 100.0 /
          (SELECT COUNT(*) FROM sales), 2)          AS Pct_Of_Orders,
    ROUND(SUM(Sales_Amount), 2)                     AS Total_Sales,
    ROUND(AVG(Sales_Amount), 2)                     AS Avg_Order_Value
FROM sales
GROUP BY Payment_Mode
ORDER BY Total_Orders DESC;


-- Q5. What is the monthly sales trend?
-- LAG() gives month-over-month growth in one pass.
SELECT '--- Q5: Monthly Sales Trend ---' AS section;

SELECT
    Order_Month,
    ROUND(SUM(Sales_Amount), 2)                     AS Total_Sales,
    ROUND(SUM(Profit), 2)                           AS Total_Profit,
    COUNT(DISTINCT Order_ID)                        AS Total_Orders,
    ROUND(
        (SUM(Sales_Amount) - LAG(SUM(Sales_Amount)) OVER (ORDER BY Order_Month))
        * 100.0 / LAG(SUM(Sales_Amount)) OVER (ORDER BY Order_Month), 2
    )                                               AS MoM_Growth_Pct
FROM sales
GROUP BY Order_Month
ORDER BY Order_Month;


-- Supporting: Sales by Category (revenue view, for the dashboard chart)
SELECT '--- Sales by Category ---' AS section;

SELECT
    Product_Category,
    ROUND(SUM(Sales_Amount), 2)                     AS Total_Sales,
    SUM(Quantity)                                   AS Total_Quantity,
    ROUND(SUM(Sales_Amount) * 100.0 /
          (SELECT SUM(Sales_Amount) FROM sales), 2) AS Pct_Of_Total_Sales
FROM sales
GROUP BY Product_Category
ORDER BY Total_Sales DESC;


-- Supporting: Sales by City.
-- NOTE: State and City are independent labels in this dataset, never a
-- hierarchy. See outputs/data_quality_report.md - every state is paired with
-- every city, so a State -> City drill-down would be meaningless.
SELECT '--- Sales by City ---' AS section;

SELECT
    City,
    ROUND(SUM(Sales_Amount), 2)                     AS Total_Sales,
    COUNT(DISTINCT Order_ID)                        AS Total_Orders
FROM sales
GROUP BY City
ORDER BY Total_Sales DESC;


-- ============================================================
-- HOW FLAT IS THIS DATA? - the check that reframes every ranking above
--
-- If the leader's share is close to 1/N, the ranking is a coin-flip.
-- The Python bootstrap in src/03_significance_tests.py confirms this
-- formally. This query is the quick SQL version of the same question.
-- ============================================================
SELECT '--- Dispersion check: is any ranking real? ---' AS section;

WITH state_totals AS (
    SELECT State, SUM(Sales_Amount) AS total FROM sales GROUP BY State
)
SELECT
    'State'                                          AS Dimension,
    COUNT(*)                                         AS N_Groups,
    ROUND(MIN(total), 0)                             AS Min_Sales,
    ROUND(MAX(total), 0)                             AS Max_Sales,
    ROUND((MAX(total) - MIN(total)) * 100.0 / AVG(total), 2) AS Spread_Pct_Of_Mean,
    ROUND(100.0 / COUNT(*), 2)                       AS Even_Share_Pct,
    ROUND(MAX(total) * 100.0 / SUM(total), 2)        AS Leader_Share_Pct
FROM state_totals

UNION ALL

SELECT
    'Product_Category', COUNT(*), ROUND(MIN(total), 0), ROUND(MAX(total), 0),
    ROUND((MAX(total) - MIN(total)) * 100.0 / AVG(total), 2),
    ROUND(100.0 / COUNT(*), 2),
    ROUND(MAX(total) * 100.0 / SUM(total), 2)
FROM (SELECT Product_Category, SUM(Sales_Amount) AS total FROM sales GROUP BY Product_Category)

UNION ALL

SELECT
    'Payment_Mode', COUNT(*), ROUND(MIN(total), 0), ROUND(MAX(total), 0),
    ROUND((MAX(total) - MIN(total)) * 100.0 / AVG(total), 2),
    ROUND(100.0 / COUNT(*), 2),
    ROUND(MAX(total) * 100.0 / SUM(total), 2)
FROM (SELECT Payment_Mode, SUM(Sales_Amount) AS total FROM sales GROUP BY Payment_Mode);


-- ============================================================
-- DATA QUALITY CHECKS - these should all return zero rows
-- ============================================================
SELECT '--- Data quality: duplicate Order_IDs (expect none) ---' AS section;
SELECT Order_ID, COUNT(*) AS n FROM sales GROUP BY Order_ID HAVING n > 1;

SELECT '--- Data quality: invalid numbers (expect none) ---' AS section;
SELECT COUNT(*) AS invalid_rows
FROM sales
WHERE Quantity <= 0 OR Sales_Amount <= 0 OR Discount < 0 OR Discount > 1;

SELECT '--- Data quality: products spanning multiple categories (expect none) ---' AS section;
SELECT Product_Name, COUNT(DISTINCT Product_Category) AS n_categories
FROM sales
GROUP BY Product_Name
HAVING n_categories > 1;

-- This one deliberately DOES return rows: it documents the known defect.
SELECT '--- Known defect: every state pairs with every city ---' AS section;
SELECT
    COUNT(DISTINCT State)                AS n_states,
    COUNT(DISTINCT City)                 AS n_cities,
    COUNT(DISTINCT State || '|' || City) AS n_distinct_pairs,
    CASE WHEN COUNT(DISTINCT State || '|' || City)
              = COUNT(DISTINCT State) * COUNT(DISTINCT City)
         THEN 'RANDOMISED - do not treat State/City as a hierarchy'
         ELSE 'plausible geography'
    END                                  AS verdict
FROM sales;
