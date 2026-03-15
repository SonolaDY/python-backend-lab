# Understand the three projects

## Start here

Run the tests and live demo from the README. Open `backend_lab/__init__.py`: `create_app()` configures one Flask app, initializes the data sources, and registers three blueprints. A blueprint groups related routes. The shared JSON error handler preserves HTTP status and headers while making error responses consistent.

## Text Analyzer: the smallest project

Read `analyze()` in `text_analyzer.py`. It extracts words, normalizes spelling, builds a `Counter`, and sorts by descending frequency. The route validates input before calling that function. Keeping calculation separate from HTTP handling makes it easier to reuse.

Try predicting the result of `Hello hello, café!` before sending it. Then change `top_n` to 1. Explain why character count differs from word count and why ties have a stable order.

Small extension: add an optional stop-word list, validate it, and test that it changes frequencies without changing the original character count.

## Student Records: the best starting point for CRM discussions

Follow a POST through `create_student()`: parse JSON, validate and normalize fields, bind values into an INSERT, commit the transaction, and return a record with status 201. SQLite assigns the id; the server creates timestamps. The Location header points to the created record.

Follow PATCH next. Only allowed fields can become SQL column names, and all values use placeholders. Explain why passing a name containing a quote is safe. Tests also submit SQL-shaped text as a filter and verify that it remains a value, not executable SQL.

Use the demo to create, retrieve, update, and delete a record. Restart the app after creating a record to see persistence. Explain why omitted PATCH fields stay unchanged and why an invalid request must leave the record untouched.

Small extension: add a `status` field restricted to `new`, `active`, and `inactive`. Plan how to update existing SQLite databases before changing the schema.

## Countries Insights: aggregation without a database

Read `load_countries()` first: malformed files fail during startup rather than later during a request. Data is loaded once; queries filter it in memory. Language labels are normalized and deduplicated within each country.

Explain why counting countries that list a language cannot tell you how many people speak it. The demo uses fictional country names and populations deliberately. `total` counts all matching rows, even when `limit` returns only two.

Small extension: add a minimum-population filter and test both no matches and a boundary match.

## Explain the choices in your own words

- Why Flask and SQLite keep the setup small.
- How request validation protects stored data and gives callers useful errors.
- How GET, POST, PATCH, and DELETE map to different operations and status codes.
- Why a SQL placeholder is different from assembling values into a query string.
- What a test client checks and why the live demo is also useful.
- What would need to change before this app could store real customer information.

Use the demo and one small extension to practice explaining the code in your own words.
