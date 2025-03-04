import os
import subprocess
import datetime
from flask import Flask, render_template, request, redirect, url_for
import pymongo 
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

def start_docker_compose():
    try:
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        print(" * Docker containers started successfully!")
    except subprocess.CalledProcessError as e:
        print(" * Error starting Docker containers:", e)
        print(" * Output:", e.output)
        print(" * Return code:", e.returncode)
#start_docker_compose()
def create_app(): 
    app = Flask(__name__, static_folder='static')
    app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
    
    # Load environment variables
    load_dotenv()
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    class User(UserMixin):
        def __init__(self, id, username):
            self.id = id
            self.username = username

    @login_manager.user_loader
    def load_user(user_id):
        db = app.config["db"]
        if db is not None:
            user_data = db.users.find_one({"_id": ObjectId(user_id)})
            if user_data:
                return User(user_id, user_data["username"])
        return None
    
    # Start Docker containers
    # 
    
    # MongoDB connection with error handling
    try:
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise ValueError("MONGO_URI not found in environment variables")
            
        db_name = os.getenv("MONGO_DBNAME")
        if not db_name:
            raise ValueError("MONGO_DBNAME not found in environment variables")
            
        cxn = pymongo.MongoClient(mongo_uri)
        db = cxn[db_name]
        cxn.admin.command("ping")
        print(" *", "Connected to MongoDB!")
        
    except Exception as e: 
        print(" * MongoDB connection error:", e)
        db = None
    
    # Store db connection in app config
    app.config["db"] = db
    
    @app.route("/")
    @login_required
    def home():
        return render_template('Home.html', username=current_user.username)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            db = app.config["db"]
            if db is not None:
                user_data = db.users.find_one({"username": username})
                if user_data and check_password_hash(user_data["password"], password):
                    user = User(id=str(user_data["_id"]), username=username)
                    login_user(user)
                    return redirect(url_for('home'))
                else:
                    return render_template('login.html', error="Invalid credentials")
        return render_template('login.html')

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            db = app.config["db"]
            if db is not None:
                existing_user = db.users.find_one({"username": username})
                if existing_user:
                    return render_template('signup.html', error="User already exists")
                hashed_password = generate_password_hash(password)
                db.users.insert_one({"username": username, "password": hashed_password})
                return redirect(url_for('onboard'))#return redirect(url_for('onboarding'))
        return render_template('signup.html')

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route("/workouts", methods=["GET", "POST"])
    @login_required
    def workouts():
        db = app.config["db"]
        sort_order = request.form.get("sort_order", "desc")
        sort_by = request.form.get("sort_by", "created_at")
        sort_direction = -1 if sort_order == "desc" else 1
        docs = db.messages.find({"dbType": "Workouts", "user": current_user.username}).sort(sort_by, sort_direction)
        return render_template('Workouts.html', docs=docs, sort_order=sort_order, sort_by=sort_by)
    
    @app.route("/diets", methods=["GET", "POST"])
    @login_required
    def diets():
        db = app.config["db"]
        sort_order = request.form.get("sort_order", "desc")
        sort_by = request.form.get("sort_by", "created_at")
        sort_direction = -1 if sort_order == "desc" else 1
        docs = db.messages.find({"dbType": "diet", "user": current_user.username}).sort(sort_by, sort_direction)
        return render_template('Diet.html', docs=docs, sort_order=sort_order, sort_by=sort_by)
    
    @app.route("/settings")
    @login_required
    def settings():
        db = app.config['db']
        if db is not None:
            week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            workout_goals = {}
            for day in week:
                goal = db.messages.find_one({"dbType": 'workout_goal', 'user': current_user.username, 'day': day})
                workout_goals[day] = goal['workout_type'] if goal else None

            diet_goals = db.messages.find_one({"dbType": 'diet_goal', 'user': current_user.username})

            return render_template('Settings.html', workout_goals=workout_goals, diet_goals=diet_goals)
    
    @app.route("/setting", methods = ["POST"])
    @login_required
    def setting():
        db=app.config['db']
        if db is not None:
            week = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
            for day in week:
                workout_data = {
                    "day": day,
                    "workout_type": request.form.get(day),
                    "dbType": "workout_goal",
                    "user": current_user.username
                }
                db.messages.update_one(
                    {"user": current_user.username, "dbType":"workout_goal", "day": day},
                    {"$set": workout_data},
                    upsert=True
                )
            
            diet_data={
                'calories': request.form.get('calories'),
                'protein': request.form.get('protein'),
                'carbohydrates': request.form.get('carbohydrates'),
                'fat': request.form.get('fat'),
                "dbType": "diet_goal",
                "user": current_user.username
            }
            db.messages.update_one(
                {'dbType': 'diet_goal', 'user': current_user.username},
                {"$set": diet_data},
                upsert=True
            )
        return redirect(url_for('home'))
    
    @app.route("/add_workout")
    @login_required
    def add_workout():
        return render_template("addWorkout.html")
    
    @app.route("/add_diet")
    @login_required
    def add_diet():
        return render_template("addMeal.html")
    
    @app.route("/onboard")
    def onboard():
        return render_template("Onboarding.html")
    
    @app.route("/onboarding", methods = ["POST"])
    @login_required
    def onboarding():
        db = app.config['db']
        if db:
            week = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
            
            for day in week:
                workout_data = {
                    "day" : day,
                    "workout_type": request.form.get(day),
                    "dbType": "workout_goal",
                    "user": current_user.username
                }
                db.messages.insert_one(workout_data)
        
            diet_data = {
                "calories": request.form.get("calories"),
                "protein": request.form.get("protein"),
                "carbohydrates": request.form.get("carbohydrates"),
                "fat": request.form.get("fat"),
                "dbType": "diet_goal",
                "user": current_user.username
            }
            db.messages.insert_one(diet_data)

        return redirect(url_for('login'))

    
    @app.route("/showBoth")
    @login_required
    def showBoth():
        # Add correct Database call (get all docs in the database to display)
        db = app.config['db']
        if db is not None:
            docs = list(db.messages.find({"user": current_user.username}))
        return render_template('showBothScreen' , docs = docs) # Add the correct name for template

    @app.route("/create/<dbType>" , methods=["POST"])
    @login_required
    def create_post(dbType):
        db = app.config['db']
        if db is not None:
            if request.form.get("time") == "":
                    time = datetime.datetime.utcnow() - datetime.timedelta(hours=5)
            else: 
                time = datetime.datetime.strptime(request.form.get("time"), "%Y-%m-%d")

            if dbType == 'Diet': #would it be called diet
                data = {
                    "meal_name": request.form.get("meal_name"),
                    "time" : request.form.get("time"), 
                    "calories": request.form.get("calories"),
                    "protein": request.form.get("protein"),
                    "carbohydrates": request.form.get("carbohydrates"),
                    "fat": request.form.get("fat"),
                    "date": time,
                    "created_at": datetime.datetime.utcnow(),
                    "dbType": "diet",
                    "user": current_user.username
                }
                db.messages.insert_one(data)
                return redirect(url_for('diets'))
            elif dbType == 'Workouts': #same question as above
                data = {
                    "workout_description": request.form.get("Workout"),
                    "workout_type": request.form.get("WorkoutType"),
                    "date": time,
                    "created_at": datetime.datetime.utcnow(),
                    "dbType": "Workouts",
                    "user": current_user.username
                }
                db.messages.insert_one(data)
                return redirect(url_for('workouts'))
                
        # Get the values from the fields 
        # Make a document and import it into the Database

    @app.route("/edit/<post_id>")
    @login_required
    def edit(post_id): 
        # Add correct Database call (Find the document from Database from the post_id)
        db = app.config["db"]
        if db is not None:
            docs = db.messages.find_one({"_id": ObjectId(post_id), "user": current_user.username})
        return render_template('editDocument', docs=docs) # Add the correct name for template

    @app.route("/edit/<post_id>/<dbType>" , methods = ["POST"])
    @login_required
    def edit_post(post_id, dbType):
        # Get the values from the fields 
        # Make a document and import it into the Database
        db = app.config["db"]
        if db is not None:
            if dbType == 'Diet': 
                updated_data = {
                    "meal_name": request.form.get("meal_name"),
                    "date_time": request.form.get("datetime"),
                    "calories": request.form.get("calories"),
                    "protein": request.form.get("protein"),
                    "carbohydrates": request.form.get("carbohydrates"),
                    "fat": request.form.get("fat"),
                    "dbType": "diet",
                    "user": current_user.username
                }
            elif dbType == 'Workouts': 
                updated_data = {
                    "date_time": request.form.get("datetime"),
                    "workout_type": request.form.get("workout_type"),
                    "dbType": "Workouts",
                    "user": current_user.username
                }
            db.messages.update_one({"_id": ObjectId(post_id)}, {"$set": updated_data})
        return redirect(url_for('showBoth'))

    @app.route("/deleteWorkout/<post_id>")
    @login_required
    def deleteWorkout(post_id):
        # Delete the document from the Database
        db = app.config["db"]
        if db is not None:
            db.messages.delete_one({"_id": ObjectId(post_id), "user": current_user.username})
        return redirect(url_for('workouts'))
    
    @app.route("/deleteDiet/<post_id>")
    @login_required
    def deleteDiet(post_id):
        # Delete the document from the Database
        db = app.config["db"]
        if db is not None:
            db.messages.delete_one({"_id": ObjectId(post_id), "user": current_user.username})
        return redirect(url_for('diets'))

    @app.route("/delete_all_data", methods=["POST"])
    @login_required
    def delete_all_data():
        db = app.config["db"]
        if db is not None:
            db.messages.delete_many({"user": current_user.username})
        return redirect(url_for('home'))

    @app.errorhandler(Exception)
    def handle_error(e): 
        return render_template("error.html", error=e)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)