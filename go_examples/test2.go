package main

import (
	"errors"
	"fmt"
	"math"
)

func main() {
	fmt.Println(SaveDivide(10, 0))
	fmt.Println(SaveDivide(10, 10))

	result, err := Sqrt(-64)
	if err != nil {
		fmt.Println(err)
	} else {
		fmt.Println(result)
	}
	result, err = Sqrt(64)
	if err != nil {
		fmt.Println(err)
	} else {
		fmt.Println(result)
	}
	greet, name := Greeting("Srinivasan")
	fmt.Println(greet + name)

	defer print1("Mrinalini Srinivasan")
	print1("Mridula Srinivasan")

}
func SaveDivide(num1, num2 int) int {
	defer func() {
		fmt.Println(recover())
	}()
	quotient := num1 / num2
	return quotient
}

func Sqrt(value float64) (float64, error) {
	if value < 0 {
		return 0, errors.New("Math: negative number passed to Sqrt")
	}
	return math.Sqrt(value), nil
}

func Greeting(value string) (string, string) {
	return "Hello World,", value
}

func print1(s string) {
	fmt.Println(s + "\n")
}
