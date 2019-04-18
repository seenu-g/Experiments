package main

import (
	"fmt"
	"math/rand"
)

type Tree struct {
	Left  *Tree
	Value int
	Right *Tree
}

func Display(root *Tree) {
	if root == nil {
		return
	}
	fmt.Println(root.Value)
	Display(root.Left)
	Display(root.Right)
}

func New(n, k int) *Tree {
	var node *Tree
	for _, v := range rand.Perm(n) {
		node = insert(node, (1+v)*k)
	}
	return node
}

func insert(node *Tree, item int) *Tree {
	if node == nil {
		return &Tree{nil, item, nil}
	}
	if item < node.Value {
		node.Left = insert(node.Left, item)
		return node
	}
	node.Right = insert(node.Right, item)
	return node
}

func main() {
	var root *Tree
	root = insert(root, 100)
	root = insert(root, 175)
	root = insert(root, 200)
	root = insert(root, 125)
	root = insert(root, 150)
	root = insert(root, 120)
	root = insert(root, 50)
	Display(root)

}
