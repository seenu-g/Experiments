package main

import (
	"fmt"
)

type Employee struct {
	firstName   string
	lastName    string
	totalLeaves int
	leavesTaken int
}
func New(firstName string, lastName string, totalLeave int, leavesTaken int) Employee {
	e := Employee{firstName, lastName, totalLeave, leavesTaken}
	return e
}

func (e Employee) LeavesRemaining() {
	fmt.Printf("%s %s has %d leaves remaining \n", e.firstName, e.lastName, (e.totalLeaves - e.leavesTaken))
}