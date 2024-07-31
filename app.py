from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__, static_folder='static')
app.config ['SESSION_COOKIE_SECURE'] = True
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a random secret key
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'notes')
app.config['ALLOWED_EXTENSIONS'] = {'txt'}

# Add this new function for www redirect
@app.before_request
def redirect_to_www_and_https():
    """Redirect non-www requests to www and HTTP to HTTPS."""
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        if not request.host.startswith('www.'):
            url = url.replace('https://', 'https://www.', 1)
        return redirect(url, code=301)
    elif not request.host.startswith('www.'):
        url = request.url.replace('https://', 'https://www.', 1)
        return redirect(url, code=301)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"Error rendering template: {e}")
        abort(500)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'hveno' and check_password_hash(generate_password_hash('FlOyd!7275'), password):
            user = User(username)
            login_user(user)
            return redirect(url_for('notes'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('notes'))

@app.route('/notes')
def notes():
    notes_dir = os.path.join(app.root_path, 'notes')
    notes_files = [f for f in os.listdir(notes_dir) if f.endswith('.txt')]
    notes_files.sort(key=lambda x: os.path.getmtime(os.path.join(notes_dir, x)), reverse=True)
    return render_template('notes.html', notes_files=notes_files)

@app.route('/notes/<filename>')
def serve_note(filename):
    notes_dir = os.path.join(app.root_path, 'notes')
    file_path = os.path.join(notes_dir, filename)
    if not os.path.exists(file_path) or not filename.endswith('.txt'):
        abort(404)
    with open(file_path, 'r') as file:
        content = file.read()
    return render_template('note_template.html', content=content, title=filename.replace('.txt', '').replace('-', ' ').title())

@app.route('/edit/<filename>', methods=['GET', 'POST'])
@login_required
def edit_note(filename):
    notes_dir = os.path.join(app.root_path, 'notes')
    # Find the file regardless of case
    real_filename = next((f for f in os.listdir(notes_dir) if f.lower() == filename.lower()), None)
    if not real_filename:
        abort(404)
    file_path = os.path.join(notes_dir, real_filename)
    
    if request.method == 'POST':
        content = request.form['content']
        try:
            with open(file_path, 'w') as file:
                file.write(content)
            return redirect(url_for('serve_note', filename=real_filename))
        except IOError:
            return "Error saving the file", 500
    
    with open(file_path, 'r') as file:
        content = file.read()
    return render_template('edit_note.html', content=content, title=real_filename.replace('.txt', '').replace('-', ' ').title(), filename=real_filename)

@app.route('/new_note', methods=['GET', 'POST'])
@login_required
def new_note():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        filename = secure_filename(title.replace(' ', '-').lower() + '.txt')
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if os.path.exists(file_path):
            return "A note with this title already exists. Please choose a different title.", 400
        
        with open(file_path, 'w') as file:
            file.write(content)
        
        return redirect(url_for('serve_note', filename=filename))
    
    return render_template('new_note.html')

if __name__ == '__main__':
    app.run(debug=True)