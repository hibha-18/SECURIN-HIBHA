-- Postgres compatible schema
CREATE TABLE recipes (id SERIAL PRIMARY KEY, cuisine VARCHAR, title VARCHAR, rating FLOAT, prep_time INTEGER, cook_time INTEGER, total_time INTEGER, description TEXT, nutrients JSONB, serves VARCHAR);
