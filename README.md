# StockBoard - 股票交易論壇

> 一個結合股票查詢、交易紀錄與社群討論的全端專案，使用 FastAPI + SPA 架構打造。

---

## 1. 專案概覽

StockBoard 是一個股票交易論壇系統，提供以下核心功能：

- **用戶系統**：註冊 / 登入（bcrypt 密碼加密）
- **討論板**：發文、留言、看板分類（台股 / 美股 / 加密貨幣 / 投資新手）
- **股票查詢**：即時股價 + 歷史走勢圖（整合 yfinance API）
- **交易紀錄**：記錄買賣交易，追蹤投資歷史
- **個人檔案**：查看自己的文章、追蹤其他用戶

**架構模式**：後端 REST API (FastAPI) + 前端 SPA (純 HTML/CSS/JS)

---

## 2. 技術棧

| 層級 | 技術 | 用途 |
|------|------|------|
| **後端框架** | FastAPI | 高效能非同步 API 框架 |
| **ORM** | SQLAlchemy | 資料庫操作與 Model 定義 |
| **資料庫** | SQLite (開發) / PostgreSQL (部署) | 資料持久化 |
| **密碼加密** | bcrypt | 安全的密碼雜湊 |
| **外部 API** | yfinance | 股票即時報價與歷史數據 |
| **前端** | Vanilla JS (SPA) | 無框架單頁應用 |
| **圖表庫** | Chart.js | 股票走勢圖視覺化 |
| **伺服器** | Uvicorn (開發) / Render (部署) | ASGI 伺服器 |

---

## 3. 專案結構

```
網頁設計(股票BLOG)/
├── main.py          # FastAPI 主程式（路由、認證、業務邏輯）
├── models.py        # SQLAlchemy ORM 模型定義
├── database.py      # 資料庫連線配置（支援 SQLite / PostgreSQL 切換）
├── index.html       # 前端 SPA（包含 HTML + CSS + JS）
├── stock_forum.db   # SQLite 資料庫檔案（自動產生）
└── README.md        # 專案說明文件
```

### 各檔案職責

| 檔案 | 行數 | 核心職責 |
|------|------|----------|
| `main.py` | 413 | 所有 API 路由、認證邏輯、密碼工具、lifespan 管理 |
| `models.py` | 73 | 4 個 ORM Model（User, TradeRecord, Post, Comment）+ Enum |
| `database.py` | 34 | Engine / Session 配置、環境變數讀取、自動建表 |
| `index.html` | 830 | 完整前端（CSS 變數系統、SPA 路由、Auth、所有 UI 互動） |

---

## 4. 資料庫設計

### ER 圖

```
users (1) ────< (N) trade_records
   │
   ├───< (N) posts
   │             │
   │             └───< (N) comments
   │
   └───< (N) comments
```

### 資料表結構

#### `users` 表
| 欄位 | 型別 | 約束 | 說明 |
|------|------|------|------|
| `id` | Integer | PK, Index | 自動遞增 |
| `username` | String | UNIQUE, Index, NOT NULL | 使用者帳號 |
| `password` | String(500) | NOT NULL | bcrypt 雜湊密碼 |

#### `trade_records` 表
| 欄位 | 型別 | 約束 | 說明 |
|------|------|------|------|
| `id` | Integer | PK, Index | 自動遞增 |
| `user_id` | Integer | FK → users.id, NOT NULL | 所屬用戶 |
| `stock_symbol` | String | NOT NULL | 股票代號 |
| `trade_type` | Enum(buy/sell) | NOT NULL | 買入/賣出 |
| `price` | Float | NOT NULL | 成交價格 |
| `quantity` | Integer | NOT NULL | 成交股數 |
| `trade_date` | DateTime | NOT NULL | 交易時間（UTC） |

