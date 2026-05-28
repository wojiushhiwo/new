# 跑刀避雷指南 - 部署说明

## 目录结构

```
/var/www/paodao-review-server/
├── app.py          # Flask 后端
├── static/         # 前端文件 (HTML/JS/CSS)
│   ├── index.html
│   ├── submit.html
│   ├── list.html
│   ├── js/app.js
│   └── css/style.css
├── *.json          # 数据文件 (studios.json, users.json 等)
├── deploy.sh       # 部署脚本
└── README.md       # 本文件
```

## 修改流程（标准方式）

### 第一步：切到 staging 分支改代码

```bash
cd /var/www/paodao-review-server
git checkout staging
# 修改文件...
```

### 第二步：提交改动

```bash
git add 改过的文件
git commit -m "改了啥"
```

### 第三步：部署上线

```bash
./deploy.sh staging
```

一行命令搞定 → 自动合并到 master → 自动重启服务

### 查看状态

```bash
./deploy.sh status
```

### 出问题了回滚

```bash
./deploy.sh rollback
```

## 直接在线改（不推荐，紧急修 bug 用）

```bash
git checkout master
# 改文件...
systemctl restart bileizhinan
```

## 数据文件说明

这些 JSON 是用户投稿数据，不要改：
- `studios.json` — 工作室数据
- `users.json` — 用户数据
- `comments.json` — 评论
- `settings.json` — 站点设置

## 日志

```bash
journalctl -u bileizhinan -f    # 实时看日志
cat /var/log/gunicorn-error.log  # 错误日志
```
