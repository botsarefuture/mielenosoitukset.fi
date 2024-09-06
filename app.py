from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = "your_secret_key"  # Change this to a secure secret key

# Connect to MongoDB
client = MongoClient(
    "mongodb://SMHV:SMHVisBEST2023!IsITreally%3F@10.0.0.4:27017/?directConnection=true&authMechanism=DEFAULT"
)
db = client["protest_database"]

# MongoDB collections
protests = db.protests
organizations = db.organizations
topics = db.topics
users = db.users


# Before request function to check authentication and admin rights
@app.before_request
def check_admin_rights():
    if request.path.startswith("/admin"):
        user_id = session.get("user")
        if not user_id:
            # Redirect to login if not logged in
            return redirect(url_for("login"))

        user = users.find_one({"_id": ObjectId(user_id)})
        if not user or not user.get("admin"):
            # Redirect to login if not admin
            return redirect(url_for("login"))


# USERS
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = users.find_one({"username": username})

        if user and check_password_hash(user["password"], password):
            # Log in successful, store user in session
            session["user"] = str(user["_id"])
            return redirect(url_for("index"))
        else:
            # Log in failed, show an error message
            return render_template("login.html")

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password == confirm_password:
            hashed_password = generate_password_hash(password)

            new_user = {"username": username, "password": hashed_password}
            users.insert_one(new_user)

            # Redirect to login page after successful signup
            return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/logout")
def logout():
    # Log out by clearing the session
    session.clear()
    return redirect(url_for("index"))


# ORGANIZATIONS


@app.route("/organizations")
def show_organizations():
    all_organizations = list(organizations.find())
    return render_template("organizations.html", organizations=all_organizations)


@app.route("/organizations/<organization_id>")
def show_organization(organization_id):
    organization = organizations.find_one({"_id": ObjectId(organization_id)})
    demonstrations = list(
        protests.find(
            {"organization._id": {"$in": [ObjectId(organization_id), organization_id]}}
        )
    )
    return render_template(
        "organization.html", organization=organization, demonstrations=demonstrations
    )


# TOPICS


@app.route("/topics")
def show_topics():
    all_topics = list(topics.find())
    return render_template("topics.html", topics=all_topics)


@app.route("/topics/<topic_id>")
def show_topic(topic_id):
    topic = topics.find_one({"_id": ObjectId(topic_id)})
    return render_template("topic.html", topic=topic)


# Route to display all demonstrations for a specific topic
@app.route("/demonstrations_by_topic/<topic_id>")
def demonstrations_by_topic(topic_id):
    # Retrieve demonstrations for the specified topic from the database
    demonstrations = list(protests.find({"topic._id": ObjectId(topic_id)}))

    # Get the topic name for displaying in the template
    topic = topics.find_one({"_id": ObjectId(topic_id)})

    return render_template(
        "demonstrations_by_topic.html", topic=topic, demonstrations=demonstrations
    )


# ADMIN PANEL


# Admin panel routes
@app.route("/admin")
def admin_panel():
    return render_template("admin/admin_panel.html")


# ... (Previous code)


# New route for managing protests
@app.route("/admin/manage_protests", methods=["GET", "POST"])
def manage_protests():
    all_protests = list(protests.find())
    all_organizations = list(organizations.find())
    all_topics = list(topics.find())

    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            # Retrieve the organization and topic IDs based on their names
            organization = organizations.find_one(
                {"_id": ObjectId(request.form["new_organization"])}
            )
            topic = topics.find_one({"_id": ObjectId(request.form["new_topic"])})

            new_protest_data = {
                "name": request.form["new_name"],
                "time": request.form["new_time"],
                "location": request.form["new_location"],
                "city": request.form["new_city"],
                "organization": organization,
                "topic": topic,
            }
            protests.insert_one(new_protest_data)
        elif action == "modify":
            protest_id = ObjectId(request.form["protest_id"])
            updated_protest_data = {
                "name": request.form["updated_name"],
                "time": request.form["updated_time"],
                "location": request.form["updated_location"],
                "city": request.form["updated_city"],
                "organization": ObjectId(request.form["updated_organization"]),
                "topic": ObjectId(request.form["updated_topic"]),
            }
            protests.update_one({"_id": protest_id}, {"$set": updated_protest_data})
        elif action == "delete":
            protest_id = ObjectId(request.form["protest_id"])
            protests.delete_one({"_id": protest_id})

        return redirect(url_for("manage_protests"))

    return render_template(
        "admin/manage_protests.html",
        protests=all_protests,
        organizations=all_organizations,
        topics=all_topics,
    )


