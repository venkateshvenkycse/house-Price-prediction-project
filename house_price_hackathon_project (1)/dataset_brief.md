# Seed data

`houses.csv`, 1,456 rows. Past residential sales scraped from a listings site, one row per sale, with
the price the house sold for.

| Column | Meaning |
|---|---|
| `listing_id` | The listing the sale came from. |
| `property_id` | The house itself. A house that sells twice keeps its `property_id` and gets a new `listing_id`. |
| `city` | Hyderabad, Bengaluru or Vijayawada, as typed by whoever made the listing. |
| `locality` | Area within the city. |
| `sold_on` | Date the sale completed. Prices rise over time, so this matters. |
| `area_sqft` | Built up area in square feet. |
| `bedrooms`, `bathrooms` | Counts. |
| `age_years` | Age of the building at the time of sale. |
| `floor` | Floor number. 0 is the ground floor. |
| `parking` | `none`, `1` or `2` covered spaces. |
| `furnishing` | `unfurnished`, `semi` or `full`. |
| `price_per_sqft` | Added by the listings site **after the sale completed**, by dividing the sale price by the area. |
| `sale_price_inr` | **The label.** What the house sold for, in rupees. |

## Facts about this data worth reading twice

Stated plainly, because the brief is not a guessing game. What you do about them is the assessment.

* **Read the `price_per_sqft` description again**, and note when in a sale's life that value comes
  into existence, compared with the moment the site would need an estimate.
* **The same house appears more than once.** Over a hundred and fifty houses sold twice. Their prices
  are close, because it is the same house.
* **There are exact duplicate rows**, because the scraper ran twice over some pages. More than twenty.
* **The data is real world messy.** A handful of prices were typed in lakhs instead of rupees. City
  names are spelled several ways. Some values are missing, at least one is impossible, at least one
  is absurd, one row has no price at all and one has a price that is not a number.

## Scope note

You are not being marked on how good the model is. A linear regression is completely acceptable. You
are being marked on whether the error you report at the end is true, and whether you can say what it
means for a buyer looking at a listing.
