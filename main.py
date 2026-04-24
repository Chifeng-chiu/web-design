from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext

from database import SessionLocal, get_db, create_tables
from models import TradeRecord, User, TradeType, Post
import yfinance

app = FastAPI(title="Stock Trading API")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TradeCreate(BaseModel):
    user_id: int
    stock_symbol: str
    trade_type: str
    price: float
    quantity: int
    trade_date: Optional[datetime] = None

class TradeResponse(BaseModel):
    id: int
    user_id: int
    stock_symbol: str
    trade_type: str
    price: float
    quantity: int
    trade_date: datetime

    class Config:
        orm_mode = True

@app.on_event("startup")
def startup_event():
    create_tables()

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class RegisterResponse(BaseModel):
    id: int
    username: str
    email: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    user_id: int
    username: str

@app.post("/register/", response_model=RegisterResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(
            (User.username == request.username) | (User.email == request.email)
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already exists")

        hashed_password = pwd_context.hash(request.password)
        new_user = User(
            username=request.username,
            email=request.email,
            password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return RegisterResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login/", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == request.username).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if not pwd_context.verify(request.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        return LoginResponse(
            user_id=user.id,
            username=user.username
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trades/", response_model=TradeResponse)
def create_trade(trade: TradeCreate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == trade.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        trade_type_enum = TradeType.BUY if trade.trade_type.lower() == "buy" else TradeType.SELL

        db_trade = TradeRecord(
            user_id=trade.user_id,
            stock_symbol=trade.stock_symbol,
            trade_type=trade_type_enum,
            price=trade.price,
            quantity=trade.quantity,
            trade_date=trade.trade_date or datetime.utcnow()
        )
        db.add(db_trade)
        db.commit()
        db.refresh(db_trade)

        return TradeResponse(
            id=db_trade.id,
            user_id=db_trade.user_id,
            stock_symbol=db_trade.stock_symbol,
            trade_type=db_trade.trade_type.value,
            price=db_trade.price,
            quantity=db_trade.quantity,
            trade_date=db_trade.trade_date
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trades/{user_id}", response_model=List[TradeResponse])
def get_user_trades(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        trades = db.query(TradeRecord).filter(TradeRecord.user_id == user_id).all()

        return [
            TradeResponse(
                id=trade.id,
                user_id=trade.user_id,
                stock_symbol=trade.stock_symbol,
                trade_type=trade.trade_type.value,
                price=trade.price,
                quantity=trade.quantity,
                trade_date=trade.trade_date
            )
            for trade in trades
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PostCreate(BaseModel):
    user_id: int
    title: str
    content: str

class PostResponse(BaseModel):
    id: int
    user_id: int
    username: str
    title: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True

@app.post("/posts/", response_model=PostResponse)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == post.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db_post = Post(
            user_id=post.user_id,
            title=post.title,
            content=post.content
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)

        return PostResponse(
            id=db_post.id,
            user_id=db_post.user_id,
            username=user.username,
            title=db_post.title,
            content=db_post.content,
            created_at=db_post.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/posts/", response_model=List[PostResponse])
def get_all_posts(db: Session = Depends(get_db)):
    try:
        posts = db.query(Post).join(User, Post.user_id == User.id).order_by(Post.created_at.desc()).all()

        return [
            PostResponse(
                id=post.id,
                user_id=post.user_id,
                username=post.user.username,
                title=post.title,
                content=post.content,
                created_at=post.created_at
            )
            for post in posts
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class StockInfo(BaseModel):
    symbol: str
    name: str
    current_price: float
    high: float
    low: float

@app.get("/stock/{symbol}", response_model=StockInfo)
def get_stock_price(symbol: str):
    try:
        ticker = yfinance.Ticker(symbol)
        info = ticker.info

        current_price = info.get('currentPrice') or info.get('regularMarketPreviousClose')
        high = info.get('dayHigh') or info.get('regularMarketDayHigh')
        low = info.get('dayLow') or info.get('regularMarketDayLow')
        name = info.get('shortName') or info.get('longName') or symbol

        if current_price is None:
            raise HTTPException(status_code=404, detail=f"找不到股票代號: {symbol}")

        return StockInfo(
            symbol=symbol.upper(),
            name=name,
            current_price=float(current_price),
            high=float(high) if high else float(current_price),
            low=float(low) if low else float(current_price)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得股價失敗: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)