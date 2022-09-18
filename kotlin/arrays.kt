fun main(args: Array<String>) {
    // once created, arrays can't resize 
    val fruits = arrayOf<String>("Apple", "Mango", "Banana", "Orange")
   
    println( fruits.get(0))
    println( fruits.get(3))
    println( "Size of fruits array " + fruits.size )

    // Set the value at 3rd index
    fruits.set(3, "Guava")
    println( fruits.get(3)) 

    for( item in fruits ){
        println( item )
     }

     if ("Mango" in fruits){
        println( "Mango exists in fruits" )
     }else{
        println( "Mango does not exist in fruits" )
     }
   
   // drop does not remove items from array. Returns a list containing all elements except first n elements.
   var tmp1 = fruits.drop(2) // drops first 2 items from fruits. 
   println( "Size of fruits array " + fruits.size )
   println(tmp1)

   println( "Is Array empty ?: " + fruits.isEmpty()) // false as there are fruits
   tmp1 = fruits.drop(2)
   println( "Size of fruits array " + fruits.size )
   println( "Is Array empty ?: " + fruits.isEmpty()) // false as there are  fruits

   val fruitsCopy = fruits.copyOf(fruits.size)
   println( "Size of fruits Full Copy array " + fruitsCopy.size )
   for( item in fruitsCopy ){
    println( item )
   }

   val fruitsClone = fruits.clone()
   println( "Size of fruits clone Full array " + fruitsClone.size )

   val fruitsCloneRange = fruits.copyOfRange(1, fruits.size) // range can starts from start index of 0 if there are 2 elements, the index stops at n-1, 
    println( "Size of fruits clone Range array " + fruitsCloneRange.size )
   for( item in fruitsCloneRange ){
      println( item )
   }

   var Fruits = fruits.copyOf(fruits.size + 4)
   Fruits.set(4, "Apple")
   Fruits.set(5, "Mango")
   Fruits.set(6, "Banana")
   Fruits.set(7, "Orange")
   println( "Size of Fruits array " + Fruits.size )
   println ("Count of fruits in Fruits array " + Fruits.count() )

   val distinct = Fruits.distinct()
   println( "Distinct fruits " + distinct.size + " in fruits " +  Fruits.size)
   for( item in distinct ){
      println( item )
   }

   println ("print range 95 to 99")
   for ( num in 95..99) {
      println(num)
    }
    println ("print range 4 to 1")
    for ( num in 4 downTo 1 ) {
      println(num)
    }
    println ("print range 0 to 1000 in step 100")
    for ( num in 0..1000 step 100 ) {
      println(num)
    }
    val num = 0..1000
    if(300 in num)
    println("300 is present")
   
    val group = 1..100
   println("min 100..1 " + group.min())
   println("max 100..1 " + group.max())
   println("sum 100..1 " + group.sum())
   println("average 100..1 " + group.average())
   println("count 100..1 " + group.count())
}
