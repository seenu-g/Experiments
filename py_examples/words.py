#!/usr/bin/python3
""" module """
import sys
from urllib.request import urlopen

def fetch_words(url):
    """ Name : fetch_words
        Description : Fetch a list of words form documents
     """
    with urlopen(url)as story:
        story_words = []
        for line in story:
            line_words = line.decode('utf-8').split()
            for word in line_words:
                story_words.append(word)
    return story_words


def print_words(story_words):
    for word in story_words:
        print(word)


def main(url):
    # url = 'http://sixty-north.com/c/t.txt'
    # url = sys.argv[1]
    words = fetch_words(url)
    print_words(words)

# as the value is main, it is the module that is executed
if __name__ == '__main__':
   main(sys.argv[1])