from flask import Flask, render_template, send_from_directory, request, redirect, url_for, session
import os
from dotenv import load_dotenv
import requests

app = Flask(__name__)
app.secret_key = "4de7fc58390ee0ef60ed6eb443f12e5dc8ff0c1718fb6c69314ae8ccc7a56cbc"

load_dotenv()

JELLYFIN_URL = os.getenv("JELLYFIN_URL")
JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY")

# Folder where avatars are stored
AVATAR_FOLDER = os.path.join("static", "avatars")

@app.route("/")
def index():
    response = requests.get(f"{JELLYFIN_URL}/Users/Public")
    users = response.json()
    
    public_users = [u for u in users if not u.get("HasPassword")]

    for u in public_users:
        if u.get("PrimaryImageTag"):
            u["avatar"] = f"{JELLYFIN_URL}/Users/{u['Id']}/Images/Primary?tag={u['PrimaryImageTag']}"
        else:
            u["avatar"] = "/static/default-avatar.png"  # fallback plaatje

    return render_template("index.html", users=public_users)


@app.route("/avatars/<user_id>")
def avatars(user_id):
    avatars = [f for f in os.listdir(AVATAR_FOLDER) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))]

    # fetch user details from Jellyfin
    headers = {
        "X-Emby-Token": JELLYFIN_API_KEY
    }
    resp = requests.get(f"{JELLYFIN_URL}/Users/{user_id}", headers=headers)
    user = resp.json()
    user_name = user.get("Name", "Unknown")

    selected = session.get("selected_avatar")
    return render_template("avatars.html", avatars=avatars, selected=selected, user_id=user_id, user_name=user_name)


@app.route("/select-avatar/<filename>", methods=["POST"])
def select_avatar(filename):
    user_id = request.form.get("user_id")
    filepath = os.path.join(AVATAR_FOLDER, filename)

    # Detect content type
    if filename.endswith(".png"):
        content_type = "image/png"
    elif filename.endswith((".jpg", ".jpeg")):
        content_type = "image/jpeg"
    else:
        return "Unsupported image format", 400

    with open(filepath, "rb") as f:
        img_bytes = f.read()

    # Build URL with query parameters
    url = f"{JELLYFIN_URL}/Users/{user_id}/Images/Primary"

    headers = {
        "Content-Type": content_type
    }

    print(img_bytes)
    resp = requests.post(url, headers=headers, data=img_bytes)

    if resp.status_code in (200, 204):
        session["selected_avatar"] = filename
        return redirect(url_for("avatars", user_id=user_id))
    else:
        return f"Failed to update avatar: {resp.status_code} {resp.text}", 400


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(AVATAR_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
