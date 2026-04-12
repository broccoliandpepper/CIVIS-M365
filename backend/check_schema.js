const sqlite3 = require('sqlite3');
const path = require('path');

const dbPath = path.join(__dirname, 'data', 'db', 'siem_hot.db');
console.log('Checking:', dbPath);

const db = new sqlite3.Database(dbPath, (err) => {
  if (err) console.error(err);
  else {
    db.all("PRAGMA table_info(audit_logs_m365)", [], (err, rows) => {
      if (err) console.error(err);
      else console.log('Columns:', rows.map(r => r.name));
      db.close();
    });
  }
});