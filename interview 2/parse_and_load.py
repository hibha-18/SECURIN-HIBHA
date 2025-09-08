import json, math, os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Recipe

DATA_FILE = os.path.join(os.path.dirname(__file__), "US_recipes_null.Pdf.json")
DB_FILE = os.path.join(os.path.dirname(__file__), "recipes.db")
ENGINE = create_engine(f"sqlite:///{DB_FILE}", connect_args={"check_same_thread": False})

def is_number(val):
    try:
        if val is None:
            return False
        if isinstance(val, str):
            v = val.strip().lower()
            if v == "" or v == "nan":
                return False
        if isinstance(val, float) and math.isnan(val):
            return False
        float(val)
        return True
    except:
        return False

def clean_numeric(val):
    if is_number(val):
        return float(val)
    return None

def clean_int(val):
    if is_number(val):
        return int(float(val))
    return None

def main():
    Base.metadata.create_all(ENGINE)
    Session = sessionmaker(bind=ENGINE)
    session = Session()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    inserted = 0
    for k, rec in data.items():
        try:
            cuisine = rec.get("cuisine") or rec.get("Cuisine") or None
            title = rec.get("title") or rec.get("name") or "Untitled"
            rating = clean_numeric(rec.get("rating", None))
            prep_time = clean_int(rec.get("prep_time", None) or rec.get("prepTime", None))
            cook_time = clean_int(rec.get("cook_time", None) or rec.get("cookTime", None))
            total_time = clean_int(rec.get("total_time", None) or rec.get("totalTime", None))
            description = rec.get("description") or ""
            nutrients = rec.get("nutrients") or {}
            serves = rec.get("serves") or rec.get("yield") or None
            r = Recipe(
                cuisine=cuisine,
                title=title,
                rating=rating,
                prep_time=prep_time,
                cook_time=cook_time,
                total_time=total_time,
                description=description,
                nutrients=nutrients,
                serves=serves
            )
            session.add(r)
            inserted += 1
        except Exception as e:
            print("Skipping", k, "error:", e)
    session.commit()
    session.close()
    print(f"Inserted {inserted} records into {DB_FILE}")

if __name__ == '__main__':
    main()
