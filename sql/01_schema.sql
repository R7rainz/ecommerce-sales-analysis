-- ============================================================
-- E-Commerce Sales Analysis - Schema
-- Target: SQLite (portable; runs with no server setup)
--
-- Build the database from the cleaned CSV:
--   sqlite3 outputs/ecommerce.db < sql/01_schema.sql
--   sqlite3 outputs/ecommerce.db ".import --csv --skip 1 data/processed/ecommerce_sales_cleaned.csv sales_raw_import"
--   sqlite3 outputs/ecommerce.db < sql/02_load.sql
--
-- Or simply run:  python src/05_build_database.py
-- ============================================================

DROP TABLE IF EXISTS sales;

CREATE TABLE sales (
    Order_ID         TEXT    NOT NULL PRIMARY KEY,
    Order_Date       DATE    NOT NULL,
    Customer_ID      TEXT    NOT NULL,
    Product_Category TEXT    NOT NULL,
    Product_Name     TEXT    NOT NULL,
    State            TEXT    NOT NULL,
    City             TEXT    NOT NULL,
    Payment_Mode     TEXT    NOT NULL,
    Quantity         INTEGER NOT NULL CHECK (Quantity > 0),
    Sales_Amount     REAL    NOT NULL CHECK (Sales_Amount > 0),
    Discount         REAL    NOT NULL CHECK (Discount >= 0 AND Discount <= 1),
    Profit           REAL    NOT NULL,
    Order_Month      TEXT    NOT NULL,
    Order_Year       INTEGER NOT NULL,
    Profit_Margin    REAL
);

-- Indexes on the columns every insight query groups by.
CREATE INDEX idx_sales_state       ON sales (State);
CREATE INDEX idx_sales_category    ON sales (Product_Category);
CREATE INDEX idx_sales_payment     ON sales (Payment_Mode);
CREATE INDEX idx_sales_month       ON sales (Order_Month);
CREATE INDEX idx_sales_product     ON sales (Product_Name);
CREATE INDEX idx_sales_order_date  ON sales (Order_Date);
