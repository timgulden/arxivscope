import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

DB_NAME = os.getenv('DOC_TROVE_DB', 'doctrove')
DB_USER = os.getenv('DOC_TROVE_USER', 'doctrove_admin')
DB_PASSWORD = os.getenv('DOC_TROVE_PASSWORD', 'MOUn47!')
DB_HOST = os.getenv('DOC_TROVE_HOST', 'localhost')
DB_PORT = int(os.getenv('DOC_TROVE_PORT', 5434)) 