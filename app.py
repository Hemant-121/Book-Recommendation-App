from flask import Flask, render_template, request, redirect, url_for, flash
from openai import OpenAI
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET-KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("SQLALCHEMY_DATABASE_URI")
db = SQLAlchemy(app)
login_manager = LoginManager(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    favorite_genre = db.Column(db.String(50))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and password == user.password:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('preferences'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    try:
        if request.method == 'POST':
            favorite_genre = request.form.get('favorite_genre')

            current_user.favorite_genre = favorite_genre

            db.session.commit()

            flash('Preferences updated successfully!', 'success')
            return redirect(url_for('recommendations'))

    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {str(e)}")
        flash('An error occurred while updating preferences. Please try again.', 'error')

    return render_template('preferences.html')

@app.route('/recommendations')
@login_required
def recommendations():
    try:

        if current_user.favorite_genre:

            user_preferences = current_user.favorite_genre

            client = OpenAI(
                api_key=os.environ.get('OPENAI_API_KEY')
            )

            openai_prompt = f"Generate book recommendations based on the {user_preferences} genre. Provide a list of books and author names"

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": openai_prompt}
                ]
            )
            
            recommendations = response.choices[0].message.content.split("\n")

            return render_template('recommendations.html', recommendations=recommendations)

        else:
            flash('User preferences not available. Please set preferences first.', 'warning')
            return redirect(url_for('preferences'))

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        flash('An error occurred while generating recommendations. Please try again.', 'error')

    return render_template('recommendations.html')



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
