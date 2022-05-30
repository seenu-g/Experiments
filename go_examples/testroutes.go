package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

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

	router.HandleFunc("/status", StatuHandler).Methods("GET")
	router.HandleFunc("/hello", HelloHandler).Methods("GET")
	router.HandleFunc("/now", NowHandler)

	subroute1 := router.PathPrefix("/url_path1").Subrouter()
	subroute1.HandleFunc("/", SubPathHandler)

	subroute2 := router.PathPrefix("/url_path2").Subrouter()
	subroute2.HandleFunc("/", SubPathHandler)

	fmt.Println("http://localhost:12345/url_path1/ or http://localhost:12345/url_path2/")

	router.HandleFunc("/health_check", HealthCheck).Methods("GET")
	router.HandleFunc("/persons", GetPersons).Methods("GET")

	log.Fatal(http.ListenAndServe(":12345", router))
}

func SubPathHandler(resp http.ResponseWriter, req *http.Request) {

	fmt.Fprint(resp, req.URL)
	json.NewEncoder(resp).Encode(req.URL)

}

func NowHandler(resp http.ResponseWriter, _ *http.Request) {

	now := time.Now()

	payload := make(map[string]string)
	payload["now"] = now.Format(time.ANSIC)

	resp.Header().Set("Content-Type", "application/json")
	resp.WriteHeader(http.StatusOK)

	json.NewEncoder(resp).Encode(payload)
}

func HelloHandler(resp http.ResponseWriter, req *http.Request) {

	name := req.URL.Query().Get("name")

	if name == "" {
		name = "guest"
	}

	fmt.Fprintf(resp, "Hello %s!", name)
}

func StatuHandler(resp http.ResponseWriter, _ *http.Request) {

	resp.WriteHeader(http.StatusOK)
	json.NewEncoder(resp).Encode("All is well")
}

func HealthCheck(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)

	fmt.Fprintf(w, "API is up and running")
}

type Response struct {
	Persons []Person `json:"persons"`
}

type Person struct {
	Id        int    `json:"id"`
	FirstName string `json:"first_name"`
	LastName  string `json:"last_name"`
}

func prepareResponse() []Person {
	var persons []Person

	var person Person
	person.Id = 1
	person.FirstName = "Issac"
	person.LastName = "Newton"
	persons = append(persons, person)

	person.Id = 2
	person.FirstName = "Albert"
	person.LastName = "Einstein"
	persons = append(persons, person)

	return persons
}

func GetPersons(w http.ResponseWriter, r *http.Request) {
	var response Response

	persons := prepareResponse()
	response.Persons = persons

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)

	//convert struct to JSON
	jsonResponse, err := json.Marshal(response)
	if err != nil {
		return
	}

	w.Write(jsonResponse)
}
