from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
# 修正 1：正確 import Session
from sqlalchemy.orm import Session
from database import SessionLocal, get_db, create_tables
from models import TradeRecord, User, TradeType, Post, Comment
import yfinance

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False   # 關閉 passlib 的 72 bytes 長度檢查
)

# 修正 2：改用 lifespan 取代棄用的 @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app = FastAPI(title="Stock Trading API", lifespan=lifespan)

# 修正 10：CORS 正式上線時請把 "*" 換成你的前端網域
# 例如：allow_origins=["https://your-site.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── 密碼工具 ─────────────────────────────────────────────────────────────────

def safe_encode_password(password: str) -> str:
    """
    修正 9：修正密碼截斷 bug。
    bcrypt 限制 72 bytes，但直接切 bytes 可能截斷多位元組字元（中文）導致
    register 和 login 截出不同字串。改用字元層級截斷再編碼，確保兩端一致。
    """
    encoded = password.encode("utf-8")
    if len(encoded) <= 72:
        return password
    # 逐字累加直到超過 72 bytes，取最後一個不超過的位置
    total = 0
    for i, ch in enumerate(password):
        char_len = len(ch.encode("utf-8"))
        if total + char_len > 72:
            return password[:i]
        total += char_len
    return password


# ─── Auth Models ──────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str

class RegisterResponse(BaseModel):
    id: int
    username: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    user_id: int
    username: str


# ─── Auth Routes ──────────────────────────────────────────────────────────────

@app.post("/register/", response_model=RegisterResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.username == request.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        safe_password = safe_encode_password(request.password)
        hashed_password = pwd_context.hash(safe_password)

        new_user = User(username=request.username, password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return RegisterResponse(id=new_user.id, username=new_user.username)

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

        safe_password = safe_encode_password(request.password)
        if not pwd_context.verify(safe_password, user.password):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        return LoginResponse(user_id=user.id, username=user.username)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Trade Models ─────────────────────────────────────────────────────────────

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


# ─── Trade Routes ─────────────────────────────────────────────────────────────

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
                id=t.id,
                user_id=t.user_id,
                stock_symbol=t.stock_symbol,
                trade_type=t.trade_type.value,
                price=t.price,
                quantity=t.quantity,
                trade_date=t.trade_date
            )
            for t in trades
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Post Models ──────────────────────────────────────────────────────────────

class PostCreate(BaseModel):
    user_id: int
    title: str
    content: str

class CommentResponse(BaseModel):
    id: int
    user_id: int
    username: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True

class PostResponse(BaseModel):
    id: int
    user_id: int
    username: str
    title: str
    content: str
    created_at: datetime
    comments: List[CommentResponse] = []

    class Config:
        orm_mode = True

class CommentCreate(BaseModel):
    user_id: int
    post_id: int
    content: str


# ─── Post Routes ──────────────────────────────────────────────────────────────

@app.post("/posts/", response_model=PostResponse)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == post.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db_post = Post(user_id=post.user_id, title=post.title, content=post.content)
        db.add(db_post)
        db.commit()
        db.refresh(db_post)

        return PostResponse(
            id=db_post.id,
            user_id=db_post.user_id,
            username=user.username,
            title=db_post.title,
            content=db_post.content,
            created_at=db_post.created_at,
            comments=[]
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
        result = []
        for post in posts:
            comments = [
                CommentResponse(
                    id=c.id,
                    user_id=c.user_id,
                    username=c.user.username,
                    content=c.content,
                    created_at=c.created_at
                )
                for c in post.comments
            ]
            result.append(PostResponse(
                id=post.id,
                user_id=post.user_id,
                username=post.user.username,
                title=post.title,
                content=post.content,
                created_at=post.created_at,
                comments=comments
            ))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 新增：留言功能
@app.post("/comments/", response_model=CommentResponse)
def create_comment(comment: CommentCreate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == comment.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        post = db.query(Post).filter(Post.id == comment.post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        db_comment = Comment(
            post_id=comment.post_id,
            user_id=comment.user_id,
            content=comment.content
        )
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)

        return CommentResponse(
            id=db_comment.id,
            user_id=db_comment.user_id,
            username=user.username,
            content=db_comment.content,
            created_at=db_comment.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ─── Stock Routes ─────────────────────────────────────────────────────────────

class StockInfo(BaseModel):
    symbol: str
    name: str
    current_price: float
    high: float
    low: float

class StockHistory(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


@app.get("/stock/{symbol}", response_model=StockInfo)
def get_stock_price(symbol: str):
    try:
        ticker = yfinance.Ticker(symbol)
        info = ticker.info

        current_price = info.get("currentPrice") or info.get("regularMarketPreviousClose")
        high = info.get("dayHigh") or info.get("regularMarketDayHigh")
        low = info.get("dayLow") or info.get("regularMarketDayLow")
        name = info.get("shortName") or info.get("longName") or symbol

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


# 新增：股票歷史走勢
@app.get("/stock/{symbol}/history", response_model=List[StockHistory])
def get_stock_history(symbol: str, period: str = "1mo"):
    """
    取得股票歷史走勢資料
    period 可傳入：1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y
    """
    try:
        ticker = yfinance.Ticker(symbol)
        hist = ticker.history(period=period)

        if hist.empty:
            raise HTTPException(status_code=404, detail=f"找不到股票代號: {symbol}")

        result = []
        for date, row in hist.iterrows():
            result.append(StockHistory(
                date=date.strftime("%Y-%m-%d"),
                open=round(float(row["Open"]), 2),
                high=round(float(row["High"]), 2),
                low=round(float(row["Low"]), 2),
                close=round(float(row["Close"]), 2),
                volume=int(row["Volume"])
            ))
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得走勢失敗: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
