from xml.dom.minidom import parse
import xml.dom.minidom

def printItems(books) :   
    for book in books:
        type = book.getElementsByTagName('type')[0]
        print ("Type: %s" % type.childNodes[0].data)
        rating = book.getElementsByTagName('rating')[0]
        print ("Rating: %s" % rating.childNodes[0].data)
        description = book.getElementsByTagName('description')[0]
        print ("Description: %s" % description.childNodes[0].data)
    
def printXML(xmlfile) :
    # Open XML document using minidom parser
    try :
        DOMTree = xml.dom.minidom.parse(xmlfile)
        collection = DOMTree.documentElement
        books = collection.getElementsByTagName("book")
    except Exception :
        print( "issues in reading : " + xmlfile)
    printItems(books)

path='/Users/srinivasang/code/Experiments/py_examples/'
def main() :
    printXML(path + "books.xml")

if __name__ =='__main__':
    main()