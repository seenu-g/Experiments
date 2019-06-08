package main

import (
    "fmt"
    "html"
    "log"
    "net/http"
)

func main() {

    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "Hello, %q", html.EscapeString(r.URL.Path))
    })

    http.HandleFunc("/hi", func(w http.ResponseWriter, r *http.Request){
        fmt.Fprintf(w, "Hi")
    })

    log.Fatal(http.ListenAndServe(":8081", nil))

}
// Run this command
//$ docker build -t my-go-app .
// View images
//$ docker images
//Run docker and map container 8081 to localhost 8080
//$ docker run -p 8080:8081 -it my-go-app
// view container running
//$ docker ps
// stop container
//$ docker kill <containerid>
