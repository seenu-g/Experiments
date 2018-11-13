//https://www.calhoun.io/updating-and-deleting-postgresql-records-using-gos-sql-package/
package main

import (
	"database/sql"
	"fmt"

	_ "github.com/lib/pq"
)

const (
	host     = "localhost"
	port     = 5432
	user     = "postgres"
	password = "Accion@123"
	dbname   = "mcaprotect"
)

func main() {
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s "+
		"password=%s dbname=%s sslmode=disable",
		host, port, user, password, dbname)
	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		panic(err)
	}
	defer db.Close()

	err = db.Ping()
	if err != nil {
		panic(err)
	}

	fmt.Println("Successfully connected!")

	var sqlStatement = `INSERT INTO monUsers (age, email, first_name, last_name)
	VALUES ($1, $2, $3, $4) RETURNING id`
	id := 0
	err = db.QueryRow(sqlStatement, 30, "srini4@tmplr.io", "Srinivasan", "G").Scan(&id)
	if err != nil {
		panic(err)
	}
	fmt.Println("New record ID is:", id)

	sqlStatement = ` UPDATE monUsers SET first_name = $2, last_name = $3
	WHERE id = $1 RETURNING id, email;`
	var email string
	err = db.QueryRow(sqlStatement, id, "NewFirst", "NewLast").Scan(&id, &email)
	if err != nil {
		panic(err)
	}
	fmt.Println(id, email)

}
