package rectangle

import (
	"fmt"
	"math"
)

func init() {
	fmt.Println("rectangle package initialized")

}

func Area(len, wid float64) float64 {
	area := len * wid
	return area
}

func Diagonal(len, wid float64) float64 {
	diagonal := math.Sqrt((len * len) + (wid * wid))
	return diagonal
}

//Any variable or function which starts with a capital letter are exported names in go.
//Only exported functions and variables can be accessed from other packages