#### `posts` 表
| 欄位 | 型別 | 約束 | 說明 |
|------|------|------|------|
| `id` | Integer | PK, Index | 自動遞增 |
| `user_id` | Integer | FK → users.id, NOT NULL | 作者 |
| `title` | String | NOT NULL | 文章標題 |
| `content` | String | NOT NULL | 文章內容 |
| `created_at` | DateTime | NOT NULL | 發表時間（UTC） |

#### `comments` 表
| 欄位 | 型別 | 約束 | 說明 |
|------|------|------|------|
| `id` | Integer | PK, Index | 自動遞增 |
| `post_id` | Integer | FK → posts.id, NOT NULL | 所屬文章 |
| `user_id` | Integer | FK → users.id, NOT NULL | 留言者 |
| `content` | String | NOT NULL | 留言內容 |
| `created_at` | DateTime | NOT NULL | 留言時間（UTC） |

### 設計亮點

1. **多資料庫支援**：`database.py` 透過 `DATABASE_URL` 環境變數自動切換 SQLite / PostgreSQL
2. **PostgreSQL 協定修正**：自動將 `postgres://` 轉為 `postgresql://`（Render 部署必備）
3. **SQLite 執行緒安全**：`check_same_thread=False` 解決 FastAPI 多執行緒存取問題
4. **UTC 時間統一**：自訂 `utcnow()` 函式取代已棄用的 `datetime.utcnow()`

---

## 5. 後端 API 學習筆記

### 5.1 FastAPI 基礎架構

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()  # 啟動時自動建表
    yield

app = FastAPI(title="Stock Trading API", lifespan=lifespan)
```

**學習重點**：
- `lifespan` 是 FastAPI 0.99+ 推薦的啟動/關閉生命週期管理方式
- 取代舊版的 `@app.on_event("startup")`（已棄用）
- 使用 `asynccontextmanager` 優雅處理資源初始化與清理

### 5.2 CORS 中介軟體

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # 允許所有來源（開發用）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**學習重點**：
- 前端 SPA 與後端 API 通常在不同域名，需要 CORS 設定
- 生產環境應將 `allow_origins` 改為具體域名列表
- `allow_credentials=True` 允許攜帶 Cookie

### 5.3 路由總覽

| 方法 | 路徑 | 功能 | 認證 |
|------|------|------|------|
| POST | `/register/` | 用戶註冊 | 否 |
| POST | `/login/` | 用戶登入 | 否 |
| POST | `/trades/` | 新增交易 | 否（傳 user_id） |
| GET | `/trades/{user_id}` | 查詢用戶交易 | 否（傳 user_id） |
| POST | `/posts/` | 發表文章 | 否（傳 user_id） |
| GET | `/posts/` | 取得所有文章 | 否 |
| POST | `/comments/` | 發表留言 | 否（傳 user_id） |
| GET | `/stock/{symbol}` | 即時股價 | 否 |
| GET | `/stock/{symbol}/history` | 歷史走勢 | 否 |

### 5.4 Pydantic 資料驗證

```python
class TradeCreate(BaseModel):
    user_id: int
    stock_symbol: str
    trade_type: str
    price: float
    quantity: int
    trade_date: Optional[datetime] = None
```

**學習重點**：
- Pydantic 自動進行型別驗證與轉換
- `response_model` 自動過濾回應欄位（不會洩露密碼等敏感資料）
- `orm_mode = True` 允許直接從 SQLAlchemy 物件轉換

### 5.5 依賴注入（Depends）

```python
def get_user_trades(user_id: int, db: Session = Depends(get_db)):
```

**學習重點**：
- `Depends(get_db)` 是 FastAPI 的依賴注入系統
- 每個請求自動取得獨立的 DB Session
- `get_db` 使用 `yield` 確保 Session 最終會被 `close()`

### 5.6 密碼加密（bcrypt）

```python
def _trim_password(password: str) -> bytes:
    """bcrypt 限制 72 bytes，超過需截斷"""
    encoded = password.encode("utf-8")
    if len(encoded) <= 72:
        return encoded
    # 字元層級截斷，避免切斷 UTF-8 多字節字元
    ...
