from config import Config
from firebase_admin import initialize_app, db, credentials

cred = credentials.Certificate(Config.SERVICE_ACCOUNT_FILE)
initialize_app(cred, {"databaseURL": Config.FIREBASE_URL})

database = db.reference()
