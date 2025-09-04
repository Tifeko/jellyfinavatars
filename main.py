import os
import base64
import requests
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.urandom(24)

load_dotenv()
JELLYFIN_URL = os.getenv("JELLYFIN_URL")
JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY")
AVATAR_FOLDER = os.path.join("static", "avatars")

# ---------- Helper Functions ----------

def jellyfin_get(path):
    url = f"{JELLYFIN_URL}{path}?apiKey={JELLYFIN_API_KEY}"
    return requests.get(url)

def get_avatar_url(user):
    """Return user avatar URL or default if not set"""
    if user.get("PrimaryImageTag"):
        return f"{JELLYFIN_URL}/Users/{user['Id']}/Images/Primary?tag={user['PrimaryImageTag']}"
    return "/static/default-avatar.png"

# ---------- Routes ----------

@app.route("/")
def index():
    """List public users (no password)"""
    resp = jellyfin_get("/Users/Public")
    if resp.status_code != 200:
        return f"Failed to fetch users: {resp.status_code}", 500

    users = resp.json()
    public_users = [u for u in users if not u.get("HasPassword")]
    for u in public_users:
        u["avatar"] = get_avatar_url(u)

    return render_template("index.html", users=public_users)

@app.route("/avatars/<user_id>")
def avatars(user_id):
    # Ensure user_id exists
    if not user_id:
        return "Missing user_id", 400

    # List avatar images
    try:
        avatars = [
            f for f in os.listdir(AVATAR_FOLDER)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]
    except FileNotFoundError:
        return "Avatar folder not found", 500

    # Fetch user info
    resp = jellyfin_get(f"/Users/{user_id}")
    if resp.status_code != 200:
        return f"Failed to fetch user info: {resp.status_code}", 500
    user = resp.json()
    user_name = user.get("Name", "Unknown")

    selected = session.get("selected_avatar")
    return render_template(
        "avatars.html",
        avatars=avatars,
        selected=selected,
        user_id=user_id,
        user_name=user_name
    )

@app.route("/select-avatar/<filename>", methods=["POST"])
def select_avatar(filename):
    """Set selected avatar for Jellyfin user"""
    user_id = request.form.get("user_id")
    if not user_id:
        return "Missing user_id", 400

    filepath = os.path.join(AVATAR_FOLDER, filename)
    if not os.path.exists(filepath):
        return "File not found", 404

    # Detect content type
    if filename.endswith(".png"):
        content_type = "image/png"
    elif filename.endswith((".jpg", ".jpeg")):
        content_type = "image/jpeg"
    else:
        return "Unsupported image format", 400

    # Read and encode as Base64
    with open(filepath, "rb") as f:
        img_bytes = f.read()
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")

    # POST to Jellyfin
    url = f"{JELLYFIN_URL}/Users/{user_id}/Images/Primary?apiKey={JELLYFIN_API_KEY}"
    headers = {"Content-Type": content_type}
    print(img_base64)
    payload = img_base64

    resp = requests.post(url, headers=headers, data=payload)

    if resp.status_code in (200, 204):
        session["selected_avatar"] = filename
        return redirect(url_for("avatars", user_id=user_id))
    else:
        return (f"Failed to update avatar: {resp.status_code} {resp.text}", 400)

# ---------- Run ----------

if __name__ == "__main__":
    app.run(debug=True)