```

**學習重點**：
- bcrypt 有 72 bytes 長度限制，需妥善處理
- UTF-8 中文字可能佔 3 bytes，不能直接切片
- 使用 `_trim_password` 確保多字節字元不被截斷

### 5.7 錯誤處理模式

```python
try:
    # 業務邏輯
    db.commit()
    return response
except HTTPException:
    raise                          # 已處理的 HTTP 錯誤直接重拋
except Exception as e:
    db.rollback()                  # 其他錯誤回滾資料庫
    raise HTTPException(status_code=500, detail=str(e))
```

**學習重點**：
- 區分 `HTTPException` 與一般 `Exception`
- 錯誤時必須 `db.rollback()` 避免 Session 鎖定
- 使用 try/except 包裝每個路由確保穩定性

### 5.8 yfinance 整合

```python
@app.get("/stock/{symbol}", response_model=StockInfo)
def get_stock_price(symbol: str):
    ticker = yfinance.Ticker(symbol)
    info = ticker.info
    current_price = info.get("currentPrice") or info.get("regularMarketPreviousClose")
```

**學習重點**：
- `yfinance.Ticker(symbol).info` 取得即時報價
- 使用 `or` 鏈接多個 fallback 欄位提高成功率
- 台股代號需加 `.TW` 後綴（如 `2330.TW`）

---

## 6. 前端 SPA 學習筆記

### 6.1 SPA 架構設計

整個前端在單一 `index.html` 中實現，包含：
- **CSS 變數系統**（`:root` 定義主題色）
- **頁面路由**（`.page` class 切換顯示）
- **狀態管理**（`localStorage` 保存登入狀態）

### 6.2 CSS 變數與主題系統

```css
:root {
  --brand: #1a73e8;        /* 品牌主色 */
  --brand-light: #e8f0fe;  /* 品牌淺色 */
  --green: #1b9e4b;        /* 漲/買入 */
  --red: #e53935;          /* 跌/賣出 */
  --sidebar-w: 240px;      /* 側欄寬度 */
}
```

**學習重點**：
- CSS 變數易於維護主題色
- 集中管理尺寸常量（`--sidebar-w`, `--topbar-h`）
- 修改一個變數即可全局生效

### 6.3 頁面路由機制

```javascript
function showPage(id) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const el = document.getElementById('page-' + id);
  if (el) el.classList.add('active');
}
```

**學習重點**：
- 透過 `.active` class 控制頁面顯示/隱藏
- 側欄 `data-page` 屬性與頁面 ID 對應
- 無框架實現簡單的 SPA 路由

### 6.4 認證流程

```
使用者開啟頁面
    ↓
checkAuth() 檢查 localStorage
    ↓
有 user_id → 隱藏 auth overlay，載入資料
無 user_id → 顯示登入/註冊表單
    ↓
登入成功 → 儲存 user_id + username 到 localStorage
```

**學習重點**：
- 使用 `localStorage` 維持登入狀態（無 JWT）
- 每次頁面載入自動檢查認證狀態
- 簡化版認證（適合學習專案）

### 6.5 伺服喚醒機制（Render 冷啟動）

```javascript
async function fetchWT(url, opts={}, ms=90000) {
  const c = new AbortController();
  const t = setTimeout(() => c.abort(), ms);
  try {
    return await fetch(url, {...opts, signal: c.signal});
  } catch(e) {
    throw new Error(e.name === 'AbortError' ? '伺服器逾時' : '無法連線');
  } finally {
    clearTimeout(t);
  }
}

