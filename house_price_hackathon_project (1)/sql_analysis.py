from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent / "instance" / "houses.db"

QUERIES = {
    "Average sale price by city": """
        SELECT city, COUNT(*) AS sales,
               ROUND(AVG(sale_price_inr), 0) AS average_price_inr
        FROM houses GROUP BY city ORDER BY average_price_inr DESC;
    """,
    "Top 10 localities by average price (minimum 5 sales)": """
        SELECT city, locality, COUNT(*) AS sales,
               ROUND(AVG(sale_price_inr), 0) AS average_price_inr
        FROM houses GROUP BY city, locality
        HAVING COUNT(*) >= 5
        ORDER BY average_price_inr DESC LIMIT 10;
    """,
    "Average sale price by bedroom count": """
        SELECT bedrooms, COUNT(*) AS sales,
               ROUND(AVG(sale_price_inr), 0) AS average_price_inr
        FROM houses GROUP BY bedrooms ORDER BY bedrooms;
    """,
    "Sales by year": """
        SELECT substr(sold_on, 1, 4) AS sale_year, COUNT(*) AS sales,
               ROUND(AVG(sale_price_inr), 0) AS average_price_inr
        FROM houses GROUP BY sale_year ORDER BY sale_year;
    """,
    "Parking comparison": """
        SELECT parking, COUNT(*) AS sales,
               ROUND(AVG(sale_price_inr), 0) AS average_price_inr
        FROM houses GROUP BY parking ORDER BY average_price_inr DESC;
    """
}


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError("Run `python train_model.py` first to create the database.")
    with sqlite3.connect(DB_PATH) as conn:
        for title, query in QUERIES.items():
            print("\\n" + "=" * 72)
            print(title)
            print("-" * 72)
            print(query.strip())
            rows = conn.execute(query).fetchall()
            for row in rows:
                print(row)


if __name__ == "__main__":
    main()
