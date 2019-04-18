package main

import (
	"fmt"
	"runtime"
	"time"
)

func findType(i interface{}) {
	switch v := i.(type) {
	case int:
		fmt.Printf("Twice %v is %v\n", v, v*2)
	case string:
		fmt.Printf("%q is %v bytes long\n", v, len(v))
	default:
		fmt.Printf("I don't to identify type %T!\n", v)
	}
}
func findOS() {
	fmt.Print("Go is running on ")
	switch os := runtime.GOOS; os {
	case "darwin":
		fmt.Println("OS X.")
	case "linux":
		fmt.Println("Linux.")
	default:
		// freebsd, openbsd,
		// plan9, windows...
		fmt.Printf("%s.", os)
	}
}
func main() {

	findType(21)
	findType("hello")
	findType(true)
	findType(45.67)

	findOS()
	HowFar()
	TestFallThrough()
}

func TestFallThrough() {
	fmt.Print("Enter Number: ")
	var input int
	fmt.Scanln(&input)

	switch input {
	case 10:
		fmt.Print("the value is 10 \n")
	case 20:
		fmt.Print("the value is 20 \n")
	case 30:
		fmt.Print("the value is 30 \n ")
	case 40:
		fmt.Print("the value is 40 \n")
	case 1:
		fmt.Print("fallover to default")
		fallthrough
	default:
		fmt.Print(" It is not 10,20,30,40 \n ")
	}
}
func HowFar() {
	fmt.Println("When's Saturday?")
	today := time.Now().Weekday()
	switch time.Saturday {
	case today + 0:
		fmt.Println("Today.")
	case today + 1:
		fmt.Println("Tomorrow.")
	case today + 2:
		fmt.Println("In two days.")
	default:
		fmt.Println("Too far away.")
	}
}
