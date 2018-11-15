package main
import ( 
	"fmt"
	"math"
)
//the init statement: executed before the first iteration
//the condition expression: evaluated before every iteration
//the post statement: executed at the end of every iteration

func main() {
	sum := 0
	for i := 0; i < 10; i++ {
		sum += i
	}
	fmt.Println(sum)

	fmt.Println(sqrt(2), sqrt(-4))

	count := 1
	for count < 1000 {
		count += count
	}
	fmt.Println(count)

	//if statement can start with a short statement to execute before the condition
	// after statement it is not available.
	if v := math.Pow(3, 2); v < 10 {
		fmt.Println(v , "less than 10");
	}
	if v := math.Pow(5, 2); v < 10 {
		fmt.Println(v , "less than 10");
	} else {
		fmt.Println(v , "greater than 10");
	}

	studentGrades := [3]int{50, 89, 75}
    fmt.Printf("Grades for each:")
    for _, grade := range studentGrades { 
      fmt.Printf("%d ",grade);
    } 
}

func sqrt(x float64) string {
	//the expression need not be surrounded by parentheses ( ) but the braces { } are required
	if x < 0 {
		return sqrt(-x) + "i"
	}
	return fmt.Sprint(math.Sqrt(x))
}
