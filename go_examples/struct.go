package main

import (
	"fmt"
)

type person struct {
	fname string
	lname string
}
type employee struct {
	person
	empId int
}

func (p person) details() {
	fmt.Println(p, " "+" I am a person")
}
func (e employee) details() {
	fmt.Println(e, " "+"I am a employee")
}
func main() {
	p1 := person{"Raj", "Kumar"}
	p1.details()
	e1 := employee{person: person{"John", "Ponting"}, empId: 11}
	e1.details()
}
