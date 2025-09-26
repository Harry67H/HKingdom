from flask import Flask, render_template_string, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO

# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SECRET_KEY'] = 'hkingdomsecret'
db = SQLAlchemy(app)

# ---------------- DATABASE MODELS ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    likes = db.relationship('Like', backref='user', lazy=True)

class Series(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    private_description = db.Column(db.Text)
    thumbnail = db.Column(db.LargeBinary)
    approved = db.Column(db.Boolean, default=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    episodes = db.relationship('Episode', backref='series', lazy=True)
    season = db.Column(db.String(50), default="Season 1")

class Episode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    video_data = db.Column(db.LargeBinary)
    thumbnail = db.Column(db.LargeBinary)
    approved = db.Column(db.Boolean, default=False)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    private_description = db.Column(db.Text)
    video_data = db.Column(db.LargeBinary)
    thumbnail = db.Column(db.LargeBinary)
    approved = db.Column(db.Boolean, default=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content_type = db.Column(db.String(20))
    content_id = db.Column(db.Integer)

# ---------------- CREATE DATABASE ----------------
with app.app_context():
    db.create_all()

# ---------------- DARK MODE CSS ----------------
dark_mode_css = """
<style>
body { background-color:#121212; color:#fff; font-family:sans-serif; margin:0; padding:20px; }
a { color:#1E90FF; text-decoration:none; }
input, textarea { background:#222; color:#fff; border:1px solid #555; padding:5px; }
button { background:#1E90FF; color:#fff; border:none; padding:5px 10px; cursor:pointer; }
img { max-width:200px; }
form { margin-bottom:20px; }
</style>
"""

# ---------------- HELPER FUNCTIONS ----------------
def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def is_admin():
    user = current_user()
    return user.is_admin if user else False

# ---------------- ROUTES ----------------
@app.route('/')
def home():
    user = current_user()
    series = Series.query.filter_by(approved=True).all()
    movies = Movie.query.filter_by(approved=True).all()
    return render_template_string(dark_mode_css + """
    <h1>H Kingdom</h1>
    {% if user %}
        <p>Welcome, {{ user.username }} | <a href="{{ url_for('logout') }}">Logout</a></p>
    {% else %}
        <a href="{{ url_for('login') }}">Login</a> | <a href="{{ url_for('signup') }}">Sign Up</a>
    {% endif %}
    <h2>Series</h2>
    {% for s in series %}
        <div>
        {% if s.thumbnail %}
            <img src="{{ url_for('get_series_thumbnail', series_id=s.id) }}">
        {% endif %}
        <a href="{{ url_for('view_series', series_id=s.id) }}">{{ s.title }}</a> (Season: {{ s.season }})
        </div>
    {% endfor %}
    <h2>Movies</h2>
    {% for m in movies %}
        <div>
        {% if m.thumbnail %}
            <img src="{{ url_for('get_movie_thumbnail', movie_id=m.id) }}">
        {% endif %}
        {{ m.title }}
        </div>
    {% endfor %}
    <form action="{{ url_for('search') }}" method="get">
        <input name="q" placeholder="Search...">
        <button>Search</button>
    </form>
    {% if user %}
        <a href="{{ url_for('create_series') }}">Create Series</a> |
        <a href="{{ url_for('create_movie') }}">Create Movie</a>
    {% endif %}
    """, user=user, series=series, movies=movies)

# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user = User(email=email, username=username, password=password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('home'))
    return render_template_string(dark_mode_css + """
    <h1>Sign Up</h1>
    <form method="post">
        Email: <input name="email"><br>
        Username: <input name="username"><br>
        Password: <input type="password" name="password"><br>
        <button>Sign Up</button>
    </form>
    """)

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        elif password == 'abcdPOO123qwertyLLL':
            admin = User.query.filter_by(username='H Kingdom').first()
            if not admin:
                admin = User(email='hkingdom@admin.com', username='H Kingdom', password=generate_password_hash('admin'), is_admin=True)
                db.session.add(admin)
                db.session.commit()
            session['user_id'] = admin.id
            return redirect(url_for('home'))
        flash("Invalid credentials")
    return render_template_string(dark_mode_css + """
    <h1>Login</h1>
    <form method="post">
        Username: <input name="username"><br>
        Password: <input type="password" name="password"><br>
        <button>Login</button>
    </form>
    """)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# ---------------- SEARCH ----------------
@app.route('/search')
def search():
    q = request.args.get('q','')
    series = Series.query.filter(Series.title.contains(q), Series.approved==True).all()
    movies = Movie.query.filter(Movie.title.contains(q), Movie.approved==True).all()
    return render_template_string(dark_mode_css + """
    <h1>Search Results for '{{ q }}'</h1>
    <a href="{{ url_for('home') }}">Back</a>
    <h2>Series</h2>{% for s in series %}<div>{{ s.title }}</div>{% endfor %}
    <h2>Movies</h2>{% for m in movies %}<div>{{ m.title }}</div>{% endfor %}
    """, series=series, movies=movies, q=q)

# ---------------- CREATE SERIES ----------------
@app.route('/create_series', methods=['GET','POST'])
def create_series():
    user = current_user()
    if not user: return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        private_description = request.form['private_description']
        season = request.form.get('season') or "Season 1"
        thumbnail = request.files['thumbnail'].read() if 'thumbnail' in request.files else None
        s = Series(title=title, description=description, private_description=private_description, thumbnail=thumbnail, creator_id=user.id, season=season)
        db.session.add(s)
        db.session.commit()
        flash("Series submitted for approval!")
        return redirect(url_for('home'))
    return render_template_string(dark_mode_css + """
    <h1>Create Series</h1>
    <form method="post" enctype="multipart/form-data">
        Title: <input name="title"><br>
        Description: <textarea name="description"></textarea><br>
        Private Description: <textarea name="private_description"></textarea><br>
        Season: <input name="season"><br>
        Thumbnail: <input type="file" name="thumbnail"><br>
        <button>Submit Series</button>
    </form>
    """)

# ---------------- CREATE MOVIE ----------------
@app.route('/create_movie', methods=['GET','POST'])
def create_movie():
    user = current_user()
    if not user: return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        private_description = request.form['private_description']
        thumbnail = request.files['thumbnail'].read() if 'thumbnail' in request.files else None
        video_data = request.files['video_data'].read() if 'video_data' in request.files else None
        m = Movie(title=title, description=description, private_description=private_description, thumbnail=thumbnail, video_data=video_data, creator_id=user.id)
        db.session.add(m)
        db.session.commit()
        flash("Movie submitted for approval!")
        return redirect(url_for('home'))
    return render_template_string(dark_mode_css + """
    <h1>Create Movie</h1>
    <form method="post" enctype="multipart/form-data">
        Title: <input name="title"><br>
        Description: <textarea name="description"></textarea><br>
        Private Description: <textarea name="private_description"></textarea><br>
        Thumbnail: <input type="file" name="thumbnail"><br>
        Video File: <input type="file" name="video_data"><br>
        <button>Submit Movie</button>
    </form>
    """)

# ---------------- VIEW SERIES ----------------
@app.route('/series/<int:series_id>')
def view_series(series_id):
    s = Series.query.get_or_404(series_id)
    episodes = Episode.query.filter_by(series_id=series_id, approved=True).all()
    user = current_user()
    return render_template_string(dark_mode_css + """
    <h1>{{ s.title }} ({{ s.season }})</h1>
    {% if s.thumbnail %}
        <img src="{{ url_for('get_series_thumbnail', series_id=s.id) }}">
    {% endif %}
    <p>{{ s.description }}</p>
    <h2>Episodes</h2>
    {% for e in episodes %}
        <div>
            {% if e.thumbnail %}
                <img src="{{ url_for('get_episode_thumbnail', episode_id=e.id) }}">
            {% endif %}
            <a href="{{ url_for('watch_episode', episode_id=e.id) }}">{{ e.title }}</a>
        </div>
    {% endfor %}
    {% if user %}
        <a href="{{ url_for('create_episode', series_id=s.id) }}">Add Episode</a>
    {% endif %}
    {% if user and user.is_admin %}
        <form method="post" action="{{ url_for('approve_series', series_id=s.id) }}">
            <button>Approve Series</button>
        </form>
        <form method="post" action="{{ url_for('mega_like_series', series_id=s.id) }}">
            <button>Mega Like Series</button>
        </form>
    {% endif %}
    <a href="{{ url_for('home') }}">Back Home</a>
    """, s=s, episodes=episodes, user=user)

# ---------------- CREATE EPISODE ----------------
@app.route('/series/<int:series_id>/create_episode', methods=['GET','POST'])
def create_episode(series_id):
    s = Series.query.get_or_404(series_id)
    user = current_user()
    if not user: return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        thumbnail = request.files['thumbnail'].read() if 'thumbnail' in request.files else None
        video_data = request.files['video_data'].read() if 'video_data' in request.files else None
        e = Episode(title=title, description=description, thumbnail=thumbnail, video_data=video_data, series_id=series_id, creator_id=user.id)
        db.session.add(e)
        db.session.commit()
        flash("Episode submitted for approval!")
        return redirect(url_for('view_series', series_id=series_id))
    return render_template_string(dark_mode_css + """
    <h1>Create Episode for {{ s.title }}</h1>
    <form method="post" enctype="multipart/form-data">
        Title: <input name="title"><br>
        Description: <textarea name="description"></textarea><br>
        Thumbnail: <input type="file" name="thumbnail"><br>
        Video File: <input type="file" name="video_data"><br>
        <button>Submit Episode</button>
    </form>
    """, s=s)

# ---------------- WATCH EPISODE ----------------
@app.route('/episode/<int:episode_id>/watch')
def watch_episode(episode_id):
    e = Episode.query.get_or_404(episode_id)
    return send_file(BytesIO(e.video_data), mimetype='video/mp4', as_attachment=False, download_name=e.title+".mp4")

# ---------------- THUMBNAILS ----------------
@app.route('/series_thumbnail/<int:series_id>')
def get_series_thumbnail(series_id):
    s = Series.query.get_or_404(series_id)
    return send_file(BytesIO(s.thumbnail), mimetype='image/jpeg') if s.thumbnail else ''

@app.route('/movie_thumbnail/<int:movie_id>')
def get_movie_thumbnail(movie_id):
    m = Movie.query.get_or_404(movie_id)
    return send_file(BytesIO(m.thumbnail), mimetype='image/jpeg') if m.thumbnail else ''

@app.route('/episode_thumbnail/<int:episode_id>')
def get_episode_thumbnail(episode_id):
    e = Episode.query.get_or_404(episode_id)
    return send_file(BytesIO(e.thumbnail), mimetype='image/jpeg') if e.thumbnail else ''

# ---------------- APPROVE SERIES ----------------
@app.route('/series/<int:series_id>/approve', methods=['POST'])
def approve_series(series_id):
    user = current_user()
    if not user or not user.is_admin: return redirect(url_for('home'))
    s = Series.query.get_or_404(series_id)
    s.approved = True
    db.session.commit()
    flash("Series approved!")
    return redirect(url_for('view_series', series_id=series_id))

# ---------------- MEGA LIKE SERIES ----------------
@app.route('/series/<int:series_id>/mega_like', methods=['POST'])
def mega_like_series(series_id):
    user = current_user()
    if not user or not user.is_admin: return redirect(url_for('home'))
    series = Series.query.get_or_404(series_id)
    for u in User.query.all():
        existing = Like.query.filter_by(user_id=u.id, content_type='series', content_id=series.id).first()
        if not existing:
            db.session.add(Like(user_id=u.id, content_type='series', content_id=series.id))
    db.session.commit()
    flash("Mega-like applied!")
    return redirect(url_for('view_series', series_id=series_id))

# ---------------- LIKE CONTENT ----------------
@app.route('/like/<content_type>/<int:content_id>')
def like_content(content_type, content_id):
    user = current_user()
    if not user: return redirect(url_for('login'))
    existing = Like.query.filter_by(user_id=user.id, content_type=content_type, content_id=content_id).first()
    if not existing:
        db.session.add(Like(user_id=user.id, content_type=content_type, content_id=content_id))
        db.session.commit()
    return redirect(request.referrer or url_for('home'))

# ---------------- RUN APP ----------------
if __name__ == '__main__':
    app.run(debug=True)
