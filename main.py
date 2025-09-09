from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models import Recipe
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "recipes.db")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

app = FastAPI(title="Recipes API - Docker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if not os.path.isdir(frontend_dir):
    frontend_dir = "frontend"
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def root():
    return RedirectResponse(url="/index")

@app.get("/index", include_in_schema=False)
def index_file():
    p = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if not os.path.exists(p):
        p = os.path.join("frontend", "index.html")
    if not os.path.exists(p):
        return JSONResponse(status_code=404, content={"detail":"index.html not found", "path_checked": p})
    return FileResponse(p, media_type="text/html")

@app.get("/health")
def health():
    return {"status":"ok"}

def parse_filter_param(raw: str):
    if raw is None:
        return None, None
    if ":" in raw:
        op, val = raw.split(":", 1)
        return op, val
    if raw.startswith(">="):
        return "gte", raw[2:]
    if raw.startswith("<="):
        return "lte", raw[2:]
    if raw.startswith(">"):
        return "gt", raw[1:]
    if raw.startswith("<"):
        return "lt", raw[1:]
    return "eq", raw

@app.get("/api/recipes")
def get_recipes(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=200)):
    session = Session()
    try:
        total = session.query(Recipe).count()
        qs = session.query(Recipe).order_by(desc(Recipe.rating))
        qs = qs.offset((page-1)*limit).limit(limit)
        rows = qs.all()
        data = []
        for r in rows:
            data.append({
                "id": r.id,
                "title": r.title,
                "cuisine": r.cuisine,
                "rating": r.rating,
                "prep_time": r.prep_time,
                "cook_time": r.cook_time,
                "total_time": r.total_time,
                "description": (r.description[:300] + "...") if r.description and len(r.description)>300 else r.description,
                "nutrients": r.nutrients,
                "serves": r.serves
            })
        return {"page": page, "limit": limit, "total": total, "data": data}
    finally:
        session.close()

@app.get("/api/recipes/search")
def search_recipes(title: str = None, cuisine: str = None, rating: str = None, total_time: str = None, calories: str = None, page: int = Query(1, ge=1), limit: int = Query(10, ge=1)):
    session = Session()
    try:
        qs = session.query(Recipe)
        filters = []
        if title:
            filters.append(Recipe.title.ilike(f"%{title}%"))
        if cuisine:
            filters.append(Recipe.cuisine.ilike(f"%{cuisine}%"))
        if rating:
            op, val = parse_filter_param(rating)
            try:
                valf = float(val)
                if op in ("gte","ge", "gt"):
                    filters.append(Recipe.rating >= valf)
                elif op in ("lte","le", "lt"):
                    filters.append(Recipe.rating <= valf)
                else:
                    filters.append(Recipe.rating == valf)
            except:
                pass
        if total_time:
            op, val = parse_filter_param(total_time)
            try:
                vi = int(float(val))
                if op in ("gte","ge", "gt"):
                    filters.append(Recipe.total_time >= vi)
                elif op in ("lte","le", "lt"):
                    filters.append(Recipe.total_time <= vi)
                else:
                    filters.append(Recipe.total_time == vi)
            except:
                pass
        if calories:
            op, val = parse_filter_param(calories)
            try:
                vi = float(val)
                all_rows = qs.all()
                matched_ids = []
                for r in all_rows:
                    try:
                        cal = r.nutrients.get("calories", "") if r.nutrients else ""
                        if isinstance(cal, str):
                            num = "".join([c for c in cal if (c.isdigit() or c=='.')])
                            if num=="":
                                continue
                            numf = float(num)
                            ok = False
                            if op in ("gte","ge", "gt"):
                                ok = numf >= vi
                            elif op in ("lte","le", "lt"):
                                ok = numf <= vi
                            else:
                                ok = numf == vi
                            if ok:
                                matched_ids.append(r.id)
                    except:
                        continue
                if matched_ids:
                    filters.append(Recipe.id.in_(matched_ids))
                else:
                    return {"page": page, "limit": limit, "total": 0, "data": []}
            except:
                pass
        if filters:
            qs = qs.filter(*filters)
        total = qs.count()
        qs = qs.order_by(desc(Recipe.rating)).offset((page-1)*limit).limit(limit)
        rows = qs.all()
        data = []
        for r in rows:
            data.append({
                "id": r.id,
                "title": r.title,
                "cuisine": r.cuisine,
                "rating": r.rating,
                "prep_time": r.prep_time,
                "cook_time": r.cook_time,
                "total_time": r.total_time,
                "description": r.description,
                "nutrients": r.nutrients,
                "serves": r.serves
            })
        return {"page": page, "limit": limit, "total": total, "data": data}
    finally:
        session.close()

@app.get("/api/recipes/{recipe_id}")
def get_recipe(recipe_id: int):
    session = Session()
    try:
        r = session.query(Recipe).get(recipe_id)
        if not r:
            return JSONResponse(status_code=404, content={"detail":"Not found"})
        return {"id": r.id, "title": r.title, "cuisine": r.cuisine, "rating": r.rating, "prep_time": r.prep_time, "cook_time": r.cook_time, "total_time": r.total_time, "description": r.description, "nutrients": r.nutrients, "serves": r.serves}
    finally:
        session.close()