# New route for managing organizations
@app.route("/admin/manage_organizations", methods=["GET", "POST"])
def manage_organizations():
    all_organizations = list(organizations.find())

    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            new_organization_name = request.form["new_organization_name"]
            organizations.insert_one({"name": new_organization_name})
        elif action == "modify":
            organization_id = request.form["organization_id"]
            updated_organization_name = request.form["updated_organization_name"]
            organizations.update_one(
                {"_id": organization_id}, {"$set": {"name": updated_organization_name}}
            )
        elif action == "delete":
            organization_id = request.form["organization_id"]
            organizations.delete_one({"_id": organization_id})

        return redirect(url_for("manage_organizations"))

    return render_template(
        "admin/manage_organizations.html", organizations=all_organizations
    )


# New route for managing topics
@app.route("/admin/manage_topics", methods=["GET", "POST"])
def manage_topics():
    all_topics = list(topics.find())

    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            new_topic_name = request.form["new_topic_name"]
            topics.insert_one({"name": new_topic_name})
        elif action == "modify":
            topic_id = request.form["topic_id"]
            updated_topic_name = request.form["updated_topic_name"]
            topics.update_one({"_id": topic_id}, {"$set": {"name": updated_topic_name}})
        elif action == "delete":
            topic_id = request.form["topic_id"]
            topics.delete_one({"_id": topic_id})

        return redirect(url_for("manage_topics"))

    return render_template("admin/manage_topics.html", topics=all_topics)


# Add a new protest, organization, or topic
@app.route("/admin/add", methods=["GET", "POST"])
def add_data():
    if request.method == "POST":
        collection_name = request.form["collection"]
        data = {
            "time": request.form["time"],
            "location": request.form["location"],
            "organization": request.form["organization"],
            "topic": request.form["topic"],
        }

        if collection_name == "protests":
            protests.insert_one(data)
            # Redirect to the manage_protests page after adding a new protest
            return redirect(url_for("manage_protests"))
        elif collection_name == "organizations":
            organizations.insert_one({"name": data["organization"]})
        elif collection_name == "topics":
            topics.insert_one({"name": data["topic"]})

    return redirect(url_for("admin_panel"))


# New route for adding a protest
@app.route("/admin/add_protest", methods=["GET", "POST"])
def add_protest():
    return render_template("admin/add_protests.html")


# New route for managing users
# New route for managing users
@app.route("/admin/manage_users", methods=["GET", "POST"])
def manage_users():
    all_users = list(users.find())

    if request.method == "POST":
        action = request.form.get("action")
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        admin = "admin" in request.form
        organizations = [
            org.strip() for org in request.form.get("organizations", "").split(",")
        ]

        if action == "create" and password == confirm_password:
            hashed_password = generate_password_hash(password)
            new_user = {
                "username": username,
                "email": email,
                "password": hashed_password,
                "admin": admin,
                "organizations": organizations,
            }
            users.insert_one(new_user)
        elif action == "modify":
            selected_user_id = request.form.get("selected_user")
            if selected_user_id:
                # Logic to modify user, update user document in the database
                selected_user = users.find_one({"_id": ObjectId(selected_user_id)})
                if selected_user:
                    # Update user fields based on the form data
                    selected_user["username"] = username
                    selected_user["email"] = email
                    selected_user["admin"] = admin
                    selected_user["organizations"] = organizations

                    # If a new password is provided, update the password
                    if password:
                        hashed_password = generate_password_hash(password)
                        selected_user["password"] = hashed_password

                    # Update the user document in the database
                    users.update_one(
                        {"_id": ObjectId(selected_user_id)}, {"$set": selected_user}
                    )
        elif action == "delete":
            selected_user_id = request.form.get("selected_user")
            if selected_user_id:
                # Logic to delete user, remove user document from the database
                users.delete_one({"_id": ObjectId(selected_user_id)})

        # Refresh the user list after modification
        all_users = list(users.find())

    return render_template("admin/manage_users.html", users=all_users)


# DEMOS
@app.route("/")
def index():
    all_protests = list(protests.find())
    return render_template("index.html", upcoming_protests=all_protests)


# Route for demonstration info page
@app.route("/demonstration/<demonstration_id>")
def demonstration_info(demonstration_id):
    demonstration = protests.find_one({"_id": ObjectId(demonstration_id)})
    print(demonstration)
    return render_template("demonstration_info.html", demonstration=demonstration)


if __name__ == "__main__":
    app.run(debug=True)
