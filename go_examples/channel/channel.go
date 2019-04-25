package main

import "fmt"

func greet1(c chan string) {
	fmt.Println("Hello1 " + <-c + "!")
}
func greet2(c chan string) {
	fmt.Println("Hello2 " + <-c + "!")
}

//Channels allow for safe communication between different threads in a Go program.
func main() {
	var c chan int
	fmt.Print(c) // zero-value of channel is nil

	channel1 := make(chan string)
	go greet2(channel1)
	go greet1(channel1) // when one of them is unblocked, the next command runs.
	channel1 <- "John"  //goroutine is blocked until some goroutine reads it

	d := make(chan int)
	fmt.Printf("type of `d` is %T\n", d)
	fmt.Printf("value of `d` is %v\n", d)

	/* the below code witll result in to deadlock exception
	/* if there is no other goroutines available, imagine all of them are sleeping */
	/*	fmt.Println("main() started")
		a := make(chan string)
		a <- "John"
		fmt.Println("main() stopped") */

	/* this will result in to [painic exeception as values are fed in to closed channel */
	/* fmt.Println("main() started")
	b := make(chan string, 1)
	go greet(b)
	b <- "John"
	close(b) // closing channel
	b <- "Mike"
	fmt.Println("main() stopped") */

	/*fmt.Println("main() started")
	num := make(chan int)
	go squares(num) // start goroutine
	// periodic block/unblock of main goroutine until chanel closes
	for {
		val, ok := <-num
		if ok == false {
			fmt.Println(val, ok, "<-- loop broke!")
			break // exit break loop
		} else {
			fmt.Println(val, ok) // prints value and channel status
		}
	}
	fmt.Println("main() stopped") */

	fmt.Println("main() started")
	num := make(chan int, 3) //channel has buffer capacity of 3
	go open_squares(num)
	fmt.Printf("Length and capacity of channel num is %v %v \n", len(num), cap(num))
	num <- 1
	num <- 2
	num <- 3
	num <- 4 // blocks here // if you comment this, channel does not overflow and nothing prints
	num <- 5
	fmt.Println("main() stopped")

	/*channel has length and capacity.
	Length is number of values queued (unread) in channel buffer
	capacity is the buffer size. To calculate length, we use len function
	to find out capacity, we use cap function, just like a slic */
	fmt.Printf("Length and capacity of channel num is %v %v  \n", len(num), cap(num))
}
func open_squares(c chan int) {
	for i := 0; i <= 3; i++ {
		num := <-c
		fmt.Println(num * num)
	}
}

func squares(n chan int) {
	for i := 0; i <= 9; i++ {
		n <- i * i
	}
	close(n) // close channel
	// if this gets missed, fatal error: all goroutines are asleep - deadlock!
}
