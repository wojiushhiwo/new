#!/usr/bin/env python3
"""跑刀避雷指南 - Flask Backend"""
import os, json, hashlib, secrets, re, time, random
from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory, jsonify
from functools import wraps

app = Flask(__name__)
app.secret_key = "paodao-review-secret-2026-bileizhinan"

# ===== Admin Domain Redirect =====
@app.before_request
def check_admin_domain():
    if request.host and request.host.startswith("admin."):
        if request.path in ["/", "/index.html"]:
            return redirect("/admin.html")

# ===== Config =====
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(DATA_DIR, "static")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
STUDIOS_FILE = os.path.join(DATA_DIR, "studios.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
FAVORITES_FILE = os.path.join(DATA_DIR, "favorites.json")
COMMENTS_FILE = os.path.join(DATA_DIR, "comments.json")

# ===== User Management =====
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            return json.load(f)
    return {}

def save_user(username, password, role="user", permissions=None):
    users = load_users()
    salt = secrets.token_hex(8)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    user_data = {"hash": pwd_hash, "salt": salt, "role": role}
    if permissions:
        user_data["permissions"] = permissions
    users[username] = user_data
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def check_user(username, password):
    users = load_users()
    if username not in users:
        return False
    u = users[username]
    pwd_hash = hashlib.sha256((password + u["salt"]).encode()).hexdigest()
    return pwd_hash == u["hash"]

# ===== Data Management =====
def load_studios():
    if os.path.exists(STUDIOS_FILE):
        with open(STUDIOS_FILE) as f:
            return json.load(f)
    return []

def save_studios(data):
    with open(STUDIOS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== Settings =====
SETTINGS_DEFAULTS = {
    "site_name": "跑刀避雷指南",
    "site_description": "三角洲行动跑刀工作室真实测评、接单防坑、黑名单查询",
    "logo_emoji": "🔪",
    "primary_color": "#4a6cf7",
    "secondary_color": "#ffd700",
    "footer_text": "纯绿玩家自建测评站",
    "footer_note": "数据来源于玩家投稿，仅供参考。接单前请自行判断。",
    "hero_title": "三角洲跑刀工作室",
    "hero_highlight": "红黑榜",
    "hero_subtitle": "纯绿玩家视角 · 真实测评 · 接单防坑",
    "search_placeholder": "搜工作室名字，比如：武汉禄昌商贸",
    "nav_home": "首页",
    "nav_blacklist": "黑名单",
    "nav_submit": "曝光投稿",
    "nav_login": "登录",
    "nav_logout": "退出",
    "stat_total": "收录工作室",
    "stat_black": "黑名单",
    "stat_white": "白名单",
    "stat_reports": "已收录",
    "section_recent": "最近收录",
    "section_platform": "按平台查看",
    "section_howto": "怎么用这个站",
    "no_results": "还没收录",
    "no_results_action": "点这里曝光",
    "search_tip": "搜不到？点这里曝光，帮兄弟避雷",
    "footer_disclaimer": "数据来源于玩家投稿，仅供参考。接单前请自行判断。"
}

def load_settings():
    defaults = dict(SETTINGS_DEFAULTS)
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                stored = json.load(f)
                defaults.update(stored)
        except:
            pass
    return defaults

def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== Favorites =====
def load_favorites():
    if os.path.exists(FAVORITES_FILE):
        try:
            with open(FAVORITES_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}

def save_favorites(data):
    with open(FAVORITES_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== Comments =====
def load_comments():
    if os.path.exists(COMMENTS_FILE):
        try:
            with open(COMMENTS_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}

def save_comments(data):
    with open(COMMENTS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== Auth Decorators =====
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

def get_user(username):
    users = load_users()
    return users.get(username, None)

def has_permission(username, perm=None):
    """检查用户是否有指定权限。perm=None 则检查是否能进后台"""
    user = get_user(username)
    if not user:
        return False
    role = user.get("role", None)
    # 兼容旧用户（没有 role 字段的 admin 默认 super_admin）
    if role is None:
        if username == "admin":
            return True
        return False
    if role == "super_admin":
        return True
    if perm is None:
        return role == "admin" or (user.get("permissions", []) and len(user.get("permissions", [])) > 0)
    if role == "admin":
        perms = user.get("permissions", [])
        return perm in perms
    return False

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return {"error": "未登录"}, 401
        if not has_permission(session.get("user")):
            return {"error": "权限不足"}, 403
        return f(*args, **kwargs)
    return decorated

def super_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return {"error": "未登录"}, 401
        user = get_user(session.get("user"))
        if not user or user.get("role") != "super_admin":
            return {"error": "需要超级管理员权限"}, 403
        return f(*args, **kwargs)
    return decorated

def require_perm(perm):
    """需要特定权限的装饰器工厂"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user" not in session:
                return {"error": "未登录"}, 401
            if not has_permission(session.get("user"), perm):
                return {"error": "权限不足"}, 403
            return f(*args, **kwargs)
        return decorated
    return decorator

# ===== Redblack Access Control =====
def has_redblack_access(username):
    """检查用户是否有红黑榜访问权限"""
    user = get_user(username)
    if not user:
        return False
    role = user.get("role", "")
    if role == "super_admin":
        return True
    if role == "admin":
        perms = user.get("permissions", [])
        if "redblack" in perms:
            return True
    return False

def redblack_required(f):
    """红黑榜访问装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login_page"))
        if not has_redblack_access(session.get("user")):
            return render_template_string("""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head><meta charset="UTF-8"><title>无权限 · 跑刀避雷指南</title>
            <meta name="robots" content="noindex, nofollow">
            <style>
              body { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
                background: #0d0e1a; color: #e0e0e0; display: flex; align-items: center; justify-content: center;
                min-height: 100vh; text-align: center; padding: 20px; }
              .card { max-width: 400px; padding: 40px; background: #191c2c; border-radius: 12px;
                border: 1px solid #252840; }
              h1 { font-size: 2rem; margin-bottom: 10px; }
              p { color: #888; margin-bottom: 20px; line-height: 1.6; }
              a { color: #FF7D29; text-decoration: none; }
              a:hover { text-decoration: underline; }
            </style></head>
            <body>
              <div class="card">
                <h1>🔒</h1>
                <h2 style="color:#FF3B30;">权限不足</h2>
                <p>你没有访问俱乐部红黑榜的权限。<br>如需访问，请联系超级管理员分配权限。</p>
                <a href="/">← 返回首页</a>
              </div>
            </body></html>
            """), 403
        return f(*args, **kwargs)
    return decorated


# ===== Public Routes =====
@app.route("/")
@app.route("/index.html")
def index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.route("/list.html")
def list_page():
    return send_from_directory(STATIC_DIR, "list.html")

@app.route('/paodao.html')
def paodao_page():
    return send_from_directory(STATIC_DIR, 'paodao.html')

@app.route('/pianju.html')
def pianju_page():
    return send_from_directory(STATIC_DIR, 'pianju.html')

@app.route('/fenghao.html')
def fenghao_page():
    return send_from_directory(STATIC_DIR, 'fenghao.html')


@app.route("/about.html")
@login_required
def about_page():
    return send_from_directory(STATIC_DIR, "about.html")

@app.route("/css/<path:filename>")
def css(filename):
    return send_from_directory(os.path.join(STATIC_DIR, "css"), filename)

@app.route("/js/<path:filename>")
def js(filename):
    return send_from_directory(os.path.join(STATIC_DIR, "js"), filename)

# ===== SEO =====
@app.route("/robots.txt")
def robots_txt():
    return """User-agent: *
Allow: /
Sitemap: https://bileizhinan.top/sitemap.xml
""", 200, {"Content-Type": "text/plain"}

@app.route("/sitemap.xml")
def sitemap_xml():
    return """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://bileizhinan.top/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>
  <url><loc>https://bileizhinan.top/list.html</loc><changefreq>daily</changefreq><priority>0.9</priority></url>
  <url><loc>https://bileizhinan.top/submit.html</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>
</urlset>
""", 200, {"Content-Type": "application/xml"}

# ===== Public API =====
@app.route("/api/session")
def api_session():
    return {"user": session.get("user", None)}

@app.route("/api/studios")
def api_studios():
    all_studios = load_studios()
    # 只返回已审核通过的工作室（前台不显示待审核的）
    published = [s for s in all_studios if s.get("status", "published") != "pending"]
    user = session.get("user")
    # 非登录用户隐藏联系方式（仅隐藏有联系方式的）
    if not user:
        for s in published:
            if s.get("contact"):
                s["contact_hidden"] = True
                s["contact"] = None
    return {"studios": published}

@app.route("/api/settings")
def api_settings():
    return load_settings()

# ===== Login =====
@app.route("/login", methods=["GET"])
def login_page():
    if "user" in session:
        return redirect(url_for("index"))
    with open(os.path.join(STATIC_DIR, "login.html")) as f:
        return render_template_string(f.read())

@app.route("/login", methods=["POST"])
def login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if check_user(username, password):
        session["user"] = username
        if "admin" in request.host:
            return redirect(url_for("admin_page"))
        return redirect(url_for("dashboard_page"))
    return redirect(url_for("login_page") + "?error=1")

# ===== 邀请码系统 =====
INVITE_FILE = os.path.join(DATA_DIR, "invite_codes.json")

def load_invites():
    if os.path.exists(INVITE_FILE):
        try:
            with open(INVITE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}

def save_invites(data):
    with open(INVITE_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_invite_code(length=8):
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 去掉易混淆的 0/O/1/I
    return "".join(random.choice(chars) for _ in range(length))

def check_invite_code(code):
    """验证邀请码，返回 True/False"""
    invites = load_invites()
    code = code.strip().upper()
    if code in invites:
        entry = invites[code]
        if entry.get("used_by") is None and entry.get("uses", 0) < entry.get("max_uses", 1):
            return True
    return False

def use_invite_code(code, username):
    """使用邀请码，标记为已用"""
    invites = load_invites()
    code = code.strip().upper()
    if code in invites:
        invites[code]["used_by"] = username
        invites[code]["uses"] = invites[code].get("uses", 0) + 1
        save_invites(invites)

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    invite = request.form.get("invite", "").strip()
    if not username or not password:
        return redirect(url_for("login_page") + "?error=2")
    if not invite:
        return redirect(url_for("login_page") + "?error=6")
    if not check_invite_code(invite):
        return redirect(url_for("login_page") + "?error=6")
    users = load_users()
    if username in users:
        return redirect(url_for("login_page") + "?error=3")
    if len(password) < 4:
        return redirect(url_for("login_page") + "?error=2")
    use_invite_code(invite, username)
    save_user(username, password)
    session["user"] = username
    return redirect(url_for("dashboard_page"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login_page"))

# ===== Public: submit (no login required) =====
@app.route("/submit.html")
def submit_page():
    return send_from_directory(STATIC_DIR, "submit.html")

@app.route("/api/report", methods=["POST"])
def api_report():
    data = request.get_json()
    if not data or not data.get("name") or not data.get("detail"):
        return {"error": "请填写工作室名称和详细经过"}, 400
    studios = load_studios()
    new_id = f"s{len(studios) + 1:03d}"
    studios.append({
        "id": new_id,
        "name": data["name"],
        "risk": data.get("risk", "warning"),
        "level": False,
        "platform": data.get("platform", ""),
        "contact": data.get("contact", ""),
        "detail": data["detail"],
        "contact_back": data.get("contact_back", ""),
        "date": time.strftime("%Y-%m-%d"),
        "source": "用户投稿",
        "reporter": "anonymous",
        "status": "pending"  # 待审核
    })
    save_studios(studios)
    return {"ok": True, "id": new_id}


# ===== Favorites API =====
@app.route("/api/favorites", methods=["GET"])
@login_required
def api_get_favorites():
    favs = load_favorites()
    user = session.get("user")
    return {"favorites": favs.get(user, [])}

@app.route("/api/favorites/<studio_id>", methods=["POST"])
@login_required
def api_add_favorite(studio_id):
    favs = load_favorites()
    user = session.get("user")
    if user not in favs:
        favs[user] = []
    if studio_id not in favs[user]:
        favs[user].append(studio_id)
    save_favorites(favs)
    return {"ok": True}

@app.route("/api/favorites/<studio_id>", methods=["DELETE"])
@login_required
def api_remove_favorite(studio_id):
    favs = load_favorites()
    user = session.get("user")
    if user in favs and studio_id in favs[user]:
        favs[user].remove(studio_id)
        save_favorites(favs)
    return {"ok": True}

# ===== Comments API =====
@app.route("/api/studios/<studio_id>/comments", methods=["GET"])
def api_get_comments(studio_id):
    all_comments = load_comments()
    studio_comments = all_comments.get(studio_id, [])
    # 只返回审核通过的评论
    visible = [c for c in studio_comments if c.get("status", "approved") != "pending"]
    return {"comments": visible, "count": len(visible)}

@app.route("/api/comments", methods=["POST"])
@login_required
def api_add_comment():
    data = request.get_json()
    if not data or not data.get("studio_id") or not data.get("content", "").strip():
        return {"error": "请填写评论内容"}, 400
    content = data["content"].strip()
    if len(content) < 2 or len(content) > 500:
        return {"error": "评论内容 2-500 字"}, 400
    all_comments = load_comments()
    studio_id = data["studio_id"]
    if studio_id not in all_comments:
        all_comments[studio_id] = []
    all_comments[studio_id].append({
        "id": "c" + str(int(time.time() * 1000)),
        "user": session.get("user"),
        "content": content,
        "date": time.strftime("%Y-%m-%d"),
        "is_admin": load_users().get(session.get("user"), {}).get("role") in ("admin", "super_admin"),
        "status": "approved"
    })
    save_comments(all_comments)
    return {"ok": True}

# ===== Admin: Comments Moderation =====
@app.route("/api/admin/comments", methods=["GET"])
@admin_required
@require_perm("reviews")
def admin_list_comments():
    all_comments = load_comments()
    result = []
    for studio_id, comments in all_comments.items():
        for c in comments:
            result.append({"studio_id": studio_id, "comment": c})
    return {"comments": result, "count": len(result)}

@app.route("/api/admin/comments/<comment_id>", methods=["PUT"])
@admin_required
@require_perm("reviews")
def admin_moderate_comment(comment_id):
    data = request.get_json() or {}
    action = data.get("action", "approve")
    all_comments = load_comments()
    found = False
    for studio_id, comments in all_comments.items():
        for c in comments:
            if c.get("id") == comment_id:
                if action == "approve":
                    c["status"] = "approved"
                elif action == "reject":
                    c["status"] = "rejected"
                elif action == "delete":
                    comments.remove(c)
                found = True
                break
    if found:
        save_comments(all_comments)
        return {"ok": True}
    return {"error": "未找到"}, 404

# ===== Admin Routes =====
@app.route("/admin.html")
@login_required
def admin_page():
    if not has_permission(session.get("user")):
        return redirect(url_for("index"))
    return send_from_directory(STATIC_DIR, "admin.html")

@app.route("/api/admin/studios", methods=["GET"])
@admin_required
@require_perm("studios")
def admin_list_studios():
    return {"studios": load_studios()}

@app.route("/api/admin/studios", methods=["POST"])
@admin_required
@require_perm("studios")
def admin_add_studio():
    data = request.get_json()
    if not data or not data.get("name"):
        return {"error": "请输入工作室名称"}, 400
    studios = load_studios()
    new_id = f"s{len(studios) + 1:03d}"
    level = data.get("level", False)
    if level == "" or level is None:
        level = False
    studios.append({
        "id": new_id,
        "name": data["name"],
        "risk": data.get("risk", "warning"),
        "level": level,
        "platform": data.get("platform", ""),
        "contact": data.get("contact", ""),
        "detail": data.get("detail", ""),
        "date": time.strftime("%Y-%m-%d"),
        "source": data.get("source", "管理员录入")
    })
    save_studios(studios)
    return {"ok": True, "id": new_id}

@app.route("/api/admin/studios/<studio_id>", methods=["PUT"])
@admin_required
@require_perm("studios")
def admin_update_studio(studio_id):
    data = request.get_json()
    if not data or not data.get("name"):
        return {"error": "请输入工作室名称"}, 400
    studios = load_studios()
    found = False
    for s in studios:
        if s["id"] == studio_id:
            level = data.get("level", False)
            if level == "" or level is None:
                level = False
            s["name"] = data["name"]
            s["risk"] = data.get("risk", "warning")
            s["level"] = level
            s["platform"] = data.get("platform", "")
            s["contact"] = data.get("contact", "")
            s["detail"] = data.get("detail", "")
            s["source"] = data.get("source", "")
            found = True
            break
    if not found:
        return {"error": "未找到该工作室"}, 404
    save_studios(studios)
    return {"ok": True}

@app.route("/api/admin/studios/<studio_id>", methods=["DELETE"])
@admin_required
@require_perm("studios")
def admin_delete_studio(studio_id):
    studios = load_studios()
    new_studios = [s for s in studios if s["id"] != studio_id]
    if len(new_studios) == len(studios):
        return {"error": "未找到该工作室"}, 404
    save_studios(new_studios)
    return {"ok": True}

# ===== Admin: Review Submissions =====
@app.route("/api/admin/reviews", methods=["GET"])
@admin_required
@require_perm("reviews")
def admin_list_reviews():
    all_studios = load_studios()
    pending = [s for s in all_studios if s.get("status") == "pending"]
    return {"pending": pending, "count": len(pending)}

@app.route("/api/admin/reviews/<studio_id>", methods=["PUT"])
@admin_required
@require_perm("reviews")
def admin_review_studio(studio_id):
    data = request.get_json() or {}
    action = data.get("action", "approve")
    studios = load_studios()
    found = False
    for s in studios:
        if s["id"] == studio_id:
            if action == "approve":
                s["status"] = "published"
                s["risk"] = data.get("risk", s.get("risk", "warning"))
                s["level"] = data.get("level", s.get("level", False))
                s["platform"] = data.get("platform", s.get("platform", ""))
            elif action == "reject":
                s["status"] = "rejected"
            found = True
            break
    if not found:
        return {"error": "未找到"}, 404
    save_studios(studios)
    return {"ok": True, "action": action, "id": studio_id}

@app.route("/api/admin/settings", methods=["GET"])
@admin_required
@require_perm("settings")
def admin_get_settings():
    return load_settings()

@app.route("/api/admin/settings", methods=["PUT"])
@admin_required
@require_perm("settings")
def admin_update_settings():
    data = request.get_json()
    if not data:
        return {"error": "无效数据"}, 400
    current = load_settings()
    allowed_keys = list(SETTINGS_DEFAULTS.keys())
    for key in allowed_keys:
        if key in data and data[key] is not None and data[key] != "":
            current[key] = data[key]
    save_settings(current)
    return {"ok": True, "settings": current}

# ===== Admin: User Management =====
@app.route("/api/admin/users", methods=["GET"])
@super_admin_required
def admin_list_users():
    users = load_users()
    safe = {}
    for u, data in users.items():
        safe[u] = {
            "role": data.get("role", "user"),
            "permissions": data.get("permissions", [])
        }
    return {"users": safe, "current": session.get("user")}

@app.route("/api/admin/users", methods=["POST"])
@super_admin_required
def admin_add_user():
    data = request.get_json()
    if not data:
        return {"error": "无效数据"}, 400
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not username or not password:
        return {"error": "用户名和密码不能为空"}, 400
    if len(username) < 2 or len(password) < 4:
        return {"error": "用户名至少2位，密码至少4位"}, 400
    users = load_users()
    if username in users:
        return {"error": "用户名已存在"}, 400
    # 权限设置
    role = data.get("role", "admin")
    permissions = data.get("permissions", [])
    if role not in ["admin", "user"]:
        role = "admin"
    save_user(username, password, role=role, permissions=permissions)
    return {"ok": True, "username": username, "role": role, "permissions": permissions}

@app.route("/api/admin/users/<username>", methods=["DELETE"])
@super_admin_required
def admin_delete_user(username):
    current_user = session.get("user")
    if username == current_user:
        return {"error": "不能删除自己"}, 400
    if username == "admin":
        return {"error": "不能删除超级管理员"}, 400
    users = load_users()
    if username not in users:
        return {"error": "用户不存在"}, 404
    del users[username]
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    return {"ok": True}

@app.route("/api/admin/users/<username>/password", methods=["PUT"])
@admin_required
def admin_change_password(username):
    data = request.get_json()
    if not data:
        return {"error": "无效数据"}, 400
    current_user = session.get("user")
    password = data.get("password", "").strip()
    if not password:
        return {"error": "密码不能为空"}, 400
    if len(password) < 4:
        return {"error": "密码至少4位"}, 400
    users = load_users()
    if username not in users:
        return {"error": "用户不存在"}, 404
    # 改别人密码需要是 admin
    if username != current_user and current_user != "admin":
        return {"error": "权限不足"}, 403
    # 保存新密码
    save_user(username, password)
    return {"ok": True, "username": username}

@app.route("/api/admin/users/<username>/permissions", methods=["PUT"])
@super_admin_required
def admin_update_permissions(username):
    data = request.get_json()
    if not data:
        return {"error": "无效数据"}, 400
    if username == "admin":
        return {"error": "不能修改超级管理员权限"}, 400
    users = load_users()
    if username not in users:
        return {"error": "用户不存在"}, 404
    role = data.get("role", users[username].get("role", "admin"))
    permissions = data.get("permissions", [])
    users[username]["role"] = role
    users[username]["permissions"] = permissions
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    return {"ok": True, "username": username, "role": role, "permissions": permissions}

# ===== Admin: Invite Codes =====
@app.route("/api/admin/invites", methods=["GET"])
@admin_required
@require_perm("invites")
def admin_list_invites():
    invites = load_invites()
    return {"invites": invites}

@app.route("/api/admin/invites", methods=["POST"])
@admin_required
@require_perm("invites")
def admin_create_invite():
    data = request.get_json() or {}
    count = int(data.get("count", 1))
    if count < 1 or count > 50:
        return {"error": "数量范围 1-50"}, 400
    invites = load_invites()
    created = []
    for _ in range(count):
        code = generate_invite_code()
        while code in invites:
            code = generate_invite_code()
        invites[code] = {
            "created_at": time.time(),
            "used_by": None,
            "uses": 0,
            "max_uses": 1  # 默认只能用一次
        }
        created.append(code)
    save_invites(invites)
    return {"ok": True, "codes": created, "count": len(created)}

@app.route("/api/admin/invites/<code>", methods=["DELETE"])
@admin_required
@require_perm("invites")
def admin_delete_invite(code):
    invites = load_invites()
    code = code.upper()
    if code not in invites:
        return {"error": "邀请码不存在"}, 404
    del invites[code]
    save_invites(invites)
    return {"ok": True}

# ===== Init Default User =====
if not os.path.exists(USERS_FILE):
    save_user("admin", "admin123", role="super_admin")



# ===== Redblack Routes =====
@app.route("/redblack")
@redblack_required
def redblack_page():
    """红黑榜管理页面 - 仅管理员可访问"""
    return send_from_directory(STATIC_DIR, 'redblack.html')

@app.route("/api/redblack")
@redblack_required
def api_redblack():
    """红黑榜数据 API - 返回完整工作室数据"""
    return {"studios": load_studios()}

# ===== Contact/Customer Service =====
CONTACT_FILE = os.path.join(DATA_DIR, "contact_messages.json")

def load_contact_messages():
    if not os.path.exists(CONTACT_FILE):
        return []
    with open(CONTACT_FILE) as f:
        return json.load(f)

def save_contact_messages(data):
    with open(CONTACT_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/api/contact", methods=["POST"])
def api_contact():
    data = request.get_json()
    if not data or not data.get("content", "").strip():
        return {"error": "请填写内容"}, 400
    name = (data.get("name") or "").strip() or "匿名"
    content = data["content"].strip()
    if len(content) > 1000:
        return {"error": "内容太长"}, 400
    msgs = load_contact_messages()
    msgs.append({
        "id": "m" + str(int(time.time() * 1000)),
        "name": name,
        "content": content,
        "contact": (data.get("contact") or "").strip(),
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "read": False
    })
    save_contact_messages(msgs)
    return {"ok": True}

@app.route("/api/admin/contact", methods=["GET"])
@admin_required
def admin_list_contact():
    return {"messages": load_contact_messages()}

@app.route("/api/admin/contact/<msg_id>", methods=["PUT"])
@admin_required
def admin_mark_read(msg_id):
    msgs = load_contact_messages()
    for m in msgs:
        if m.get("id") == msg_id:
            m["read"] = True
            save_contact_messages(msgs)
            return {"ok": True}
    return {"error": "未找到"}, 404

@app.route("/api/admin/contact/<msg_id>", methods=["DELETE"])
@admin_required
def admin_delete_contact(msg_id):
    msgs = load_contact_messages()
    msgs = [m for m in msgs if m.get("id") != msg_id]
    save_contact_messages(msgs)
    return {"ok": True}




@app.route("/api/admin/contact/<msg_id>/reply", methods=["POST"])
@admin_required
def admin_reply_contact(msg_id):
    data = request.get_json()
    if not data or not data.get("content", "").strip():
        return {"error": "请填写回复内容"}, 400
    msgs = load_contact_messages()
    for m in msgs:
        if m.get("id") == msg_id:
            if "replies" not in m:
                m["replies"] = []
            m["replies"].append({
                "id": "r" + str(int(time.time() * 1000)),
                "content": data["content"].strip(),
                "date": time.strftime("%Y-%m-%d %H:%M"),
                "admin": session.get("user", "admin")
            })
            m["read"] = True
            save_contact_messages(msgs)
            return {"ok": True, "reply": m["replies"][-1]}
    return {"error": "未找到"}, 404

@app.route("/api/contact/lookup", methods=["POST"])
def api_contact_lookup():
    data = request.get_json()
    q = (data.get("query") or "").strip().lower()
    if not q:
        return {"error": "请输入查询条件"}, 400
    msgs = load_contact_messages()
    results = []
    for m in msgs:
        if q in (m.get("name") or "").lower() or q in (m.get("contact") or "").lower() or q == (m.get("id") or "").lower():
            results.append({
                "id": m.get("id"),
                "name": m.get("name"),
                "content": m.get("content"),
                "date": m.get("date"),
                "replies": m.get("replies", [])
            })
    return {"messages": results[:20]}


# ===== User Dashboard =====
@app.route("/dashboard")
@login_required
def dashboard_page():
    return send_from_directory(STATIC_DIR, "dashboard.html")

@app.route("/api/dashboard/stats")
@login_required
def api_dashboard_stats():
    user = session.get("user")
    # 投稿数
    all_studios = load_studios()
    submissions = [s for s in all_studios if s.get("reporter") == user]
    # 评论数
    all_comments = load_comments()
    user_comments = 0
    for sid, comments in all_comments.items():
        for c in comments:
            if c.get("user") == user:
                user_comments += 1
    # 收藏数
    favs = load_favorites()
    user_favs = len(favs.get(user, []))
    return {"submissions": len(submissions), "comments": user_comments, "favorites": user_favs}

@app.route("/api/user/submissions")
@login_required
def api_user_submissions():
    user = session.get("user")
    all_studios = load_studios()
    user_subs = [s for s in all_studios if s.get("reporter") == user]
    return {"submissions": user_subs}

@app.route("/api/user/comments")
@login_required
def api_user_comments():
    user = session.get("user")
    all_comments = load_comments()
    all_studios = load_studios()
    studio_names = {s["id"]: s["name"] for s in all_studios}
    result = []
    for studio_id, comments in all_comments.items():
        for c in comments:
            if c.get("user") == user:
                result.append({
                    "studio_id": studio_id,
                    "studio_name": studio_names.get(studio_id, studio_id),
                    "content": c.get("content", ""),
                    "date": c.get("date", "")
                })
    return {"comments": result}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
