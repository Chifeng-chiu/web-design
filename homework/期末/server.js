// ============================================================
//  作業 03 — Node.js Hello World（Web Server 版）
//  使用 Node.js 內建的 http 模組建立最基礎的網頁伺服器
// ============================================================

// ── 載入 http 模組 ──
// require 是 Node.js 用來載入「模組（module）」的方法
// 'http' 是 Node.js 內建的模組，不需要另外安裝
// 它提供建立 HTTP 伺服器與處理 HTTP 請求/回應的所有功能
const http = require('http');

// ── 設定伺服器參數 ──
// 主機名稱：'127.0.0.1' 也就是 localhost，只允許本機連線
// 也可以改成 '0.0.0.0' 讓區域網路內的其他裝置也能連線
const HOSTNAME = '127.0.0.1';

// 埠號（port）：3000 是開發時常用的埠號
// 可以改成 8080、5000 等，只要不與其他程式衝突即可
// 注意：埠號小於 1024 需要管理者權限，所以開發時通常用 3000 以上
const PORT = 3000;

// ── 建立伺服器 ──
// http.createServer() 會建立一個 HTTP 伺服器實例
// 它接收一個「回呼函式（callback function）」作為參數
// 這個回呼函式會在「每次收到 HTTP 請求」時被執行
const server = http.createServer((req, res) => {
  // -------------------------------------------------------
  //  req  = request（請求）  — 代表使用者送過來的請求
  //        例如：req.url 是使用者請求的網址路徑（如 '/' 或 '/about'）
  //              req.method 是 HTTP 方法（如 'GET'、'POST'）
  //
  //  res  = response（回應） — 代表我們要回傳給使用者的回應
  //        透過 res 的各種方法，我們可以控制要回傳什麼內容
  // -------------------------------------------------------

  // ---- 設定 HTTP 狀態碼與回應標頭 ----
  // writeHead() 的第一個參數是 HTTP 狀態碼
  // 200 代表「OK」（請求成功）
  // 第二個參數是回應標頭（response header）
  // 'Content-Type' 告訴瀏覽器回應內容是 HTML，編碼為 UTF-8
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });

  // ---- 寫入回應內容並結束回應 ----
  // res.end() 會將內容送回給使用者，並結束這次的回應
  // 一旦呼叫 res.end()，就不能再寫入更多資料
  // 這裡使用模板字串（backtick）來撰寫 HTML
  res.end(`
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
      <meta charset="UTF-8">
      <title>Node.js Hello World</title>
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
          font-family: 'Segoe UI', system-ui, sans-serif;
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
          color: #fff;
          text-align: center;
        }
        .container { padding: 2rem; }
        h1 { font-size: 3rem; margin-bottom: .5rem; }
        p { font-size: 1.1rem; color: #a5b4fc; }
        .badge {
          display: inline-block;
          margin-top: 1.5rem;
          padding: .35rem 1.2rem;
          border-radius: 999px;
          background: rgba(99,102,241,.2);
          border: 1px solid rgba(99,102,241,.4);
          font-size: .85rem;
          color: #a5b4fc;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Hello World! 🚀</h1>
        <p>這是我的第一個 Node.js 網頁伺服器</p>
        <div class="badge">Node.js · http 模組</div>
      </div>
    </body>
    </html>
  `);
});

// ── 啟動伺服器 ──
// server.listen() 讓伺服器開始監聽指定的主機與埠號
// 語法：server.listen(port, hostname, callback)
// 第三個參數是啟動成功後會執行的回呼函式（選擇性的）
server.listen(PORT, HOSTNAME, () => {
  // 當伺服器成功啟動時，在終端機印出訊息
  // template literal 使用反引號（`）與 ${} 來嵌入變數
  console.log(`✅ 伺服器已啟動！`);
  console.log(`   請在瀏覽器開啟 → http://${HOSTNAME}:${PORT}`);
  console.log(`   按 Ctrl + C 可停止伺服器`);
});
