from flask import Flask, send_from_directory

# Importação dos blueprints
from api.routes.transactions_routes import bp as transactions_bp
from api.routes.categories_routes import bp as categories_bp
from api.routes.summary_routes import bp as summary_bp
from api.routes.import_routes import bp as import_bp
from api.routes.splitwise_routes import bp as splitwise_bp
from api.routes.person_routes import bp as person_bp
from api.routes.dashboard_routes import bp as dashboard_bp
from api.routes.overview_routes import bp as overview_bp
from api.routes.settings_routes import bp as settings_bp
from api.routes.finance_history_routes import bp as finance_history_bp
from api.routes.pluggy_routes import bp as pluggy_bp
from api.routes.database_routes import bp as database_bp
from api.routes.investments_routes import bp as investments_bp
from api.routes.recurrences_routes import bp as recurrences_bp

app = Flask(__name__)

# Registra os blueprints
app.register_blueprint(transactions_bp, url_prefix="/api/transactions")
app.register_blueprint(categories_bp, url_prefix="/api/categories")
app.register_blueprint(summary_bp, url_prefix="/api/summary")
app.register_blueprint(import_bp, url_prefix="/api/import")
app.register_blueprint(splitwise_bp, url_prefix="/api/splitwise")
app.register_blueprint(person_bp, url_prefix="/api/persons")
app.register_blueprint(settings_bp, url_prefix="/api/settings")
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
app.register_blueprint(overview_bp, url_prefix="/api/overview")
app.register_blueprint(finance_history_bp, url_prefix="/api/finance-history")
app.register_blueprint(pluggy_bp, url_prefix="/api/pluggy")
app.register_blueprint(database_bp, url_prefix="/api/database")
app.register_blueprint(investments_bp, url_prefix="/api/investments")
app.register_blueprint(recurrences_bp, url_prefix="/api/recurrences")


@app.route("/")
def index():
    return send_from_directory("static", "home.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)


if __name__ == "__main__":
    app.run(debug=True)
