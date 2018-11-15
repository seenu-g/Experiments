package main
import (  
    "fmt"
	"os"
	"net"
)

func main() {  
   openFile("/test.txt");
   openFile("/test$$#@&*^.txt");

   findIpAddress("mcaprotect.org")
   findIpAddress("google.com")
   findIpAddress("yahoo.com")
   findIpAddress("broker.mcapr0tect.org")

}

func openFile(filename string){
	f, err := os.Open(filename)
    if err != nil {
		if err, ok := err.(*os.PathError); ok {
			fmt.Println("File at path", err.Path, "failed to open")
			return
		}
		fmt.Println("Error message:", err)
	}

    fmt.Println(f.Name(), "opened successfully")
}
func findIpAddress(hostname string){
	addr, err := net.LookupHost(hostname)
	if err, ok := err.(*net.DNSError); ok {
		if err.Timeout() {
			fmt.Println("operation timed out")
		} else if err.Temporary() {
			fmt.Println("temporary error")
		} else {
			fmt.Println("generic error: ", err)
		}
		return
	}
	fmt.Println(hostname," : ", addr)
}