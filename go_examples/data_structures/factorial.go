package main

import (
	"fmt"
)

func main() {
	fmt.Print("Enter number to find factorial: ")
	var input int
	fmt.Scanln(&input)

	fmt.Println(factorial(input))
}

func factorial(num int) int {
	if num == 0 {
		return 1
	}
	return num * factorial(num-1)
}
