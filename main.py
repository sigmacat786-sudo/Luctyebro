import os
import threading
from flask import Flask, render_template

# ─── Configuration ──────────────────────────────────────────────────────────
# Source quiz URL — shown openly to users (not hidden/cloaked).
QUIZ_URL = "https://vidcloud.eu.org/play.php?batch_id=6a38f418034b8baed508e6e4&subject_id=6a48b4351b64047a0b9fe3dd&topic_id=6a491789704bec63c66cae64&video_id=6a669b244577223c93f7af1d&video_name=%E0%A4%B5%E0%A4%BF%E0%A4%B2%E0%A4%AF%E0%A4%A8+03+%3A+%E0%A4%B0%E0%A4%BE%E0%A4%B8%E0%A4%BE%E0%A4%AF%E0%A4%A8%E0%A4%BF%E0%A4%95+%E0%A4%B8%E0%A4%82%E0%A4%AF%E0%A5%8B%E0%A4%9C%E0%A4%A8+%E0%A4%95%E0%A5%87+%E0%A4%A8%E0%A4%BF%E0%A4%AF%E0%A4%AE+%7C%7C+DPP+will+be+provided+soon&video_img=&video_type=live&play_type=Lecture"

# ─── Flask app ──────────────────────────────────────────────────────────────
flask_app = Flask(__name__)


@flask_app.route('/')
def index():
    return render_template('index.html', quiz_url=QUIZ_URL)


def run_flask():
    port = int(os.environ.get("PORT", 8000))
    flask_app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    # Started directly (no separate bot process here), so just run Flask
    # in the main thread. If you later add a bot/worker loop, start Flask
    # in a background thread instead (see run_flask above) and keep this
    # thread for the worker.
    run_flask()
