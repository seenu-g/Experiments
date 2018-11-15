package main

import (
	"fmt"
	"math"
)

type MyFloat float64
func (f MyFloat) Abs() float64 {
	if f < 0 {
		return float64(-f)
	}
	return float64(f)
}

type StringBuilder string
func(str StringBuilder) len() int {
	return len(str)
}
func(str StringBuilder) display()  {
	fmt.Println(str)
}

func main() {
	f := MyFloat(-math.Sqrt2)
	fmt.Println(f.Abs())

	s := StringBuilder("Hello world")
	fmt.Println(s.len())
	s.display();

}