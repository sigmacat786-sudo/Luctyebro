import os
import re
import unicodedata
import functools
from datetime import datetime, timedelta

from flask import Flask, render_template, request, jsonify, redirect, url_for, session

from utils.db import get_db

# ─── Configuration ──────────────────────────────────────────────────────────
# Public domain shown/used in every generated Lecture/Quiz link.
# Hardcoded (not read from env) on purpose — this is the ONLY line to edit
# if this service's Render domain ever changes.
PUBLIC_BASE_URL = "https://smartyms-toxic-live-class-system.onrender.com"

# ─── Server-side Admin Auth (keys never reach the browser) ────────────────
OWNER_NAME = "ViPvxMS10BRO"
ADMIN_KEYS = ["MS#Admin_R4!xQ8Lp7", "Core$MS_N6v!T2Zk9", "mS@Root_P8#Lm5Qx3"]
VIP_KEYS = ["ToXic#ViPR8m!4QxL7", "tOxic@VipN5v!9ZpK2", "ToXic$ViPX7#rT3Lm8"]

# ─── Flask app ──────────────────────────────────────────────────────────────
flask_app = Flask(__name__)

# SECRET_KEY signs the session cookie. Set a SECRET_KEY env var on Render so
# admin sessions survive restarts/redeploys — without it a fallback is used
# and everyone is logged out whenever the process restarts.
flask_app.secret_key = os.environ.get("SECRET_KEY", "c7c8d55d9d8b4a3c2f71b1f5f79c8ea84e8d2c7c3a4b51d70b91ef0fdad5f2f6f13e9a7b8c6d1e24f4a8e9c0b5d3a7f6d8e2c1b9a4f7d5e8c3a6b1d0f9e2c7")
flask_app.config["SESSION_COOKIE_HTTPONLY"] = True
flask_app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
flask_app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)

db = get_db()
lectures_col = db["lectures"]


def admin_required(view):
    """Guards admin-only routes with the server-side session set by /login.
    API routes get a JSON 401; page routes get redirected back to the
    login/generate portal at '/'.
    """
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            if request.path.startswith("/api/"):
                return jsonify({"ok": False, "error": "Login required"}), 401
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapped


def _sanitize_name(name: str) -> str:
    """
    Turns an admin-entered Lecture/Quiz name into a URL-safe slug:
    spaces become hyphens, and only letters (any script), numbers and
    hyphens are kept — no underscores, no spaces, no special characters,
    no emojis. Capped at 100 chars.
    """
    name = (name or "").strip()
    name = re.sub(r"\s+", "-", name)
    kept = []
    for ch in name:
        if ch == "-":
            kept.append(ch)
            continue
        category = unicodedata.category(ch)  # 'Lx'=letter, 'Nx'=number
        if category[0] in ("L", "N"):
            kept.append(ch)
        # anything else (symbols, punctuation, underscore, emoji) is dropped
    slug = "".join(kept)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug[:100]


# ─── Auth routes ────────────────────────────────────────────────────────────
@flask_app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    name_ok = data.get("owner_name") == OWNER_NAME
    admin_ok = data.get("admin_key") in ADMIN_KEYS
    vip_ok = data.get("vip_key") in VIP_KEYS

    if name_ok and admin_ok and vip_ok:
        session.permanent = True
        session["is_admin"] = True
        return jsonify({"ok": True})

    return jsonify({"ok": False, "error": "Invalid Name / Admin Key / VIP Key. Check karo aur dobara try karo."}), 401


@flask_app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


# ─── Page: Admin login + link-generate portal ──────────────────────────────
@flask_app.route("/")
def index():
    return render_template("admin.html")


# ─── API: paste original Lecture/Quiz link + name -> save + generate link ──
@flask_app.route("/api/generate", methods=["POST"])
@admin_required
def api_generate():
    data = request.get_json(silent=True) or {}
    original_url = (data.get("original_url") or "").strip()
    desired_name = (data.get("name") or "").strip()

    if not original_url:
        return jsonify({"ok": False, "error": "Original Lecture/Quiz link required"}), 400
    if not (original_url.startswith("http://") or original_url.startswith("https://")):
        return jsonify({"ok": False, "error": "Invalid link — valid http(s) URL do"}), 400

    name = _sanitize_name(desired_name)
    if not name:
        return jsonify({
            "ok": False,
            "error": "Invalid Lecture/Quiz name — sirf letters, numbers aur hyphen(-) allowed hai."
        }), 400

    now = datetime.utcnow()
    lectures_col.update_one(
        {"_id": name},
        {
            "$set": {"original_url": original_url, "updated_at": now},
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )

    public_link = f"{PUBLIC_BASE_URL}/{name}"
    return jsonify({"ok": True, "name": name, "public_link": public_link})


# ─── Page: Generated link result page ──────────────────────────────────────
@flask_app.route("/generated/<name>")
def generated(name):
    doc = lectures_col.find_one({"_id": name}, {"_id": 1})
    if not doc:
        return redirect(url_for("index"))
    public_link = f"{PUBLIC_BASE_URL}/{name}"
    return render_template("generated.html", name=name, public_link=public_link)


# ─── Page: Live Class / Quiz viewer (existing look, feel & protections — ──
# ─── unchanged: iframe sandbox, popup block, back-button lock overlay) ────
@flask_app.route("/<name>")
def play(name):
    doc = lectures_col.find_one({"_id": name})
    if not doc:
        return "Link galat hai ya Class/Quiz expire ho gaya. 😔", 404
    return render_template("index.html", quiz_url=doc["original_url"])


def run_flask():
    port = int(os.environ.get("PORT", 8000))
    flask_app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    # Started directly (no separate bot process here), so just run Flask
    # in the main thread. If you later add a bot/worker loop, start Flask
    # in a background thread instead (see run_flask above) and keep this
    # thread for the worker.
    run_flask()
