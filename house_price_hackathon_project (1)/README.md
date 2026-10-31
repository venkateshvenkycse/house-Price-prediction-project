# House Price Prediction — Hackathon Project

A small end-to-end project using the provided `houses.csv`: data cleaning, SQLite, SQL analysis, a regression model, and a Flask HTTP API with a simple web form.

## Features
- Cleans inconsistent city names, duplicate rows, invalid/missing values, and prices entered in lakhs.
- Excludes `price_per_sqft` from model features because it is calculated after the sale and leaks the target.
- Uses a group split by `property_id` to reduce repeat-property leakage between train and test data.
- Stores cleaned data in SQLite (`instance/houses.db`).
- Trains a scikit-learn regression pipeline and reports MAE, RMSE, and R².
- Provides a browser form and `POST /predict` API.

## Setup (Windows PowerShell)
1. Put `houses.csv` in this project folder.
2. Create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install packages:
   ```powershell
   pip install -r requirements.txt
   ```
4. Clean data, create SQLite database, and train the model:
   ```powershell
   python train_model.py
   ```
5. Start the web app:
   ```powershell
   python app.py
   ```
6. Open http://127.0.0.1:5000 in your browser.

## SQL analysis
After running `train_model.py`, run:
```powershell
python sql_analysis.py
```
It prints example analysis queries and their results.

## API example
```powershell
curl.exe -X POST http://127.0.0.1:5000/predict `
  -H "Content-Type: application/json" `
  -d "{\"city\":\"Hyderabad\",\"locality\":\"Gachibowli\",\"area_sqft\":1200,\"bedrooms\":2,\"bathrooms\":2,\"age_years\":5,\"floor\":3,\"parking\":\"1\",\"furnishing\":\"semi\",\"sold_on\":\"2026-10-29\"}"
```

## Important notes
- This is a learning/demo model, not a professional valuation tool.
- Predictions can be unreliable for localities or property types with few examples.
- The model uses historical sale data; market conditions may change.
- Do not use `price_per_sqft` as an input feature.
- The cleaning code uses explicit validation rules and logs rows dropped. Review the cleaning report before presenting results.

## Project structure
```text
house_price_hackathon/
  houses.csv                 # copy your provided dataset here
  train_model.py             # cleaning, SQLite load, model training/evaluation
  app.py                     # Flask web app + JSON API
  sql_analysis.py             # example SQL queries
  schema.sql                 # database schema
  templates/index.html       # simple browser UI
  static/style.css           # styling
  requirements.txt
```
