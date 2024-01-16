package main

import (
	"fmt"
	"math"
	"math/cmplx"
	"strings"
)

var (
	MaxInt uint64     = 1<<64 - 1
	z      complex128 = cmplx.Sqrt(-5 + 12i)
)

const Pi = 3.14

func main() {
	defer fmt.Println("world")

	var i, j int = 1, 2
	k := 3
	c, python, java := true, false, "no!"

	fmt.Println(i, j, k, c, python, java)

	fmt.Printf("Type: %T Value: %v\n", MaxInt, MaxInt)
	fmt.Printf("Type: %T Value: %v\n", z, z)

	var x, y int = 3, 4
	var f float64 = math.Sqrt(float64(x*x + y*y))
	fmt.Println(x, y, f)

	fmt.Println(Pi)

	fmt.Println("hello")

	m1 := 2
	m2 := 3
	fmt.Println(m1 + m2)

	var str1, str2 string = "Milli", "Srinivasan"
	//m1 := "Milli Srinivasan"
	fmt.Println(str1 + str2)
	var str3 string = str1 + " " + str2
	fmt.Println(str3, "Contains", str2, strings.Contains(str3, str1))
	fmt.Println(str3, "Contains", "Shubha", strings.Contains(str3, "Shubha"))
	fmt.Println(strings.ReplaceAll(str3, "Milli", "Milani"))
	fmt.Println(strings.Split(str3, " "))

	//s1 := "my"
	//s1 := "my name" this is error := is used only for declaration
}

/*
1. Only Inside a function, the := short assignment statement can be used in place of a var declaration with implicit type.
2. A var declaration can include initializers, one per variable.
3. Variable declarations may be "factored" into blocks, as with import statements
4. The int, uint, and uintptr types are usually 32 bits wide on 32-bit systems and 64 bits wide on 64-bit systems
5. When declaring a variable without specifying an explicit type, the variable's type is inferred from the value on the right hand side.
6. Constants are declared like variables, but with the const keyword.
   Constants can be character, string, boolean, or numeric values.
   Constants cannot be declared using the := syntax.


*/