// 4 秒後顯示 "伺服器喚醒中" 提示
function startWake() {
  wakeTimer = setTimeout(showWake, 4000);
}
```

**學習重點**：
- Render 免費方案有冷啟動問題（約 30-60 秒）
- `AbortController` 設定超時限制
- 視覺化 feedback 提升使用者體驗

### 6.6 看板過濾功能

```javascript
function filterPosts() {
  if (currentBoard === 'all') { renderPosts(allPosts, 'postsList'); return; }
  const filtered = allPosts.filter(p =>
    p.title.includes(currentBoard) || p.content.includes(currentBoard)
  );
  renderPosts(filtered.length ? filtered : [], 'postsList');
}
```

**學習重點**：
- 前端過濾（無需額外 API）
- 關鍵字匹配標題與內容
- 即時切換無需重新請求

### 6.7 Chart.js 走勢圖

```javascript
stockChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: data.map(d => d.date),
    datasets: [{
      label: '收盤價',
      data: data.map(d => d.close),
      borderColor: '#1a73e8',
      fill: true,
      tension: .3
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false
  }
});
```

**學習重點**：
- 每次切換期間先 `stockChart.destroy()` 避免圖表疊加
- `tension: .3` 產生平滑曲線
- `fill: true` 加上半透明底色

### 6.8 XSS 防護

```javascript
function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
```

**學習重點**：
- 所有動態插入 DOM 的內容都經過 `esc()` 編碼
- 防止 `<script>` 注入攻擊
- 前端基本的輸入 sanitation

---

## 7. 核心技術亮點

### 7.1 多資料庫無縫切換

```python
# database.py
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./stock_forum.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)
```

開發時用 SQLite（零配置），部署時自動切換 PostgreSQL。

### 7.2 ORM Relationship 設計

```python
# models.py
User.trade_records = relationship("TradeRecord", back_populates="user")
User.posts = relationship("Post", back_populates="user")
Post.comments = relationship("Comment", back_populates="post", order_by="Comment.created_at")
```

- `back_populates` 建立雙向關聯
- `order_by` 讓留言自動按時間排序
- 查詢文章時可一次載入所有留言

### 7.3 Enum 型別欄位

```python
class TradeType(enum.Enum):
    BUY = "buy"
    SELL = "sell"

trade_type = Column(Enum(TradeType), nullable=False)
```

使用 Enum 而非 String 確保資料一致性。

### 7.4 UTC 時間處理

```python
def utcnow():
    """取代棄用的 datetime.utcnow()，使用 timezone-aware 的 UTC 時間"""
    return datetime.now(timezone.utc).replace(tzinfo=None)
```

- `datetime.utcnow()` 在 Python 3.12+ 已棄用
- 改用 `datetime.now(timezone.utc)` 再轉為 naive datetime（與 SQLite 相容）

### 7.5 前端狀態管理

| 狀態 | 儲存方式 | 說明 |
|------|----------|------|
| `user_id` | localStorage | 當前登入用戶 ID |
| `username` | localStorage | 當前用戶名稱 |
| `bio` | localStorage | 自我介紹（純前端） |
| `displayName` | localStorage | 顯示名稱（純前端） |
| `following` | localStorage | 追蹤列表（JSON 陣列） |
| `allPosts` | JS 變數 | 所有文章（記憶體快取） |

---

## 8. 部署實戰

### 8.1 部署到 Render

#### 步驟 1：準備 `requirements.txt`

```
fastapi==0.115.0
uvicorn==0.30.6
sqlalchemy==2.0.35
pydantic==2.9.2
bcrypt==4.2.0
yfinance==0.2.43
```

#### 步驟 2：準備 `render.yaml`

```yaml
services:
  - type: web
    name: stockboard
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: stockboard-db
          property: connectionString
```

#### 步驟 3：Push 到 GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git push origin main
```

#### 步驟 4：在 Render 建立 Web Service

1. 連結 GitHub 倉庫
2. 設定 Python 環境
3. 新增 PostgreSQL 資料庫
4. 部署

### 8.2 本地開發

```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動伺服器
python main.py
# 或
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 打開瀏覽器
http://localhost:8000/docs    # Swagger UI（API 文件）
```

### 8.3 前端 API 位址設定

在 `index.html` 中修改：

```javascript
const API = 'https://your-app.onrender.com';  // 改為你的 Render URL
```

### 8.4 環境變數設定

