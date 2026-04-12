import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from app.api.ingest import parse_incidents_csv

path = Path('sample_data/incidents-queue-20260411.csv')
content = path.read_bytes()
records = parse_incidents_csv(content)
print('records', len(records))
if records:
    print(records[0].dict())
