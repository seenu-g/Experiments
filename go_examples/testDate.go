package main

import "fmt"
import "time"

func main() {
	printFunc := fmt.Println

	present := time.Now() // current time
	printFunc(present)

	DOB := time.Date(2003, 9, 13, 1, 45, 39, 213, time.Local)
	printFunc(DOB)

	fmt.Println(DOB.Year())
	fmt.Println(DOB.Month())
	fmt.Println(DOB.Day())
	fmt.Println(DOB.Hour())
	fmt.Println(DOB.Minute())
	fmt.Println(DOB.Second())
	fmt.Println(DOB.Nanosecond())
	fmt.Println(DOB.Location())

	fmt.Println(DOB.Weekday())

	fmt.Println(DOB.Before(present))
	fmt.Println(DOB.After(present))
	fmt.Println(DOB.Equal(present))

	diff := present.Sub(DOB)
	fmt.Println(diff)
	years := int(diff.Hours() / (24 * 365))
	fmt.Printf("%d years ago \n", years)
	days := int(diff.Hours() / 24)
	fmt.Printf("%d days ago \n", days)
	fmt.Println(diff.Hours())
	fmt.Println(diff.Minutes())
	fmt.Println(diff.Seconds())
	fmt.Println(diff.Nanoseconds())
	fmt.Println(DOB.Add(diff))
	fmt.Println(DOB.Add(-diff))
}
