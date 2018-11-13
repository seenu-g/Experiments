package main

import (
	"fmt"
	"math"
)

//Function values may be used as function arguments and return values.

func compute(fn func(float64, float64) float64) float64 {
	return fn(3, 4)
}

func FibonacciRecursion(n int) int {
	if n <= 1 {
		return n
	}
	return FibonacciRecursion(n-1) + FibonacciRecursion(n-2)
}

func main() {
	hypot := func(x, y float64) float64 {
		return math.Sqrt(x*x + y*y)
	}
	fmt.Println(hypot(5, 12))

	fmt.Println(compute(hypot))
	fmt.Println(math.Pow)
	fmt.Println(compute(math.Pow))

	for i := 0; i <= 19; i++ {
		fmt.Printf("%d  ", FibonacciRecursion(i))
	}
	fmt.Println("")

}
