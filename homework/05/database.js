const bcrypt = require('bcryptjs');

// 直接用 JavaScript 陣列當作記憶體資料庫
let users = [];
let posts = [];
let userIdCounter = 1;
let postIdCounter = 1;

async function initDatabase() {
  console.log('[Database] 初始化 Vercel 相容模式 (Array Mock)...');
  
  // 建立一個預設帳號 admin / 密碼 123456
  const hashedPassword = await bcrypt.hash('123456', 10);
  users = [{
    id: userIdCounter++,
    username: 'admin',
    email: 'admin@test.com',
    password: hashedPassword,
    created_at: new Date().toISOString()
  }];

  // 建立一篇預設文章
  posts = [{
    id: postIdCounter++,
    title: '歡迎來到我的部落格',
    content: '這是一個為了 Vercel 環境特製的陣列資料庫！完全避開了 SQLite 的非同步與唯讀問題。現在網頁應該能光速載入，發文功能也能正常使用了喔！',
    author: '系統管理員',
    user_id: 1,
    category: '生活',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }];

  console.log('[Database] 初始化完成');
  return true;
}

function getAllPosts() {
  // 回傳所有文章，並依照時間由新到舊排序
  return [...posts].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
}

function getPostById(id) {
  // 注意：從網址傳來的 id 可能是字串，所以要用 Number() 轉型
  return posts.find(p => p.id === Number(id)) || null;
}

function createPost(title, content, author, userId = null, category = '生活') {
  const now = new Date().toISOString();
  const newPost = {
    id: postIdCounter++,
    title,
    content,
    author: author || 'Anonymous',
    user_id: userId ? Number(userId) : null,
    category,
    created_at: now,
    updated_at: now
  };
  posts.push(newPost);
  return newPost.id;
}

function updatePost(id, title, content, author) {
  const post = posts.find(p => p.id === Number(id));
  if (post) {
    post.title = title;
    post.content = content;
    post.author = author;
    post.updated_at = new Date().toISOString();
  }
}

function deletePost(id) {
  posts = posts.filter(p => p.id !== Number(id));
}

async function createUser(username, email, password) {
  // 檢查帳號或信箱是否重複
  if (users.some(u => u.username === username)) throw new Error('Username already exists');
  if (users.some(u => u.email === email)) throw new Error('Email already exists');
  
  const hashedPassword = await bcrypt.hash(password, 10);
  const now = new Date().toISOString();
  const newUser = {
    id: userIdCounter++,
    username,
    email,
    password: hashedPassword,
    created_at: now
  };
  
  users.push(newUser);
  return { id: newUser.id, username, email };
}

async function verifyUser(username, password) {
  const user = users.find(u => u.username === username || u.email === username);
  if (user) {
    const isValid = await bcrypt.compare(password, user.password);
    if (isValid) {
      return { id: user.id, username: user.username, email: user.email };
    }
  }
  return null;
}

function getUserById(id) {
  const user = users.find(u => u.id === Number(id));
  if (user) {
    return { id: user.id, username: user.username, email: user.email, created_at: user.created_at };
  }
  return null;
}

function getUserByUsername(username) {
  const user = users.find(u => u.username === username);
  if (user) {
    return { id: user.id, username: user.username, email: user.email, created_at: user.created_at };
  }
  return null;
}

function getUserPosts(userId) {
  return posts.filter(p => p.user_id === Number(userId))
              .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
}

function getPostsByCategory(category) {
  return posts.filter(p => p.category === category)
              .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
}

function searchPosts(keyword) {
  const lowerKeyword = keyword.toLowerCase();
  return posts.filter(p => 
                p.title.toLowerCase().includes(lowerKeyword) || 
                p.content.toLowerCase().includes(lowerKeyword)
              ).sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
}

module.exports = {
  initDatabase,
  getAllPosts,
  getPostById,
  createPost,
  updatePost,
  deletePost,
  createUser,
  verifyUser,
  getUserById,
  getUserByUsername,
  getUserPosts,
  getPostsByCategory,
  searchPosts
};