| 變數 | 開發環境 | 生產環境 |
|------|----------|----------|
| `DATABASE_URL` | 不設（預設 SQLite） | `postgresql://...`（Render 自動注入） |

---

## 9. 安全學習

### 9.1 已實施的安全措施

| 項目 | 實作方式 | 位置 |
|------|----------|------|
| **密碼加密** | bcrypt + 72 bytes 截斷處理 | `main.py:16-35` |
| **XSS 防護** | `esc()` 函式轉義所有輸出 | `index.html:444-447` |
| **SQL 注入防護** | SQLAlchemy ORM（參數化查詢） | `models.py` |
| **錯誤隔離** | HTTPException 區分處理 | `main.py` 每個路由 |
| **資料庫回滾** | 異常時 `db.rollback()` | `main.py` 每個路由 |

### 9.2 待加強的安全措施

#### JWT Token 認證

目前使用 `user_id` 直接傳遞，任何知道 user_id 的人都可以模擬該用戶。

**改進方案**：
```python
from jose import JWTError, jwt
from datetime import timedelta

SECRET_KEY = "your-secret-key"  # 應從環境變數讀取
ALGORITHM = "HS256"

def create_token(user_id: int):
    expire = datetime.utcnow() + timedelta(days=7)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, ALGORITHM)
```

#### CORS 限制

```python
# 不應該在生產環境使用 "*"
allow_origins=["https://yourdomain.com"]
```

#### 輸入驗證

- 文章標題/內容長度限制
- 股票代號格式驗證
- 價格/數量範圍檢查

#### Rate Limiting

防止暴力登入與 API 濫用：
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/login/")
@limiter.limit("5/minute")
def login(request: Request, ...):
```

---

## 10. FAQ 與除錯

### Q1: 伺服器啟動很慢怎麼辦？

**原因**：Render 免費方案有冷啟動機制，閒置 15 分鐘後會休眠。

**解法**：
- 等待 30-60 秒自動喚醒
- 前端已實作 `fetchWT` 逾時機制與 "伺服器喚醒中" 提示
- 升級到 Render 付費方案可避免冷啟動

### Q2: 股票查不到價格？

**可能原因**：
1. 台股代號需加 `.TW`（如 `2330.TW`）
2. 台股盤後時段可能無法取得即時價格
3. yfinance 有請求頻率限制

**除錯**：
```python
# 在 main.py 中查看原始資料
ticker = yfinance.Ticker("2330.TW")
print(ticker.info)  # 檢查有哪些欄位
```

### Q3: CORS 錯誤？

**錯誤訊息**：`Access to fetch at '...' has been blocked by CORS policy`

**解法**：確認 `main.py` 中的 CORS 設定：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 確保前端域名在列表中
    ...
)
```

### Q4: 資料庫鎖定（database is locked）？

**原因**：SQLite 不支援高併發寫入。

**解法**：
- 開發環境：確認 `check_same_thread=False` 已設定
- 生產環境：升級到 PostgreSQL

### Q5: `datetime.utcnow()` 警告？

Python 3.12+ 會顯示 `DeprecationWarning`。

**解法**：專案已使用自訂 `utcnow()` 函式：
```python
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)
```

### Q6: 前端看不到最新文章？

**原因**：前端快取了 `allPosts` 但未重新請求。

**解法**：發布文章後已呼叫 `loadPosts()` 重新載入，確保資料同步。

### Q7: bcrypt 安裝失敗？

**Windows 常見錯誤**：缺少 Visual C++ Build Tools

**解法**：
```bash
# 方法 1：安裝預編譯版本
pip install bcrypt --only-binary=all

# 方法 2：安裝 Visual C++ Build Tools
# https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

### Q8: yfinance 傳回 None？

**原因**：某些股票代號在 yfinance 中沒有對應資料。

**解法**：
```python
# 使用 fallback 欄位
current_price = info.get("currentPrice") or info.get("regularMarketPreviousClose")
high = info.get("dayHigh") or info.get("regularMarketDayHigh")
```

---

## 11. 學習路徑建議

### 初學者路線

```
1. HTML/CSS 基礎
   └── 閱讀 index.html 的 CSS 部分，理解 CSS 變數與 Flexbox
   
