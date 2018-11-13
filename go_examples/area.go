package main

// copy package in work/src/geometry
import (
	"fmt"
	"geometry/rectangle" //importing custom package
)

func main() {
	var rectLen, rectWidth float64 = 6, 7
	// rectangle.init() // init starts with small letter
	fmt.Println("Geometrical shape properties")
	/*Area function of rectangle package used
	 */
	fmt.Printf("area of rectangle %.2f\n", rectangle.Area(rectLen, rectWidth))
	/*Diagonal function of rectangle package used
	 */
	fmt.Printf("diagonal of the rectangle %.2f ", rectangle.Diagonal(rectLen, rectWidth))
}
