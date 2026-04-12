const http = require('http');
const fs = require('fs');

// Try simple GET first to see if server works
const testReq = http.request({
  hostname: '127.0.0.1',
  port: 5000,
  path: '/health',
  method: 'GET'
}, (res) => {
  let body = '';
  res.on('data', chunk => body += chunk);
  res.on('end', () => console.log('Health:', body));
});
testReq.end();