from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.authentication import AuthenticationBackend, AuthCredentials
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Annotated, Union
from datetime import datetime, timedelta, timezone
import sqlite3, random
from .config import ADMINDB_PATH, SECRET_KEY

from .main import app, templates

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 21


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str  # we will use emails as usernames
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def tokens(self) -> list[str]:
        ADMINDB = sqlite3.connect(ADMINDB_PATH)
        return [
            token
            for token, in ADMINDB.execute(
                "SELECT token FROM tokens WHERE user = ?", (self.username,)
            )
        ]


class UserInDB(User):
    hashed_password: str


def verify_auth_token(token: str):
    ADMINDB = sqlite3.connect(ADMINDB_PATH)
    for (
        user,
        token,
    ) in ADMINDB.execute("SELECT user, token FROM tokens WHERE token = ?", (token,)):
        return True
    return False


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    ADMINDB = sqlite3.connect(ADMINDB_PATH)
    for email, username, disabled, password in ADMINDB.execute(
        "SELECT email, username, disabled, password FROM users WHERE email = ?",
        (username,),
    ):
        return UserInDB(
            username=email,
            full_name=username,
            disabled=disabled,
            hashed_password=password,
        )


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


class CookieTokenAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        access_token = request.cookies.get("access_token")
        if access_token:
            user = await get_current_user(access_token)
            return AuthCredentials(["authenticated"]), user


app.add_middleware(AuthenticationMiddleware, backend=CookieTokenAuthBackend())


@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@app.get("/users/{user_id}", response_class=HTMLResponse)
async def user_info(
    request: Request, user_id: str, token: Annotated[str, Depends(oauth2_scheme)]
):
    return templates.TemplateResponse(
        "user_info.html",
        {
            "request": request,
            "user_id": user_id,
        },
    )


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def loginpage(request: Request):

    response = templates.TemplateResponse(
        "login.html",
        {
            "request": request,
        },
    )
    return response


@app.post("/users/create", response_class=JSONResponse)
async def users_create(request: Request, user: UserInDB):
    ADMINDB = sqlite3.connect(ADMINDB_PATH)

    try:
        ADMINDB.execute(
            "INSERT INTO users (email, username, password, disabled) VALUES (?, ?, ?, ?)",
            (
                user.username,
                user.full_name,
                get_password_hash(user.hashed_password),
                False,
            ),
        )
        ADMINDB.execute(
            "INSERT INTO tokens (user, token) VALUES (?, ?)",
            (
                user.username,
                "".join([random.choice("abcdef0123456789") for x in range(20)]),
            ),
        )
        ADMINDB.commit()
    except sqlite3.IntegrityError:
        return JSONResponse(
            content={"status": "error", "message": "User already exists"}
        )
    return JSONResponse(content={"status": "ok"})


# To create new users:
# curl -X POST -H "Content-Type: application/json" -d '{"username": "eposthumus@gmail.com", "full_name": "Etienne Posthumus", "hashed_password": "nifty"}' http://localhost:10000/users/create
