package main

import (
	"fmt"
	"net/http"
)

func main() {
	http.HandleFunc("/", MyHandler1)
	http.HandleFunc("/John", MyHandler2)
	http.HandleFunc("/Srini", MyHandler3)
	fmt.Printf("check for different routes at http://localhost:8080")
	http.ListenAndServe(":8080", nil)
}
func MyHandler1(w http.ResponseWriter, r *http.Request) {
	fmt.Fprint(w, "Hello World\n")
}
func MyHandler2(w http.ResponseWriter, r *http.Request) {
	fmt.Fprint(w, "Hello John\n")
}
func MyHandler3(w http.ResponseWriter, r *http.Request) {
	fmt.Fprint(w, "Hello Srini\n")
}
