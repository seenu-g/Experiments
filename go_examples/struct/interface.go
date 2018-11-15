//An interface type is defined as a set of method signatures.
//A value of interface type can hold any value that implements those methods.

package main

import (
	"fmt"
	"math"
)

type Abser interface {
	Abs() float64
}
type MyFloat float64
func (f MyFloat) Abs() float64 {
	if f < 0 {
		return float64(-f)
	}
	return float64(f)
}

type Vertex struct {
	X, Y float64
}

func (v *Vertex) Abs() float64 {
	return math.Sqrt(v.X*v.X + v.Y*v.Y)
}
func main() {
	var a Abser
	f := MyFloat(-math.Sqrt2)
	v := Vertex{3, 4}

	a = f  // a MyFloat implements Abser
	a = &v // a *Vertex implements Abser
	fmt.Println(a.Abs())


	var interf myInterface
	
	interf = &myStruct{"Srinivasan",42}
	describe(interf)
	interf.method()
	
	interf = myFloat(math.Pi)
	describe(interf)
	interf.method()	
}


type myInterface interface {
	method()
}
func describe(i myInterface) {
	fmt.Printf("(%v, %T)\n", i, i)
}

type myStruct struct {
	name string
	value int
}
func (t *myStruct) method() {
	fmt.Println(t.name, t.value)
}

type myFloat float64
func (f myFloat) method() {
	fmt.Println(f)
}