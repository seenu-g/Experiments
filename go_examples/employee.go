package main

import (
	"encoding/json"
	"log"
	"net/http"

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

func CreateEmployeeEndpoint(w http.ResponseWriter, req *http.Request) {
	params := mux.Vars(req)
	var person Employee
	_ = json.NewDecoder(req.Body).Decode(&person)
	person.ID = params["id"]
	emp = append(emp, person)
	json.NewEncoder(w).Encode(emp)
}
func DeleteEmployeeEndpoint(w http.ResponseWriter, req *http.Request) {
	params := mux.Vars(req)
	for index, item := range emp {
		if item.ID == params["id"] {
			emp = append(emp[:index], emp[index+1:]...)
			break
		}
	}
	json.NewEncoder(w).Encode(emp)
}

func main() {
	router := mux.NewRouter()
	emp = append(emp, Employee{ID: "1", Firstname: "Nic", Lastname: "Raboy",
		Address: &Address{City: "Dublin", State: "CA"}})
	emp = append(emp, Employee{ID: "2", Firstname: "Maria", Lastname: "Raboy"})
	router.HandleFunc("/employee", GetEmployeeEndpoint).Methods("GET")
	router.HandleFunc("/employee/{id}", GetEmpIdEndpoint).Methods("GET")
	router.HandleFunc("/employee/{id}", CreateEmployeeEndpoint).Methods("POST")
	router.HandleFunc("/employee/{id}", DeleteEmployeeEndpoint).Methods("DELETE")
	log.Fatal(http.ListenAndServe(":12345", router))
}
