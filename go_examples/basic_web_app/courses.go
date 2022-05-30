package main

import (
	"encoding/json"
	"log"
	"math/rand"
	"net/http"
	"strconv"

	"github.com/gorilla/mux"
)

var courses []Course

func main() {
	//Initialize router using mux
	router := mux.NewRouter()

	courses = append(courses, Course{ID: "124134", Name: "FullStack Django Developer Freelance ready", Price: "299", Link: "https://courses.learncodeonline.in/learn/FullStack-Django-Developer-Freelance-ready",
		Author: &Author{Firstname: "Hitesh", Lastname: "Choudhary"}})
	courses = append(courses, Course{ID: "154434", Name: "Full stack with Django and React", Price: "299", Link: "https://courses.learncodeonline.in/learn/Full-stack-with-Django-and-React",
		Author: &Author{Firstname: "Hitesh", Lastname: "Choudhary"}})
	courses = append(courses, Course{ID: "198767", Name: "Complete React Native bootcamp", Price: "199", Link: "https://courses.learncodeonline.in/learn/Complete-React-Native-Mobile-App-developer",
		Author: &Author{Firstname: "Hitesh", Lastname: "Choudhary"}})

	// Create the routes, we will be creating each function in future
	router.HandleFunc("/api/courses", getCourses).Methods("GET")
	router.HandleFunc("/api/course/{id}", getSingleCourse).Methods("GET")
	router.HandleFunc("/api/courses/create", createCourse).Methods("POST")
	router.HandleFunc("/api/courses/update/{id}", updateCourse).Methods("PUT")
	router.HandleFunc("/api/courses/delete/{id}", deleteCourse).Methods("DELETE")

	// Initialize a server, log.Fatal will throw an error if anything goes wrong
	log.Fatal(http.ListenAndServe(":8000", router))

}

type Author struct {
	Firstname string `json:"firstname"`
	Lastname  string `json:"lastname"`
}

// Course model (Struct)
type Course struct {
	ID     string  `json:"id"`
	Name   string  `json:"name"`
	Price  string  `json:"price"`
	Link   string  `json:"link"`
	Author *Author `json:"author"` // This field is pointing towards the Author struct
}

func getCourses(res http.ResponseWriter, req *http.Request) {
	res.Header().Set("Content-Type", "application/json")
	json.NewEncoder(res).Encode(courses)
}

func getSingleCourse(res http.ResponseWriter, req *http.Request) {
	res.Header().Set("Content-Type", "application/json")
	params := mux.Vars(req) // we are extracting 'id' of the Course which we are passing in the url
	for _, item := range courses {
		if item.ID == params["id"] {
			json.NewEncoder(res).Encode(item) // sending matched course in json format
			return
		}
	}
	json.NewEncoder(res).Encode("No course found")
}

func createCourse(res http.ResponseWriter, req *http.Request) {
	res.Header().Set("Content-Type", "application/json")
	var course Course
	_ = json.NewDecoder(req.Body).Decode(&course)
	course.ID = strconv.Itoa(rand.Intn(1000000)) // just creating dummy id as we are not sending an id from postman
	// At the end, send the course that we have created.
	json.NewEncoder(res).Encode(course)
}

func deleteCourse(res http.ResponseWriter, req *http.Request) {
	res.Header().Set("Content-Type", "application/json")
	params := mux.Vars(req) // we are extracting 'id' of the Course which we are passing in the url

	for i, item := range courses {
		if item.ID == params["id"] {
			// This is slicing of a slice(array)
			// append all the courses in `courses` slice (array) except, the one which has ID equal to the id which we've passed in the url
			courses = append(courses[:i], courses[i+1:]...)
			break
		}
	}
	json.NewEncoder(res).Encode(courses) // it will return all the other courses except the deleted one.
}

func updateCourse(res http.ResponseWriter, req *http.Request) {
	res.Header().Set("Content-Type", "application/json")
	params := mux.Vars(req) // we are extracting 'id' of the Course which we are passing in the url

	for i, item := range courses {
		if item.ID == params["id"] {
			courses = append(courses[:i], courses[i+1:]...)
			var course Course
			//  create new course from it
			_ = json.NewDecoder(req.Body).Decode(&course)
			course.ID = params["id"] // we are keeping the id same because we are updating the existing coursen
			// Now, append that course in 'courses' slice(array)
			courses = append(courses, course)
			json.NewEncoder(res).Encode(course)
			return
		}
	}
}
