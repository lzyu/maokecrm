-- Add opportunity_name column to sales_opportunities table
ALTER TABLE sales_opportunities
ADD COLUMN IF NOT EXISTS opportunity_name VARCHAR(200) NOT NULL DEFAULT '';
