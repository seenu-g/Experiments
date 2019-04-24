package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/julienschmidt/httprouter"
)

func HandlerFunc(w http.ResponseWriter, r *http.Request) {
	fmt.Println("someone visited the page")
	w.Header().Set("Content-Type", "text/html") // if text/plain, browser will display them as text with HTML tags
	if r.URL.Path == "/" {
		fmt.Fprint(w, "<h1>Welcome to my awesome site!</h1>")
	} else if r.URL.Path == "/contact" {
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, "To get in touch, please send an email "+
			"to <a href=\"mailto:support@lenslocked.com\">"+
			"support@lenslocked.com</a>")
	} else {
		w.WriteHeader(http.StatusNotFound)
		fmt.Fprint(w, "<h1>We could not find the page you "+
			"were looking for :(</h1>"+
			"<p>Please email us if you keep being sent to an "+
			"invalid page.</p>")
	}
}

// additional parameter httprouter.Params has downside that code is locked down with this specific router
func Index(w http.ResponseWriter, r *http.Request, _ httprouter.Params) {
	fmt.Fprint(w, "Welcome!\n")
}
func Hello(w http.ResponseWriter, r *http.Request, ps httprouter.Params) {
	fmt.Fprintf(w, "hello, %s!\n", ps.ByName("name"))
}

func main() {
	router := httprouter.New()
	router.GET("/", Index)
	router.GET("/hello/:name", Hello)

	//mux := http.NewServeMux()
	//mux.HandleFunc("/", HandlerFunc)
	//http.HandleFunc("/", HandlerFunc)
	//http.ListenAndServe(":3000", mux)
	//http.ListenAndServe(":3000", nil)
	log.Fatal(http.ListenAndServe(":8080", router))

}
