package main

import "fmt"

func square(c chan int) {
	fmt.Println("[square] reading")
	num := <-c
	c <- num * num
}

func cube(c chan int) {
	fmt.Println("[cube] reading")
	num := <-c
	c <- num * num * num
}

func example1(squareChan chan int, cubeChan chan int, testNum int) {
	fmt.Println("[main] sent testNum to squareChan")
	squareChan <- testNum
	fmt.Println("[main] resuming")

	fmt.Println("[main] sent testNum to cubeChan")
	cubeChan <- testNum
	fmt.Println("[main] resuming")

	fmt.Println("[main] reading from channels")
	squareVal, cubeVal := <-squareChan, <-cubeChan
	sum := squareVal + cubeVal
	fmt.Println("[main] sum of square and cube of", testNum, " is", sum)
	fmt.Println("[main] main() stopped")
}

func main() {
	fmt.Println("[main] main() started")

	squareChan := make(chan int)
	cubeChan := make(chan int)

	go square(squareChan)
	go cube(cubeChan)
	testNum := 3
	fmt.Println("[main] sent testNum ", testNum, " to example1")
	example1(squareChan, cubeChan, testNum)

	go square(squareChan)
	go cube(cubeChan)
	testNum = 4
	fmt.Println("[main] sent testNum ", testNum, " to example1")
	example1(squareChan, cubeChan, testNum)
}
