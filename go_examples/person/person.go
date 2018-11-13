package main

import (
	"fmt"
)

type person struct {
	firstName   string
	lastName    string
	totalLeaves int
	leavesTaken int
}

/*
func New(firstName string, lastName string, totalLeave int, leavesTaken int) person {
	p := person{firstName, lastName, totalLeave, leavesTaken}
	return p
} */

func (p person) LeavesRemaining() {
	fmt.Printf("%s %s has %d leaves remaining \n", p.firstName, p.lastName, (p.totalLeaves - p.leavesTaken))
}
