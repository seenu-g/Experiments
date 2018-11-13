package main

import (
	"encoding/json"
	"log"
	"net/http"
    "fmt"
	"github.com/gorilla/mux"
)

type Employee struct {
	ID        string
	Firstname string
	Lastname  string
	Address   *Address
}
type Address struct {
	City  string
	State string
}

var emp []Employee

func GetEmpIdEndpoint(w http.ResponseWriter, req *http.Request) {
	params := mux.Vars(req)
	for _, item := range emp {
		if item.ID == params["id"] {
			json.NewEncoder(w).Encode(item)
			return
		}
	}
	json.NewEncoder(w).Encode(&Employee{})
}

func GetEmployeeEndpoint(w http.ResponseWriter, req *http.Request) {
	json.NewEncoder(w).Encode(emp)
}
func NotSupported(w http.ResponseWriter, req *http.Request) {
	json.NewEncoder(w).Encode("Not supported function")
}

func main() {
	router := mux.NewRouter()
	emp = append(emp, Employee{ID: "1", Firstname: "MArina", Lastname: "A",
		Address: &Address{City: "Bangalore", State: "Karnataka"}})
	emp = append(emp, Employee{ID: "2", Firstname: "Rajesh", Lastname: "NM"})
	emp = append(emp, Employee{ID: "3", Firstname: "Vinay", Lastname: "BV"})
	router.HandleFunc("/employee", GetEmployeeEndpoint).Methods("GET")
	router.HandleFunc("/employee/", NotSupported).Methods("GET")
	router.HandleFunc("/employee/{id}", GetEmpIdEndpoint).Methods("GET")
	fmt.Println("http://localhost:12345/employee/id or http://localhost:12345/employee")
	log.Fatal(http.ListenAndServe(":12345", router))
}
