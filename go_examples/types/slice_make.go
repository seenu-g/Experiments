package main

//Slices can be created with the built-in make function;
//this is how you create dynamically-sized arrays.
//To specify a capacity, pass a third argument to make:

import "fmt"

func main() {

	var s []int
	fmt.Println(s, len(s), cap(s))
	if s == nil {
		fmt.Println("nil!")
	}

	exp2 := make([]int, 20) // user make to create slice
	for i := range exp2 {
		exp2[i] = 1 << uint(i)
	}
	fmt.Println("displayed in single line", exp2)
	for _, value := range exp2 {
		fmt.Printf("%d\n", value)
	}

	a := make([]int, 5)
	fmt.Printf("%s len=%d cap=%d %v\n", "a", len(a), cap(a), a)

	b := make([]int, 0, 5) //To specify a capacity, pass a third argument to make:
	fmt.Printf("%s len=%d cap=%d %v\n", "b", len(b), cap(b), b)

	c := b[:2]
	fmt.Printf("%s len=%d cap=%d %v\n", "c", len(c), cap(c), c)
	c = append(c, 1)
	fmt.Printf("%s len=%d cap=%d %v\n", "c", len(c), cap(c), c)

	d := c[2:5]
	fmt.Printf("%s len=%d cap=%d %v\n", "d", len(d), cap(d), d)

	d = append(d, 2, 3, 4)
	fmt.Printf("%s len=%d cap=%d %v\n", "d", len(d), cap(d), d)
	fmt.Printf("%s len=%d cap=%d %v\n", "b", len(b), cap(b), b)

}
