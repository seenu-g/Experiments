
fun main() {
   //  A Kotlin list can be either mutable (mutableListOf) or read-only (listOf),  can have duplicate elements.

   val nameList = listOf("Srini", "Naresh", "Ram", "Venky")
   println("Size " + nameList.size)
   println(nameList) 
   val item = "Ram"
   println("index of $item :" + nameList.indexOf(item))
   val index = 1
   println("item at index $index :" + nameList.get(index))

   if(nameList.contains("Srini1")){
        println("nameList contains Srini")
   }else{
        println("nameList does not contain Srini1")
    }

    // List provides read-only access to stored elements
    val numberList = listOf("one", "two", "three", "four")    
    val itr = numberList.listIterator() 
    while (itr.hasNext()) {
        println(itr.next())
    }
    if("two" in numberList){
        println(true)
    }else{
        println(false)
    }
    
    val addList = nameList + numberList
    println ("Add two list : $addList")
    val addList2 = numberList + numberList
    println ("Add two list : $addList2 - can have duplicates")

    val smallList = listOf("one")
    val diffList = numberList - smallList
    println ("subtract one list from other : $diffList")

    try {
        // this gives compiler errors
       // numberList.add("five")
    } catch ( exception: Exception) {
        println ("Exception " + exception)
    }

    //MutableList provides “list-specific write operations” that allow us to add or remove particular elements from an existing list.
    val theMutableList = mutableListOf("apple", "orange", "guava", "pineapple")
   // println(theMutableList)
    for (i in theMutableList.indices) {
        println(theMutableList[i])
     }
     
     theMutableList.add("papaya")
     theMutableList.add("watermelon")
     theMutableList.add("grapes")
     theMutableList.remove("guava")
     println ("\n after operating on the list")
     theMutableList.forEach { println(it) }

     // A Kotlin set can be either mutable (mutableSetOf) or read-only (setOf). Kotlin mutable or immutable sets do not allow to have duplicate elements.

     val firstSet = setOf("one", "two", "three")
     val secondSet = setOf("one", "four", "five", "six", "three")
     val resultSet = firstSet + secondSet // there are no duplicates in resultSet
     println(resultSet)

     //Kotlin map is a collection of key/value pairs, where each key is unique, and it can only be associated with one value. 
     //The same value can be associated with multiple keys though. We can declare the keys and values to be any type; there are no restrictions.

     var theMap = mutableMapOf("one" to 1, "two" to 2, "three" to 3, "four" to 4)
     println("The value for key two " + theMap.get("two"))
     theMap.put("five",5)
     theMap.remove( "two")
     println(theMap)
     println("The value for key two " + theMap.get("two"))
     println("The value for key five " + theMap["five"])
     println("size " + theMap.size)
     var valueMap = theMap.filterValues{ it > 2}
     println("values > 2 " + valueMap)

     var theCapital = mutableMapOf<String, String>()
    
     theCapital.put ("Karntaka","Bengaluru")
     theCapital.put ("Tamil Nadu", "Chennai")
     theCapital.put ("Kerala","Trivandrum")
     theCapital.put ("Telangana", "Hyderabad")
     theCapital.put ("Andhra", "Hyderabad")
     theCapital.put ("Punjab", "Chandigarh")     
     theCapital.put ("Haryana" ,"Chandigarh")
     
     println(theCapital) 

     var state : String
     state = "Punjab"
     println( "capital of  $state :" + theCapital.get(state))
     state = "Haryana"
     println( "capital of  $state :" + theCapital.get(state))

     var strState : String
     strState = "Maharashtra"
     if(theCapital.containsKey(strState)){
        println("$strState is present ")
     }else{
        println("$strState is not present ")
     }
     var strCapital : String
     strCapital = "Chennai"
     if(theCapital.containsValue(strCapital)){
        println("$strCapital is present \n ")
     }else{
        println("$strCapital is not present \n")
     }

     for ((k, v) in theCapital) {
        println("$k = $v")
     }

     theCapital.put ("Maharashtra" ,"Mumbai")
     theCapital.put ("Rajasthan" ,"Jaipur")
     println("\n count of elements in map " + theCapital.count())

     var SortedCapital = theCapital.toSortedMap()
     println(" Capitals (sorted on State)")
     SortedCapital.forEach { 
      k, v -> println("state = $k, Capital = $v") 
     }

     val findCapital = "Chandigarh"
     var foundStates = theCapital.filterValues{ it == findCapital}
     println("states wth Capital  $findCapital :  $foundStates" )
     
     val findState= "Maharashtra"
     var foundCapital = theCapital.filterKeys{ it == findState}
     println(" Capital of  $findState is :  $foundCapital[$findState]" )
}