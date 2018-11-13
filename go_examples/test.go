package main

import (
	"fmt"
	"reflect"
	"strings"
)

func main() {
	var x [5]int
	var i, j int
	for i = 0; i < 5; i++ {
		x[i] = i + 10
	}
	for j = 0; j < 5; j++ {
		fmt.Printf("Element[%d] = %d\n", j, x[j])
	}

	var b = 5
	var a = [3][3]int{{1, 2, 3}, {4, 5, 6}, {7, 8, 9}}
	/* output each array element's value */
	for i = 0; i < 3; i++ {
		for j = 0; j < 3; j++ {
			fmt.Print(a[i][j], " ")
		}
		fmt.Println()
	}
	fmt.Print(b, "\n")
	b = 89
	fmt.Println(reflect.TypeOf(b))
	fmt.Printf("%T\n", b)
	var b1 = "srini"
	fmt.Println(reflect.TypeOf(b1))

	var str = "I love my country"
	fmt.Println(len(str))

	str = "New "
	fmt.Println(strings.Repeat(str, 4))

	str = "Hi...there"
	fmt.Println(strings.Contains(str, "th"))

	str = "Hi...there"
	fmt.Println(strings.Index(str, "there"))

	str = "Hi...there"
	fmt.Println(strings.Replace(str, "e", "Z", 2))

}
