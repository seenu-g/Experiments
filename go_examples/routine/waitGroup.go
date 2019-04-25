package main

import (
	"fmt"
	"sync"
	"time"
)

func slave(wg *sync.WaitGroup, instance int) {
	fmt.Println("Service called on slave instance ", instance)
	wg.Done() // decrement counter for master
}
func master(wg *sync.WaitGroup, instance int) {
	time.Sleep(2 * time.Second)
	fmt.Println("Service called on master instance", instance)
	go slave(wg, instance)
}

func main() {
	fmt.Println("main() started")
	var wg sync.WaitGroup // create waitgroup (empty struct)

	for i := 1; i <= 3; i++ {
		wg.Add(1) // increment master counter for master
		go master(&wg, i)
	}
	// go master(&wg, 4) // As this is not added to waitGroup, it may print after main() stopped
	wg.Wait() // blocks here
	fmt.Println("main() stopped")
}
