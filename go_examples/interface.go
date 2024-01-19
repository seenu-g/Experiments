package main

import (
	"fmt"
)

type vehicle interface {
	accelerate()
	start()
	stop()
}

func Print(v vehicle) {
	fmt.Println(v)
}

type toyota struct {
	model string
	color string
	speed int
}

func (t toyota) start() {
	Print(t)
	fmt.Println("Started?")
}
func (t toyota) accelerate() {
	Print(t)
	fmt.Println("I accelerate swift?")
}
func (t toyota) stop() {
	Print(t)
	fmt.Println("Stopped?")
}

func (t toyota) drive() {
	fmt.Println("-------------------------------- ")
	t.start()
	t.accelerate()
	t.accelerate()
	t.stop()
	fmt.Println("-------------------------------- ")
}

type maruti struct {
	model string
	color string
	speed int
}

func (m maruti) start() {
	Print(m)
	fmt.Println("Started?")
}
func (m maruti) accelerate() {
	Print(m)
	fmt.Println("I accelerate fast?")
}
func (m maruti) stop() {
	Print(m)
	fmt.Println("Stopped?")
}

func (m maruti) drive() {
	fmt.Println("-------------------------------- ")
	m.start()
	m.accelerate()
	m.stop()
	fmt.Println("-------------------------------- ")
}

func Anything(anything interface{}) {
	fmt.Println(anything)
}

func main() {
	t1 := toyota{"Toyota", "Red", 100}
	m1 := maruti{"Maruti", "Gray", 200}

	t1.drive()
	m1.drive()

	var t toyota
	Print(t)
	t.accelerate()

	var v vehicle
	Print(v)

	Anything(2.44)
	Anything(("Pascal"))
	Anything(struct{}{})

	mymap := make(map[string]interface{})
	mymap["name"] = "Honda"
	mymap["model"] = 2011
	fmt.Println(mymap)
}
