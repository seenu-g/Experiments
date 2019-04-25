package main

import "fmt"

func display(roc <-chan string) {
	fmt.Println("Hello " + <-roc + "!")
}

func main() {
	roc := make(<-chan int)
	soc := make(chan<- int)

	fmt.Printf("Data type of roc is `%T`\n", roc)
	fmt.Printf("Data type of soc is `%T\n", soc)

	fmt.Println("main() started")
	c := make(chan string)

	go display(c)
	c <- "John"

	fmt.Println("main() stopped")
}
