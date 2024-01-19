package main

import "fmt"

type car interface {
	move()
	start()
	drive()
	stop()
}

type honda struct {
	model string
}

func (h *honda) move() {
	h.start()
	h.drive()
}
func (h *honda) start() {
	fmt.Println("Honda Civic started")
}
func (h *honda) drive() {
	fmt.Println("Honda Civic on drive")
}
func (h *honda) stop() {
	fmt.Println("Honda Civic on move")
}

func NewHonda(arg string) car {
	return &honda{arg}
}

type volvo struct {
	model string
}

func (v *volvo) move() {
	v.start()
	v.drive()
}
func (v *volvo) start() {
	fmt.Println("Volvo started")
}
func (v *volvo) drive() {
	fmt.Println("Volvo on drive")
}
func (v *volvo) stop() {
	fmt.Println("Volvo on move")
}

func NewVolvo(arg string) car {
	return &volvo{arg}
}

func main() {
	temp_honda := NewHonda("Camry")
	temp_volvo := NewVolvo("Beetle")
	temp_honda.move()
	temp_volvo.move()
}
