
def shopping_list():
    print("program to add items to shopping list")
    items = []
    while True: 
        item = input("Enter new item ")
        if item == "0" :
            break
        else :
            items.append(item)
    print( "Your list of items for purchase during shopping" )
    print(items)

shopping_list()