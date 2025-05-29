from fastapi import FastAPI, Depends, HTTPException, Path, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Set, Dict

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

# --- MODELS ---

class LoginData(BaseModel):
    username: str
    password: str

class ProductBase(BaseModel):
    name: str
    price: float
    category: Optional[str] = None  # za filtere
    description: Optional[str] = None  # dodatni opis

class Product(ProductBase):
    id: int

class Review(BaseModel):
    product_id: int
    username: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)

class WishlistItem(BaseModel):
    product_id: int

class PurchaseRecord(BaseModel):
    product_id: int
    quantity: int
    total_price: float

class UserProfile(BaseModel):
    username: str
    role: str

# --- DATA STORAGE (u memoriji) ---

products: List[Product] = []
reviews: List[Review] = []
user_carts: Dict[str, List[CartItem]] = {}
user_wishlist: Dict[str, Set[int]] = {}
user_purchase_history: Dict[str, List[PurchaseRecord]] = {}

# --- HELPERS ---

def get_next_id() -> int:
    if products:
        return max(product.id for product in products) + 1
    return 1

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

# --- AUTH ---

@app.post("/login")
def login(data: LoginData):
    user = USERS.get(data.username)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Pogrešno korisničko ime ili lozinka")
    token = user["password"]  # u pravoj aplikaciji koristi JWT ili slično
    return {"access_token": token, "token_type": "bearer"}

# --- PROFILE ---

@app.get("/profile")
def get_profile(username: str = Depends(get_current_username)):
    user = USERS.get(username)
    return UserProfile(username=username, role=user["role"])

# --- PRODUCTS ---

@app.post("/admin/products")
def add_product(product_data: ProductBase, username: str = Depends(get_current_username)):
    check_admin(username)
    new_id = get_next_id()
    product = Product(id=new_id, **product_data.dict())
    products.append(product)
    return {"message": "Proizvod dodat.", "product": product}

@app.get("/products")
def list_products(
    username: str = Depends(get_current_username),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    sort: Optional[str] = Query(None)  # najnoviji, najprodavaniji, price_asc, price_desc
):
    filtered = products
    if category:
        filtered = [p for p in filtered if p.category == category]
    if min_price is not None:
        filtered = [p for p in filtered if p.price >= min_price]
    if max_price is not None:
        filtered = [p for p in filtered if p.price <= max_price]

    if sort == "price_asc":
        filtered.sort(key=lambda p: p.price)
    elif sort == "price_desc":
        filtered.sort(key=lambda p: p.price, reverse=True)
    elif sort == "newest":
        filtered.sort(key=lambda p: p.id, reverse=True)
    elif sort == "oldest":
        filtered.sort(key=lambda p: p.id)

    # TODO: za "najprodavaniji" treba statistika prodaja, možemo implementirati kasnije

    return {"products": filtered}

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

# --- REVIEWS ---

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

# --- CART ---

@app.post("/cart")
def add_to_cart(item: CartItem, username: str = Depends(get_current_username)):
    cart = user_carts.setdefault(username, [])
    for citem in cart:
        if citem.product_id == item.product_id:
            citem.quantity += item.quantity
            break
    else:
        cart.append(item)
    return {"message": "Proizvod dodat u korpu.", "cart": cart}

@app.get("/cart")
def get_cart(username: str = Depends(get_current_username)):
    return {"cart": user_carts.get(username, [])}

@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int, username: str = Depends(get_current_username)):
    cart = user_carts.get(username, [])
    for idx, citem in enumerate(cart):
        if citem.product_id == product_id:
            cart.pop(idx)
            return {"message": "Proizvod uklonjen iz korpe.", "cart": cart}
    raise HTTPException(status_code=404, detail="Proizvod nije u korpi")

# --- WISHLIST ---

@app.post("/wishlist/{product_id}")
def add_to_wishlist(product_id: int, username: str = Depends(get_current_username)):
    wishlist = user_wishlist.setdefault(username, set())
    wishlist.add(product_id)
    return {"message": "Proizvod dodat u wishlistu.", "wishlist": list(wishlist)}

@app.get("/wishlist")
def get_wishlist(username: str = Depends(get_current_username)):
    wishlist = user_wishlist.get(username, set())
    products_in_wishlist = [p for p in products if p.id in wishlist]
    return {"wishlist": products_in_wishlist}

@app.delete("/wishlist/{product_id}")
def remove_from_wishlist(product_id: int, username: str = Depends(get_current_username)):
    wishlist = user_wishlist.get(username, set())
    if product_id in wishlist:
        wishlist.remove(product_id)
        return {"message": "Proizvod uklonjen iz wishliste.", "wishlist": list(wishlist)}
    raise HTTPException(status_code=404, detail="Proizvod nije u wishlisti")

# --- PURCHASE / CHECKOUT ---

@app.post("/checkout")
def checkout(username: str = Depends(get_current_username)):
    cart = user_carts.get(username, [])
    if not cart:
        raise HTTPException(status_code=400, detail="Korpa je prazna.")
    total = 0.0
    for item in cart:
        product = next((p for p in products if p.id == item.product_id), None)
        if not product:
            raise HTTPException(status_code=404, detail=f"Proizvod sa ID {item.product_id} ne postoji.")
        total += product.price * item.quantity

    # Evidencija kupovine
    history = user_purchase_history.setdefault(username, [])
    for item in cart:
        product = next((p for p in products if p.id == item.product_id), None)
        if product:
            record = PurchaseRecord(
                product_id=product.id,
                quantity=item.quantity,
                total_price=product.price * item.quantity
            )
            history.append(record)

    user_carts[username] = []  # praznimo korpu nakon kupovine

    return {"message": "Kupovina uspešno završena.", "total": total}

# --- PURCHASE HISTORY ---

@app.get("/purchase-history")
def get_purchase_history(username: str = Depends(get_current_username)):
    history = user_purchase_history.get(username, [])
    return {"purchase_history": history}

# --- ROOT ---

@app.get("/")
def read_root(username: str = Depends(get_current_username)):
    return {"message": f"Zdravo, ulogovan si kao '{username}'."}

@app.get("/admin")
def read_admin(username: str = Depends(get_current_username)):
    check_admin(username)
    return {"message": f"Dobrodošao, admin '{username}'!"}
