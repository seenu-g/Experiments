
fun add (op1 : Int, op2 : Int):Int{
    var sum = op1 + op2
    return sum;
}

fun factorial(a:Int):Int{
    val result:Int
    
    if( a <= 1){
       result = a
    }else{
       result = a*factorial(a-1)
    }
    
    return result
 }
 
fun multiply(a: Int, b: Int) = a  * b 
fun subtract(a: Int, b: Int) = a  - b 
fun divide(a: Int, b: Int) = a  / b 

// A higher-order function is a function that takes another function as parameter and/or returns a function.
fun calculate(a: Int, b: Int, operation:(Int, Int) -> Int): Int {
    return operation(a, b)                                       
}

fun square(x: Int) = x * x
fun cube(x: Int) = x * x * x

fun run_macros( a: Int, operation:(Int)-> Int): Int {
     return operation(a)
}

// Kotlin lambda is a function which has no name and defined with a curly braces {} which takes zero or more parameters and body of function.
// The body of function is written after variable (if any) followed by -> operator.


fun main() {
    val op1 = 400
    val op2 = 25
   
    var result = add(op1, op2)
    println( " op1 = $op1 , op2  = $op2 add: " + result )
    
    println( " op1 = $op1 , op2  = $op2 subtract : " + calculate(op1,op2,::subtract))
    println( " op1 = $op1 , op2  = $op2 multiply : " + calculate(op1,op2,::multiply))
    println( " op1 = $op1 , op2  = $op2 divide : " + calculate(op1,op2,::divide))
    println( " op2 = $op2 squares :"  + run_macros(op2,::square))    
    println( " op2 = $op2 cube :"  + run_macros(op2,::cube))    

    result = factorial(5)
    println( "factorial " +result)

    // Kotlin lambda is  no name function, defined within curly braces {} and takes zero or more parameters and body of function.
    //The body of function is written after variable (if any) followed by -> operator.
    val upperCase = { str: String -> str.toUpperCase() }  
    println( upperCase("hello, world!") )

    var floatValue = { str: String -> str.toFloat()}
    println( " Convert string to Float " + floatValue("12345.678") )
    println( 12345.678 + floatValue("12345.678"))
    
    var longValue = { str: String -> str.toLong()}
    println( " Convert string to long " + longValue("5") )

    var longValue1 = { num: Int -> num.toLong()}
    println(  " Convert Int to long " + longValue1(5) )

 }
 