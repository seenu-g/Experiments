package main

import (
        "fmt"
		"os"
		"math"
)
func main() {
	fmt.Printf("Now you have %g problems.\n", math.Sqrt(7))
	goPath := os.Getenv("GOPATH")
    fmt.Printf(goPath)
}