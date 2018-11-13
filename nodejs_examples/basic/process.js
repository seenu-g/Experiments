// Print the current directory
console.log('Current directory: ' + process.cwd());
// Print the process version
console.log('Current version: ' + process.version);
// Print the memory usage
console.log(process.memoryUsage());

// Getting executable path
console.log(process.execPath);

// Platform Information
console.log(process.platform);

process.stdout.write("Hello World!" + "\n");
console.log('Passed Parameters');
// Reading passed parameter
process.argv.forEach(function(val, index, array) {
    console.log(index + ': ' + val);
});