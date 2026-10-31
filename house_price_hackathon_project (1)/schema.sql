CREATE TABLE IF NOT EXISTS houses (
    listing_id TEXT,
    property_id TEXT,
    city TEXT NOT NULL,
    locality TEXT,
    sold_on TEXT,
    area_sqft REAL NOT NULL,
    bedrooms INTEGER,
    bathrooms REAL,
    age_years REAL,
    floor REAL,
    parking TEXT,
    furnishing TEXT,
    sale_price_inr REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_houses_city ON houses(city);
CREATE INDEX IF NOT EXISTS idx_houses_locality ON houses(locality);
CREATE INDEX IF NOT EXISTS idx_houses_sold_on ON houses(sold_on);
CREATE INDEX IF NOT EXISTS idx_houses_property_id ON houses(property_id);
