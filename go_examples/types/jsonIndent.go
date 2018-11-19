package main

import (
	"io"
	"strings"
	"fmt"
	"bytes"
	"encoding/json"
	"log"
	"os"
)

type Message struct {
	Name string
	ID int
}

func main() {
	
	messages := []Message{{"Diamond Fork", 29},{"Sheep Creek", 51},}

	b, err := json.Marshal(messages)
	if err != nil {
		log.Fatal(err)
	}
	// json string is not indented
	os.Stdout.Write(b)
	fmt.Println("\n")

	// the json string got indented
	var out bytes.Buffer
	json.Indent(&out, b, "", "")
//	json.Indent(&out, b, "=", "\n")
	out.WriteTo(os.Stdout)
	fmt.Println("\n")
	
//Each JSON element in the output will begin on a new line beginning with prefix followed by one or more copies of indent
	b1, err := json.MarshalIndent(messages, "", "")
//  b1, err := json.MarshalIndent(messages, "=", "\n")
	if err != nil {
		log.Fatal(err)
	}
	os.Stdout.Write(b1)

	const jsonStream = `
{"Name": "Ray", "ID": 1}
{"Name": "Eric", "ID": 2}
{"Name": "Steve", "ID": 3}
{"Name": "Jason", "ID": 4}
{"Name": "Srini", "ID": 5}
`
//A Decoder reads and decodes JSON values from an input stream.
dec := json.NewDecoder(strings.NewReader(jsonStream))

//More reports whether there is another element in the current array or object being parsed.
//	for dec.More() {
for {
	var msg Message
	if err := dec.Decode(&msg); err == io.EOF {
		break
	} else if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("%s: %d\n", msg.Name, msg.ID)
}

dec1 := json.NewDecoder(strings.NewReader(jsonStream))
// Token returns the next JSON token in the input stream.
// At the end of the input stream, Token returns nil, io.EOF
for  {
	t, err := dec1.Token()
	if err == io.EOF {
		break
	} else if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("%T: %v\n", t, t)
}

}