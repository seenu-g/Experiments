package main

import (
	"fmt"
	"math/rand"
	"time"
)

func thread(n int) {
	for i := 0; i < 10; i++ {
		fmt.Println(n, ":", i)
		amt := time.Duration(rand.Intn(250))
		time.Sleep(time.Millisecond * amt)
	}
}
func thread2() {
	for i := 0; i < 10; i++ {
		fmt.Println(5, ":", i)
		amt := time.Duration(rand.Intn(250))
		time.Sleep(time.Millisecond * amt)
	}
}
func main() {

	go thread(1)
	go thread2()
	fmt.Println("main thread")
	var input string
	fmt.Scanln(&input)
}
