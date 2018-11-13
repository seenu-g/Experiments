//A slice is a dynamically-sized, flexible view into  elements of an array.
//Changing elements of a slice modifies the corresponding elements of its underlying array.
//A slice literal is like an array literal without the length.
//The default is zero for  low bound and  length of  slice for  high bound.
//A nil slice has a length and capacity of 0 and has no underlying array.

package main

import "fmt"

var power2 = []int{1, 2, 4, 8, 16, 32, 64, 128}

func main() {
	primes := [6]int{2, 3, 5, 7, 11, 13}

	var slice1 []int = primes[1:4]
	fmt.Println(slice1)
	fmt.Println(len(slice1))

	for i, v := range power2 {
		fmt.Printf("2**%d = %d\n", i, v)
	}

	slice2 := slice1[:0] // This does not impact primes
	fmt.Printf("len=%d cap=%d %v\n", len(slice2), cap(slice2), slice2)
	slice2 = slice2[:4]
	fmt.Printf("len=%d cap=%d %v\n", len(slice2), cap(slice2), slice2)
	slice2 = slice2[2:] //Drop its first two values.
	fmt.Printf("len=%d cap=%d %v\n", len(slice2), cap(slice2), slice2)
	fmt.Println(primes)

	persons := [4]string{"John", "Paul", "George", "Ringo"}
	fmt.Println(persons)

	section1 := persons[0:2]
	section2 := persons[1:3]
	fmt.Println(section1, section2)

	section2[0] = "XXX"
	fmt.Println(section1, section2)
	fmt.Println(persons)

}
