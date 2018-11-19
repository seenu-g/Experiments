package main

import (
	"encoding/json"
	"fmt"
	"os"
	"log"
)
type Color struct {
	Space string
	Point json.RawMessage // delay parsing until we know the color space
}
type RGB struct {
	R uint8
	G uint8
	B uint8
}
type YCbCr struct {
	Y  uint8
	Cb int8
	Cr int8
}

//RawMessage is a raw encoded JSON value. It implements Marshaler and Unmarshaler 
// and can be used to delay JSON decoding or precompute a JSON encoding.
func main() {
	h := json.RawMessage(`{"precomputed": true}`)

	c := struct {
		Header *json.RawMessage `json:"header"`
		Body   string           `json:"body"`
	}{Header: &h, Body: "Hello Gophers!"}

	b, err := json.MarshalIndent(&c, "", "\t")
	if err != nil {
		fmt.Println("error:", err)
	}
	os.Stdout.Write(b)

	var j = []byte(`[
	{"Space": "YCbCr", "Point": {"Y": 255, "Cb": 0, "Cr": -10}},
	{"Space": "RGB",   "Point": {"R": 99, "G": 218, "B": 155}},
	{"Space": "RGB",   "Point": {"R": 49, "G": 248, "B": 255}},
	{"Space": "YCbCr", "Point": {"Y": 119, "Cb": 118, "Cr": 39}}
    ]`)
	
	var colors []Color
	err2 := json.Unmarshal(j, &colors)
	if err2 != nil {
		log.Fatalln("error:", err)
	}

	for _, c := range colors {
		var dst interface{}
		switch c.Space {
		case "RGB":
			dst = new(RGB)
		case "YCbCr":
			dst = new(YCbCr)
		}
		err := json.Unmarshal(c.Point, dst)
		if err != nil {
			log.Fatalln("error:", err)
		}
		fmt.Println(c.Space, dst)
	}
}