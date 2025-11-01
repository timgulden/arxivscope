import psycopg2
import uuid
from datetime import date

# Connection parameters (adjust if needed)
DB_NAME = 'doctrove'
DB_USER = 'tgulden'
DB_HOST = 'localhost'
DB_PORT = 5434

# Generate a test UUID
paper_id = str(uuid.uuid4())

try:
    # Connect to the database
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, host=DB_HOST, port=DB_PORT)
    conn.autocommit = True
    cur = conn.cursor()
    print('Connected to PostgreSQL!')

    # Insert a test record
    print('Inserting test record...')
    cur.execute('''
        INSERT INTO doctrove_papers (
            doctrove_paper_id, doctrove_source, doctrove_source_id, doctrove_title, doctrove_abstract, doctrove_authors, doctrove_primary_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (doctrove_source, doctrove_source_id) DO NOTHING;
    ''', (
        paper_id,
        'testsource',
        'testid123',
        'Test Paper Title',
        'This is a test abstract.',
        ['Alice', 'Bob'],
        date.today()
    ))

    # Query the record back
    print('Querying test record...')
    cur.execute('SELECT doctrove_paper_id, doctrove_title, doctrove_authors, doctrove_primary_date FROM doctrove_papers WHERE doctrove_paper_id = %s;', (paper_id,))
    row = cur.fetchone()
    print('Fetched row:', row)

    # Clean up (delete test record)
    cur.execute('DELETE FROM doctrove_papers WHERE doctrove_paper_id = %s;', (paper_id,))
    print('Test record deleted.')

    cur.close()
    conn.close()
    print('Connection closed.')

except Exception as e:
    print('Error:', e) 