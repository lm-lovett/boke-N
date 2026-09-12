from workers import asgi

from app.factory import create_app

app = create_app()
Default = asgi.entrypoint(app)
