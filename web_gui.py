from pathlib import Path
import json
import asyncio
from flask import Flask, request, redirect, render_template, session
from social_p2p import Peer, DEFAULT_PORT

app = Flask(__name__)
app.secret_key = 'p2psocial'

def get_peer():
    username = session.get('username')
    if not username:
        return None
    data_dir = Path.home() / '.p2psocial'
    profile_path = data_dir / f"{username}_profile.json"
    return Peer(username, port=DEFAULT_PORT, profile_path=profile_path)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        return redirect('/')
    peer = get_peer()
    if not peer:
        return render_template('login.html')
    posts = asyncio.run(peer.fetch_posts(peer.username))
    return render_template('index.html', username=peer.username, posts=posts)

@app.route('/post', methods=['POST'])
def post_message():
    peer = get_peer()
    if not peer:
        return redirect('/')
    text = request.form['text']
    asyncio.run(peer.add_post(text))
    return redirect('/')

if __name__ == '__main__':
    app.run(port=5000)
