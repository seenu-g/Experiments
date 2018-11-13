package main

import "fmt"

//A map maps keys to values.
//The zero value of a map is nil. A nil map has no keys, nor can keys be added.
//The make function returns a map of the given type, initialized and ready for use.

type Vertex struct {
	Lat, Long float64
}

var m map[string]Vertex

func main() {
	m = make(map[string]Vertex)
	m["Bell Labs"] = Vertex{40.68433, -74.39967}
	m["MS Research"] = Vertex{80.68433, -74.39967}
	m["Google Research"] = Vertex{120.68433, -74.39967}

	var m1 = map[string]Vertex{
		"Bell Labs": {40.68433, -74.39967}, // If the top-level type is just a type name, you can omit it from the elements of the literal.
		"Google":    Vertex{37.42202, -122.08408},
	}

	fmt.Println(m["Bell Labs"])
	fmt.Println(m["MS Research"])
	fmt.Println(m["Google Research"])
	fmt.Println(m1)

	map_values := make(map[string]int)

	map_values["Srinivasan"] = 1559
	map_values["Rajesh"] = 1659
	map_values["Marina"] = 659
	map_values["Gopal Triple"] = 9

	fmt.Println("map values:", map_values)

	delete(map_values, "Gopal Triple")
	fmt.Println("Dropping one entry, map values:", map_values)

	v, ok := map_values["Gopal Triple"]
	fmt.Println("Gopal Triple:", v, "Present?", ok)
	v1, ok1 := map_values["Srinivasan"]
	fmt.Println("Srinivasan:", v1, "Present?", ok1)

}
