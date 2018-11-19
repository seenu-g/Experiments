package contactbook

import (
	"fmt"
	"sync"
)

type ContactEntry struct {
	Id      int
	Email   string
	Title   string
	Name  string
}

type ContactBook struct {
	contactData []*ContactEntry
	mutex *sync.Mutex

}

func NewContactBook() *ContactBook{
	return &ContactBook{
		make([]*ContactEntry, 0),
		new(sync.Mutex),
	}

}

// AddEntry adds a new GuestBookEntry with the provided data.
func (g *ContactBook) AddContact(email, title, name string) int {
	{
		g.mutex.Lock()
		defer g.mutex.Unlock()
		newId := len(g.contactData)
		newEntry := &ContactEntry{
			newId,
			email,
			title,
			name,
		}
		g.contactData = append(g.contactData, newEntry)	
		return newId
	}
	
}

// RemoveEntry removes the entry with the given id. Return nil in case of
// success or a specific error in case of failure.
func (g *ContactBook) RemoveEntry(id int) error {
	g.mutex.Lock()
	defer g.mutex.Unlock()

	if id < 0 || id >= len(g.contactData) ||
		g.contactData[id] == nil {
		return fmt.Errorf("invalid id")
	}
	g.contactData[id] = nil

	return nil
}

// GetEntry returns the entry identified by the given id or an error if it can
// not find it.
func (g *ContactBook) GetEntry(id int) (*ContactEntry, error){
	if id < 0 || id >= len(g.contactData) || g.contactData[id] == nil {
	return nil, fmt.Errorf("invalid id")
    }
    return g.contactData[id], nil
}

// GetAllEntries returns all non-nil entries in the Guest Book.
func (g *ContactBook) GetAllEntries() []*ContactEntry{
	// Placeholder for the entries we will be returning.
	entries := make([]*ContactEntry, 0)

	// Iterate through all existig entries.
	for _, entry := range g.contactData {
		if entry != nil {
			// Entry is not nil, so we want to return it.
			entries = append(entries, entry)
		}
	}
	return entries
}

func (g *ContactBook) RemoveAllContacts() {
	g.mutex.Lock()
	defer g.mutex.Unlock()
	// Reset to a new empty one.
	g.contactData = []*ContactEntry{}
}