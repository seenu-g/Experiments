package main

import (
	"encoding/json"
	"fmt"
	"log"
	"strings"
	"os"
)

type EmployeeGroup struct {
	ID     int
	Name   string
	Skills []string
}

type Employee struct {
	Name  string
	ID int
}

type Animal int
const (
	Unknown Animal = iota
	Gopher
	Zebra
)

func (a *Animal) UnmarshalJSON(b []byte) error {
	var s string
	if err := json.Unmarshal(b, &s); err != nil {
		return err
	}
	switch strings.ToLower(s) {
	default:
		*a = Unknown
	case "gopher":
		*a = Gopher
	case "zebra":
		*a = Zebra
	}

	return nil
}

func (a Animal) MarshalJSON() ([]byte, error) {
	var s string
	switch a {
	default:
		s = "unknown"
	case Gopher:
		s = "gopher"
	case Zebra:
		s = "zebra"
	}

	return json.Marshal(s)
}

func main() {

	group := EmployeeGroup{
		ID:     1,
		Name:   "Developers",
		Skills: []string{"C", "Java", "Python", "GoLang"},
	}

	b, err := json.Marshal(group)
	if err != nil {
		fmt.Println("error:", err)
	}
	os.Stdout.Write(b)

	var employeeBlob = []byte(`[
		{"Name": "Ramesh", "ID": 1},
		{"Name": "Kinesh",  "ID": 2}
	]`)
	var employees []Employee
	err = json.Unmarshal(employeeBlob, &employees)
	if err != nil {
			fmt.Println("error:", err)
	}
	fmt.Printf("\n %+v", employees) 
	

	blob := `["gopher","armadillo","zebra","unknown","gopher","bee","gopher","zebra"]`
	var zoo []Animal
	if err := json.Unmarshal([]byte(blob), &zoo); err != nil {
		log.Fatal(err)
	}

	census := make(map[Animal]int)
	for _, animal := range zoo {
		census[animal] += 1
	}

	fmt.Printf("\n Zoo Census:\n* Gophers: %d\n* Zebras:  %d\n* Unknown: %d\n",
		census[Gopher], census[Zebra], census[Unknown])
}
