package contactbook

import (
	"encoding/json"
	"io/ioutil"
	"net/http"
	"strconv"
	"github.com/go-martini/martini"
)

func (g *ContactBook) GetPath() string {
	// Associate this service with http://host:port/contactbook.
	return "/contactbook"
}

func (g *ContactBook) WebDelete(params martini.Params) (int, string) {
	if len(params) == 0 {
		g.RemoveAllContacts()
		return http.StatusOK, "collection deleted"
	}
	id, err := strconv.Atoi(params["id"]) 	// Convert id to an integer.
	if err != nil {
		return http.StatusBadRequest, "invalid entry id" 		// Id was not a number.
	}
	err = g.RemoveEntry(id)
	if err != nil {
		return http.StatusNotFound, "entry not found"
	}
	return http.StatusOK, "entry deleted"
}

func (g *ContactBook) WebGet(params martini.Params) (int, string) {
	if len(params) == 0 {
		encodedEntries, err := json.Marshal(g.GetAllEntries())
		if err != nil {
			return http.StatusInternalServerError, "internal error"
		}
		return http.StatusOK, string(encodedEntries)
	}
	id, err := strconv.Atoi(params["id"])
	if err != nil {
		return http.StatusBadRequest, "invalid entry id" 		// Id was not a number.
	}
	entry, err := g.GetEntry(id)
	if err != nil {
		return http.StatusNotFound, "entry not found"
	}
	encodedEntry, err := json.Marshal(entry)
	if err != nil {
		return http.StatusInternalServerError, "internal error"
	}
	return http.StatusOK, string(encodedEntry)
}

func (g *ContactBook) WebPost(params martini.Params,
	req *http.Request) (int, string) {
	defer req.Body.Close()

	requestBody, err := ioutil.ReadAll(req.Body)
	if err != nil {
		return http.StatusInternalServerError, "internal error"
	}

	if len(params) != 0 {
		// No keys in params. This is not supported.
		return http.StatusMethodNotAllowed, "method not allowed"
	}

	var contactEntry ContactEntry
	err = json.Unmarshal(requestBody, &contactEntry)
	if err != nil {
		// Could not unmarshal entry.
		return http.StatusBadRequest, "invalid JSON data"
	}

	g.AddContact(contactEntry.Email, contactEntry.Title,contactEntry.Name)
	return http.StatusOK, "new entry created"
}