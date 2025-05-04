from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import requests
from urllib.parse import urlparse

# Konfigurasi upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'thumbnails')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Pastikan direktori instance dan upload ada
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "videos.db")}'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
db = SQLAlchemy(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_image_url(url):
    try:
        # Check if URL has an image extension
        parsed = urlparse(url)
        ext = os.path.splitext(parsed.path)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
            return False
            
        # Try to get headers only
        response = requests.head(url, allow_redirects=True, timeout=5)
        content_type = response.headers.get('content-type', '')
        return 'image' in content_type
    except:
        return False

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    videos = db.relationship('Video', backref='category', lazy=True)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    dood_url = db.Column(db.String(500), nullable=False)
    thumbnail_url = db.Column(db.String(500))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    views = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

# Buat database dan tabel
with app.app_context():
    db.create_all()

# Admin routes
@app.route('/admin')
def index():
    videos = Video.query.order_by(Video.date_added.desc()).all()
    return render_template('index.html', videos=videos, now=datetime.now())

@app.route('/admin/categories')
def categories():
    categories = Category.query.order_by(Category.name).all()
    return render_template('categories.html', categories=categories, now=datetime.now())

@app.route('/admin/categories/add', methods=['POST'])
def add_category():
    name = request.form.get('name')
    if name:
        if Category.query.filter_by(name=name).first():
            flash('Kategori sudah ada!', 'error')
        else:
            category = Category(name=name)
            db.session.add(category)
            db.session.commit()
            flash('Kategori berhasil ditambahkan!', 'success')
    return redirect(url_for('categories'))

@app.route('/admin/categories/delete/<int:id>')
def delete_category(id):
    category = Category.query.get_or_404(id)
    if category.videos:
        flash('Tidak dapat menghapus kategori yang masih memiliki video!', 'error')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Kategori berhasil dihapus!', 'success')
    return redirect(url_for('categories'))

@app.route('/admin/add', methods=['GET', 'POST'])
def add_video():
    if request.method == 'POST':
        title = request.form['title']
        dood_url = request.form['dood_url']
        description = request.form['description']
        thumbnail_url = request.form.get('thumbnail_url', '').strip()
        category_id = request.form.get('category_id')
        
        if not title or not dood_url:
            flash('Judul dan URL harus diisi!', 'error')
            return redirect(url_for('add_video'))
        
        # Clean up URL
        dood_url = dood_url.strip()
        
        new_video = Video(
            title=title, 
            dood_url=dood_url, 
            description=description,
            category_id=category_id if category_id else None
        )
        
        # Check thumbnail URL first
        if thumbnail_url and is_valid_image_url(thumbnail_url):
            new_video.thumbnail_url = thumbnail_url
        # If no valid thumbnail URL, check for uploaded file
        elif 'thumbnail' in request.files:
            file = request.files['thumbnail']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                new_video.thumbnail_url = url_for('static', filename=f'thumbnails/{filename}')
        
        db.session.add(new_video)
        db.session.commit()
        flash('Video berhasil ditambahkan!', 'success')
        return redirect(url_for('index'))
    
    categories = Category.query.order_by(Category.name).all()
    return render_template('add.html', categories=categories, now=datetime.now())

@app.route('/admin/delete/<int:id>')
def delete_video(id):
    video = Video.query.get_or_404(id)
    
    # Delete thumbnail file if it's a local file
    if video.thumbnail_url and 'thumbnails/' in video.thumbnail_url:
        try:
            thumbnail_path = os.path.join(app.root_path, 'static', video.thumbnail_url.split('/static/')[1])
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        except Exception as e:
            print(f"Error deleting thumbnail: {e}")
    
    db.session.delete(video)
    db.session.commit()
    flash('Video berhasil dihapus!', 'success')
    return redirect(url_for('index'))

# Public routes
@app.route('/')
def public_index():
    latest_videos = Video.query.order_by(Video.date_added.desc()).limit(8).all()
    categories = Category.query.all()
    return render_template('public/index.html', latest_videos=latest_videos, categories=categories, now=datetime.now())

@app.route('/category/<int:id>')
def public_category(id):
    category = Category.query.get_or_404(id)
    videos = Video.query.filter_by(category_id=id).order_by(Video.date_added.desc()).all()
    return render_template('public/category.html', category=category, videos=videos, now=datetime.now())

@app.route('/watch/<int:id>')
def public_watch(id):
    video = Video.query.get_or_404(id)
    # Increment view count
    video.views += 1
    db.session.commit()
    return redirect(video.dood_url)

@app.route('/search')
def public_search():
    query = request.args.get('q', '')
    if query:
        videos = Video.query.filter(Video.title.ilike(f'%{query}%')).order_by(Video.date_added.desc()).all()
    else:
        videos = []
    return render_template('public/search.html', videos=videos, query=query, now=datetime.now())

@app.route('/latest')
def public_latest():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = Video.query.order_by(Video.date_added.desc()).paginate(page=page, per_page=per_page)
    return render_template('public/latest.html', pagination=pagination, now=datetime.now())

if __name__ == '__main__':
    # Development
    if os.environ.get('FLASK_ENV') == 'development':
        app.run(debug=True)
    # Production
    else:
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
