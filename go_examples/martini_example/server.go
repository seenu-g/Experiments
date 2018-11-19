package main

import (
	"library/contact/contactbook"
	"library/contact/contactservice"
	"github.com/go-martini/martini"
)

func main() {
	martiniClassic := martini.Classic()
	contactBook := contactbook.NewContactBook()
	contactservice.RegisterWebService(contactBook, martiniClassic)
	martiniClassic.Run()
}
