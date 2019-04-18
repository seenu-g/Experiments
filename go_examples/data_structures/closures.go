package main

import (
	"fmt"
	"sort"
)

var DoStuff func() = func() {
	// Do stuff
}

func RegFunc() { fmt.Println("reg func") }

func main() {

	number := 10
	squareNum := func() int {
		number *= number
		return number //  value of "number" gets updated due to this function
	}
	fmt.Println(squareNum())
	fmt.Println(squareNum())

	DoStuff()

	DoStuff = func() {
		fmt.Println("Doing stuff!")
	}
	DoStuff()

	DoStuff = func() {
		fmt.Println("Doing other stuff.")
	}
	DoStuff()

	DoStuff = RegFunc
	DoStuff()

	TestClosure()
}

func TestClosure() {
	numbers := []int{1, 11, -5, 8, 2, 0, 12}
	sort.Ints(numbers)
	fmt.Println("Sorted:", numbers)

	index1 := sort.SearchInts(numbers, 8)
	fmt.Println("7 is at index:", index1)

	index := sort.Search(len(numbers), func(i int) bool {
		return numbers[i] >= 7
	})
	fmt.Println("The first number >= 7 is at index:", index)
	fmt.Println("The first number >= 7 is:", numbers[index])
}
