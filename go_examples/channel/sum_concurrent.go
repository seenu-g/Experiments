package main

import "fmt"

func sum(s []int, mychannel chan int) {
	sum := 0
	for _, v := range s {
		sum += v
	}
	mychannel <- sum // send sum to channel
}

func main() {
	s := []int{7, -2, 8, 9, 4, 5, 1, 6, 11, 16, -5, 10}

	//  compute the sum of numbers in an array.
	mychannel := make(chan int)
	//split the array among two goroutines and find the sum of the two array slices concurrently
	go sum(s[:len(s)/2], mychannel)
	go sum(s[len(s)/2:], mychannel)

	x := <-mychannel // receive from mychannel
	y := <-mychannel // receive from mychannel

	fmt.Println("Sum computed in first goroutine: ", x)
	fmt.Println("Sum computed in second goroutine: ", y)

	fmt.Println("Total sum: ", x+y)

}
