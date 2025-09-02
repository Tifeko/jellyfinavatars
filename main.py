from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

# Folder where avatars are stored
AVATAR_FOLDER = os.path.join("static", "avatars")

@app.route("/")
def index():
    # List all files in the avatar folder
    avatars = os.listdir(AVATAR_FOLDER)
    avatars = [f for f in avatars if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))]
    return render_template("index.html", avatars=avatars)

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(AVATAR_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
