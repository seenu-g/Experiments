package main

import (
	"fmt"
)

type Rectangle struct {
	length, width int
	name          string
} 

func main() {

	r1 := Rectangle{2, 1, "my_r1"} //initialize values in order they are defined in struct
	fmt.Println("Rectangle r1 is: ", r1)

	e := Employee{"Srinivasan", "G", 30, 20}
	fmt.Println(e)
	e.LeavesRemaining()

	pr := new(Rectangle)
	(*pr).width = 6
	pr.length = 8
	pr.name = "ptr_to_rectangle"
	fmt.Println("Rectangle pr as address is: ", pr) 

	e1 := new(Employee)
	e1.firstName = "Mridula"
	e1.lastName = "Srinivasan"
	e1.totalLeaves = 12
	e1.leavesTaken = 6
	fmt.Println(e1)

	p1 := new(person)
	p1.firstName = "Mridula"
	p1.lastName = "Srinivasan"
	p1.totalLeaves = 12
	p1.leavesTaken = 6
	fmt.Println(p1)
}
