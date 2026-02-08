import os
import couchdb
from dotenv import load_dotenv
load_dotenv()

COUCHDB_USER = os.getenv("COUCHDB_USER", "admin")
COUCHDB_PASSWORD = os.getenv("COUCHDB_PASSWORD", "password")
COUCHDB_URL = os.getenv("COUCHDB_URL", "http://127.0.0.1:5984/")

# Connect to CouchDB
server = couchdb.Server(f"http://{COUCHDB_USER}:{COUCHDB_PASSWORD}@{COUCHDB_URL.split('//')[1]}")

try:
    info = server.version()
    print("Connected to CouchDB, version:", info)
except Exception as e:
    print("Failed to connect to CouchDB:", e)

if "users" not in server:
    server.create("users")
userDB = server["users"]

if "projects" not in server:
    server.create("projects")
projectsDB = server["projects"]

if "ai_chat" not in server:
    server.create("ai_chat")
aiChatDB = server["ai_chat"]

if "drafts" not in server:
    server.create("drafts")
draftsDB = server["drafts"]

# This is for creating other DBs
# userdb = server["users"]
# messagedb = server["messages"]
# projectdb = server["projects"]