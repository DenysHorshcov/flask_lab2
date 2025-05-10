from app import create_app
from app.models import db  # ✅ absolute import
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
