from flask import Flask, send_from_directory

# Importação dos blueprints
from api.routes.transactions_routes import bp as transactions_bp
from api.routes.categories_routes import bp as categories_bp
from api.routes.summary_routes import bp as summary_bp
from api.routes.import_routes import bp as import_bp
from api.routes.splitwise_routes import bp as splitwise_bp
from api.routes.person_routes import bp as person_bp
from api.routes.dashboard_routes import bp as dashboard_bp

app = Flask(__name__)

# Registra os blueprints
app.register_blueprint(transactions_bp, url_prefix="/api/transactions")
app.register_blueprint(categories_bp, url_prefix="/api/categories")
app.register_blueprint(summary_bp, url_prefix="/api/summary")
app.register_blueprint(import_bp, url_prefix="/api/import")
app.register_blueprint(splitwise_bp, url_prefix="/api/splitwise")
app.register_blueprint(person_bp, url_prefix="/api/persons")
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")


@app.route("/")
def index():
    return send_from_directory("static", "home.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)


if __name__ == "__main__":
    app.run(debug=True)
