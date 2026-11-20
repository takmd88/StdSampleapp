import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from app import close_db, create_app, get_db, validate_contact

class PortfolioTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.db=Path(self.tmp.name)/"test.db"
        self.client=create_app({"TESTING":True,"DATABASE":str(self.db),"SECRET_KEY":"test"}).test_client()
    def tearDown(self): self.tmp.cleanup()
    def test_index(self): self.assertEqual(self.client.get("/").status_code,200)
    def test_contact_saved(self):
        response=self.client.post("/contact",data={"name":"山田 太郎","email":"taro@example.com","subject":"開発相談","message":"相談したいです。"})
        self.assertEqual(response.status_code,302)
        with closing(sqlite3.connect(self.db)) as db: saved=db.execute("SELECT name,email FROM inquiries").fetchone()
        self.assertEqual(saved,("山田 太郎","taro@example.com"))
    def test_invalid_rejected(self):
        self.assertEqual(self.client.post("/contact",data={"name":"","email":"x","subject":"","message":""}).status_code,400)
        with closing(sqlite3.connect(self.db)) as db: self.assertEqual(db.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0],0)

    def test_contact_trimmed_and_redirected(self):
        response = self.client.post("/contact", data={
            "name": " 山田 太郎 ", "email": " taro@example.com ",
            "subject": " 開発相談 ", "message": " 相談したいです。\n",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/?sent=1#contact")
        with closing(sqlite3.connect(self.db)) as db:
            saved = db.execute("SELECT name, email, subject, message FROM inquiries").fetchone()
        self.assertEqual(saved, ("山田 太郎", "taro@example.com", "開発相談", "相談したいです。"))

    def test_honeypot_not_saved(self):
        response = self.client.post("/contact", data={"website": "spam"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/?sent=1#contact")
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0], 0)

    def test_database_connection_lifecycle_and_rollback(self):
        with self.client.application.app_context():
            db = get_db()
            self.assertIs(get_db(), db)
            with self.assertRaises(RuntimeError):
                with db:
                    db.execute(
                        "INSERT INTO inquiries (name, email, subject, message) VALUES (?, ?, ?, ?)",
                        ("name", "a@b", "subject", "message"),
                    )
                    raise RuntimeError("abort transaction")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0], 0)
        with self.assertRaises(sqlite3.ProgrammingError):
            db.execute("SELECT 1")
        with self.client.application.app_context():
            close_db()  # Teardown also handles contexts that never opened a connection.


class ContactValidationTest(unittest.TestCase):
    def test_length_boundaries(self):
        valid = {"name": "n" * 80, "email": "a" * 252 + "@b",
                 "subject": "s" * 120, "message": "m" * 2000}
        fields, errors = validate_contact(valid)
        self.assertEqual(fields, valid)
        self.assertEqual(errors, [])
        for key in valid:
            with self.subTest(field=key):
                _, errors = validate_contact({**valid, key: valid[key] + "x"})
                self.assertEqual(len(errors), 1)

    def test_missing_blank_and_invalid_email(self):
        self.assertEqual(len(validate_contact({})[1]), 4)
        blank = dict.fromkeys(("name", "email", "subject", "message"), " \n ")
        self.assertEqual(len(validate_contact(blank)[1]), 4)
        self.assertEqual(len(validate_contact({
            "name": "name", "email": "invalid", "subject": "subject", "message": "message",
        })[1]), 1)

if __name__=="__main__": unittest.main()
