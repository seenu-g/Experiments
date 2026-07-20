"""
Unit tests for each individual step of the SQL agent pipeline in sqlite3_agent.py.

Run with: python -m unittest test_sqlite3_agent -v

Each test exercises exactly one step (list tables / schema / draft query / checker /
run query / final answer) so a failure pinpoints which step broke, instead of only
finding out after the autonomous multi-turn agent loop (sqlite3_agent_auto.py) goes
quiet partway through.
"""
import unittest

from sqlite3_agent import (
    DEFAULT_QUESTION,
    answer_step,
    checker_step,
    draft_query_step,
    ensure_chinook_db,
    list_tables_step,
    run_query_step,
    schema_step,
)

QUESTION = DEFAULT_QUESTION


class TestSqlAgentSteps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_chinook_db()

    def test_01_list_tables(self):
        tables = list_tables_step()
        self.assertIn("Track", tables)
        self.assertIn("Genre", tables)

    def test_02_schema(self):
        relevant_tables, schema = schema_step("Track, Genre", QUESTION)
        self.assertIn("Track", relevant_tables)
        self.assertIn("CREATE TABLE", schema)
        self.assertIn("Milliseconds", schema)

    def test_03_draft_query(self):
        schema = (
            "CREATE TABLE Track (TrackId INTEGER, GenreId INTEGER, Milliseconds INTEGER);\n"
            "CREATE TABLE Genre (GenreId INTEGER, Name TEXT);"
        )
        draft_query = draft_query_step(schema, QUESTION)
        self.assertIn("SELECT", draft_query.upper())
        self.assertIn("AVG", draft_query.upper())

    def test_04_checker(self):
        draft_query = (
            "SELECT Name, AVG(Milliseconds) FROM Track "
            "JOIN Genre ON Track.GenreId = Genre.GenreId GROUP BY Name"
        )
        checked_query = checker_step(draft_query)
        self.assertIn("SELECT", checked_query.upper())

    def test_05_run_query(self):
        result = run_query_step(
            "SELECT Genre.Name, AVG(Track.Milliseconds) AS AvgLength "
            "FROM Track JOIN Genre ON Track.GenreId = Genre.GenreId "
            "GROUP BY Genre.Name ORDER BY AvgLength DESC LIMIT 1;"
        )
        self.assertIn("Sci Fi & Fantasy", result)

    def test_06_answer(self):
        answer = answer_step(QUESTION, "[('Sci Fi & Fantasy', 2911783.04)]")
        self.assertIn("fantasy", answer.lower())


if __name__ == "__main__":
    unittest.main()
