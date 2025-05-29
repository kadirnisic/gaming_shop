from fastapi import FastAPI, Depends, HTTPException, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI()

# CORS za frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# USERS: username -> password i role
USERS = {
    "admin": {"password": "gaming123", "role": "admin"},
    "user": {"password": "user123", "role": "user"},
}

class LoginData(BaseModel):
    username: str
    password: str

class ProductBase(BaseModel):
    name: str
    price: float

class Product(ProductBase):
    id: int

products: List[Product] = []

# Automatski id generator
def get_next_id() -> int:
    if products:
        return max(product.id for product in products) + 1
    return 1

@app.post("/login")
def login(data: LoginData):
    user = USERS.get(data.username)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Pogrešno korisničko ime ili lozinka")
    token = user["password"]
    return {"access_token": token, "token_type": "bearer"}

def get_current_username(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    for username, data in USERS.items():
        if data["password"] == token:
            return username
    raise HTTPException(status_code=401, detail="Unauthorized")

def check_admin(username: str):
    user = USERS.get(username)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: samo admini imaju pristup")

@app.get("/")
def read_root(username: str = Depends(get_current_username)):
    return {"message": f"Zdravo, ulogovan si kao '{username}'."}

@app.get("/admin")
def read_admin(username: str = Depends(get_current_username)):
    check_admin(username)
    return {"message": f"Dobrodošao, admin '{username}'!"}

@app.post("/admin/products")
def add_product(product_data: ProductBase, username: str = Depends(get_current_username)):
    check_admin(username)
    new_id = get_next_id()
    product = Product(id=new_id, **product_data.dict())
    products.append(product)
    return {"message": "Proizvod dodat.", "product": product}

@app.get("/products")
def list_products(username: str = Depends(get_current_username)):
    return {"products": products}

@app.put("/admin/products/{product_id}")
def update_product(
    product_id: int = Path(..., ge=1),
    product_data: ProductBase = ...,
    username: str = Depends(get_current_username)
):
    check_admin(username)
    for idx, product in enumerate(products):
        if product.id == product_id:
            updated_product = Product(id=product_id, **product_data.dict())
            products[idx] = updated_product
            return {"message": "Proizvod ažuriran.", "product": updated_product}
    raise HTTPException(status_code=404, detail="Proizvod nije pronađen")

@app.delete("/admin/products/{product_id}")
def delete_product(
    product_id: int = Path(..., ge=1),
    username: str = Depends(get_current_username)
):
    check_admin(username)
    for idx, product in enumerate(products):
        if product.id == product_id:
            deleted = products.pop(idx)
            return {"message": "Proizvod obrisan.", "product": deleted}
    raise HTTPException(status_code=404, detail="Proizvod nije pronađen")

# ------------------------
from fastapi import FastAPI, Depends, HTTPException, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI()

# CORS za frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# USERS: username -> password i role
USERS = {
    "admin": {"password": "gaming123", "role": "admin"},
    "user": {"password": "user123", "role": "user"},
}

class LoginData(BaseModel):
    username: str
    password: str

class ProductBase(BaseModel):
    name: str
    price: float

class Product(ProductBase):
    id: int

products: List[Product] = []

# Automatski id generator
def get_next_id() -> int:
    if products:
        return max(product.id for product in products) + 1
    return 1

@app.post("/login")
def login(data: LoginData):
    user = USERS.get(data.username)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Pogrešno korisničko ime ili lozinka")
    token = user["password"]
    return {"access_token": token, "token_type": "bearer"}

def get_current_username(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    for username, data in USERS.items():
        if data["password"] == token:
            return username
    raise HTTPException(status_code=401, detail="Unauthorized")

def check_admin(username: str):
    user = USERS.get(username)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: samo admini imaju pristup")

@app.get("/")
def read_root(username: str = Depends(get_current_username)):
    return {"message": f"Zdravo, ulogovan si kao '{username}'."}

@app.get("/admin")
def read_admin(username: str = Depends(get_current_username)):
    check_admin(username)
    return {"message": f"Dobrodošao, admin '{username}'!"}

@app.post("/admin/products")
def add_product(product_data: ProductBase, username: str = Depends(get_current_username)):
    check_admin(username)
    new_id = get_next_id()
    product = Product(id=new_id, **product_data.dict())
    products.append(product)
    return {"message": "Proizvod dodat.", "product": product}

@app.get("/products")
def list_products(username: str = Depends(get_current_username)):
    return {"products": products}

@app.put("/admin/products/{product_id}")
def update_product(
    product_id: int = Path(..., ge=1),
    product_data: ProductBase = ...,
    username: str = Depends(get_current_username)
):
    check_admin(username)
    for idx, product in enumerate(products):
        if product.id == product_id:
            updated_product = Product(id=product_id, **product_data.dict())
            products[idx] = updated_product
            return {"message": "Proizvod ažuriran.", "product": updated_product}
    raise HTTPException(status_code=404, detail="Proizvod nije pronađen")

@app.delete("/admin/products/{product_id}")
def delete_product(
    product_id: int = Path(..., ge=1),
    username: str = Depends(get_current_username)
):
    check_admin(username)
    for idx, product in enumerate(products):
        if product.id == product_id:
            deleted = products.pop(idx)
            return {"message": "Proizvod obrisan.", "product": deleted}
    raise HTTPException(status_code=404, detail="Proizvod nije pronađen")

# ------------------------
# Recenzije (Reviews)
# ------------------------

class Review(BaseModel):
    product_id: int
    username: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

reviews: List[Review] = []

@app.post("/reviews")
def add_review(review: Review, username: str = Depends(get_current_username)):
    if username != review.username:
        raise HTTPException(status_code=403, detail="Ne možeš dodati recenziju u tuđe ime.")
    if not any(p.id == review.product_id for p in products):
        raise HTTPException(status_code=404, detail="Proizvod ne postoji.")
    reviews.append(review)
    return {"message": "Recenzija uspešno sačuvana."}

@app.get("/products/{product_id}/reviews")
def get_reviews(product_id: int, username: str = Depends(get_current_username)):
    product_reviews = [r for r in reviews if r.product_id == product_id]
    return {"reviews": product_reviews}
