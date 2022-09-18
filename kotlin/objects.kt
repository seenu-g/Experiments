// By default, Kotlin classes are public and we can control the visibility of the class members
//  allows to initialize the constructor parameters with some default values
class Person  {
    // Property (data member)
    private var name: String ;
    private var age: Int ;
    private var salary: Double ;

     // Initializer Block There could be more than one init blocks and during the initialization of an instance, 
     // the initializer blocks are executed in the same order as they appear in the class body

     constructor ( _name: String, _age: Int) {
        this.name = _name
        this.age = _age
        this.salary = 00.00

     }

     constructor ( _name: String, _age: Int, _salary: Double) {
        this.name = _name
        this.age = _age
        this.salary = _salary
     }
    // Member function
    fun printMe() {
       print(" Name - " + name)
       print(" Age - " + age)
    }
 }


 interface ICalcInterface {
   fun add( op1 : Int, op2 : Int): Int     
   fun subtract( op1 : Int, op2 : Int): Int     
   fun multiply( op1 : Int, op2 : Int): Int  
   fun divide( op1 : Int, op2 : Int) : Int

}
//Kotlin abstract class cannot be instantiated. inherit subclasses from a Kotlin abstract class.
//Kotlin abstract class properties and methods are non-abstract unless we explictly use abstract keyword to make them abstract. 
// Kotlin doesn’t support multiple class inheritances. A class can inherit multiple interfaces
class Calculator : ICalcInterface {
   override fun add( op1 : Int, op2 : Int) : Int{
      return op1 + op2 
   }      
   override fun subtract( op1 : Int, op2 : Int): Int{
      return op1 - op2 
   }           
   override fun multiply( op1 : Int, op2 : Int): Int{
      return op1 * op2 
   }           
   override fun divide( op1 : Int, op2 : Int): Int{
      return op1 / op2 
   }      
}

// kotlin provides toString(), hashCode(), copy() and equals() functions
data class Book(val name: String, val publisher: String, var reviewScore: Int)

fun printBook(book : Book){
  println("Name = ${book.name}")
  println("Publisher = ${book.publisher}")
  println("Score = ${book.reviewScore}")
}

 fun main(args: Array<String>) {
    val obj1 = Person("Naresh",48)
    val obj2 = Person("Srini",46,0.00)
    val obj3 = Person("Manali",22)
    obj1.printMe() 
    obj2.printMe() 
    obj3.printMe() 

    val obj = Calculator()
    val op1 : Int
    val op2 : Int
    op1 = 50 
    op2 = 25
    println( " \n $op1 + $op2 = " + obj.add(op1,op2))
    println(" $op1 - $op2 = " + obj.subtract(op1,op2))
    println(" $op1 * $op2 = " + obj.multiply(op1,op2))
    println(" $op1 / $op2 = " + obj.divide(op1,op2))


   val book1 = Book("Kotlin", "Tutorials Point", 10)
   val book2 = book1.copy(reviewScore=5)

   println("Book1")
   printBook(book1)
   println("Book2")
   printBook(book2)
 }
