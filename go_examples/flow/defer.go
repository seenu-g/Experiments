package main

import "fmt"
//A defer statement defers function execution until the surrounding function returns.
func printHelloWorld(){
	defer fmt.Println("world")

	fmt.Println("hello")
}
func printForLoop(){
	fmt.Println("counting")
	for i := 0; i < 10; i++ {
		defer fmt.Println(i)
	}
	fmt.Println("done")
}
//Deferred function calls are pushed onto a stack. When a function returns, its deferred calls are executed in last-in-first-out order
func main() {
	defer printHelloWorld();
	printForLoop();
}
