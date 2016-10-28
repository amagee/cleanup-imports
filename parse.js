var esprima = require('esprima');

var content = '';
process.stdin.resume();
process.stdin.on('data', function(buf) { content += buf.toString(); });
process.stdin.on('end', function() {
  console.log(
    JSON.stringify(
      esprima.parse(
        content, {
          sourceType: 'module',
          jsx: true
        }
      ), 
      null, 
      4
    )
  );
});
