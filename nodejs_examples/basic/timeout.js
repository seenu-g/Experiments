function printHello() {
    console.log("Hello, World!");
    console.timeEnd('Timer');
}
console.time("Timer");
// Now call above function after 2 seconds
setTimeout(printHello, 2000);

// Now clear the timer
//clearTimeout(t);