2. JavaScript 基礎
   └── 理解 fetch API、async/await、DOM 操作
   
3. Python 基礎
   └── 理解函式、class、import、型別提示
   
4. FastAPI 入門
   └── 閱讀 main.py 的路由定義，理解 @app.get / @app.post
   
5. SQLAlchemy 入門
   └── 閱讀 models.py，理解 Column、ForeignKey、relationship
```

### 進階學習項目

| 主題 | 實作建議 |
|------|----------|
| **JWT 認證** | 加入登入 token，取代目前的 user_id 傳遞 |
| **分頁** | 文章列表加入分頁功能（limit/offset） |
| **搜尋** | 文章標題/內容全文搜尋 |
| **圖片上傳** | 用戶大頭貼上傳功能 |
| **即時通知** | WebSocket 推送新留言通知 |
| **Docker 化** | 撰寫 Dockerfile 與 docker-compose |
| **單元測試** | 使用 pytest 測試 API 路由 |
| **前端框架** | 將 SPA 改寫為 Vue.js / React |

### 推薦學習資源

- **FastAPI 官方文件**：https://fastapi.tiangolo.com/
- **SQLAlchemy 教程**：https://docs.sqlalchemy.org/
- **Chart.js 文件**：https://www.chartjs.org/docs/
- **yfinance GitHub**：https://github.com/ranaroussi/yfinance

---

## 12. 專有名詞表

| 術語 | 英文 | 說明 |
|------|------|------|
| **SPA** | Single Page Application | 單頁應用，所有互動在同一頁面完成 |
| **REST API** | Representational State Transfer | 無狀態的 HTTP API 架構風格 |
| **ORM** | Object-Relational Mapping | 將資料庫表格對應到物件的技術 |
| **CORS** | Cross-Origin Resource Sharing | 跨來源資源共享機制 |
| **bcrypt** | - | 基於 Blowfish 的密碼雜湊函式 |
| **Pydantic** | - | Python 資料驗證與設定管理庫 |
| **Uvicorn** | - | 基於 uvloop 的 ASGI 伺服器 |
| **lifespan** | - | FastAPI 應用程式生命週期管理 |
| **Dependency Injection** | 依賴注入 | FastAPI 的 `Depends()` 機制 |
| **yfinance** | Yahoo Finance API | 免費股票數據來源 |
| **冷啟動** | Cold Start | 伺服器閒置後首次請求的延遲 |
| **XSS** | Cross-Site Scripting | 跨站腳本攻擊 |
| **Enum** | Enumeration | 列舉型別，限制欄位為固定值之一 |
| **Foreign Key** | 外鍵 | 關聯另一表格主鍵的欄位 |
| **Session** | 資料庫會話 | SQLAlchemy 中操作資料庫的物件 |
| **Middleware** | 中介軟體 | 攔截請求/回應的處理層 |
| **Render** | - | 雲端託管平台（類似 Heroku） |
| **ASGI** | Asynchronous Server Gateway Interface | Python 非同步伺服器介面標準 |
| **Fallback** | 後備方案 | 當主要方法失敗時的替代方案 |
| **Sanitation** | 輸入淨化 | 過濾使用者輸入以防止攻擊 |

---

## 快速開始

```bash
# 1. 安裝依賴
pip install fastapi uvicorn sqlalchemy pydantic bcrypt yfinance

# 2. 啟動後端
python main.py

# 3. 打開瀏覽器訪問 API 文件
http://localhost:8000/docs

# 4. 直接開啟 index.html 使用前端
# 或將 index.html 中的 API URL 改為 http://localhost:8000
```

---

**專案版本**：1.0.0  
**授權**：僅供學習使用  
**最後更新**：2026-05-08
