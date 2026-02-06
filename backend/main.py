import os
import re
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from services.search_service import search_clinic
from services.auth_service import verify_password, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from jose import JWTError, jwt

# Rate Limiter Configuration
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security & Auth Configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Single User Configuration
ADMIN_USER = "ambulatorio"
# Default password if not set: Ambulatorio2026!
ADMIN_PASSWORD_HASH = get_password_hash(os.getenv("ADMIN_PASSWORD", ""))

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

# Input Sanitization
def sanitize_input(text: str) -> str:
    if not text:
        return text
    # Remove HTML tags and potential script injections
    return re.sub(r'<[^>]*>', '', text)

# Dependencies
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username != ADMIN_USER:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

# Routes
@app.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    username = sanitize_input(form_data.username)
    # Password verification
    if username != ADMIN_USER or not verify_password(form_data.password, ADMIN_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/search")
@limiter.limit("20/minute")
def search(request: Request, query: str, engine: str | None = None, current_user: str = Depends(get_current_user)):
    """
    Search for a clinic by name. Protected route.
    """
    sanitized_query = sanitize_input(query)
    result = search_clinic(sanitized_query, engine=engine)
    return result
