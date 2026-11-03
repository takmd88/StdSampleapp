import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from app import create_app

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

if __name__=="__main__": unittest.main()
