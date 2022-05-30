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

	c := make(chan string)
	fmt.Println("main() started")

	go display(c)
	c <- "John"

	go display(c)
	c <- "Srini"

	fmt.Println("main() stopped")
}
