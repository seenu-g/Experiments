package main

import (
	"fmt"
)

type person struct {
	firstName string
	lastName  string
	age       int
}

type employee struct {
	person
	empId int
}

func (p person) person_details() {
	fmt.Println(p, " "+" I am a person")
}
func (e employee) employee_details() {
	fmt.Println(e, " "+"I am a employee")
}

func main() {
	x := person{age: 30, firstName: "John", lastName: "Anderson"}
	fmt.Println(x)
	fmt.Println(x.firstName)

	p1 := person{"Raj", "Kumar", 32}
	p1.person_details()
	e1 := employee{person: person{"John", "Ponting", 30}, empId: 11}
	e1.employee_details()
	e2 := employee{person: p1, empId: 11}
	e2.employee_details()

	//p1.employee_details() will not compile

	var y = map[string]int{"Kate": 28, "John": 37, "Raj": 20}
	fmt.Println(y)
	fmt.Println("\n", y["Raj"])

	m := make(map[string]int)
	fmt.Println(m)
	m["Key1"] = 10
	m["Key2"] = 20
	m["Key3"] = 30
	fmt.Println(m)
	m["Key2"] = 555
	fmt.Println(m)

}
