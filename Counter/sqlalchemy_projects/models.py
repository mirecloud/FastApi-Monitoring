from sqlalchemy.sql.expression import null
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy_projects.database import Base
from sqlalchemy import Integer, Column, String, Boolean
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
 
class Post(Base):
    __tablename__ = "postsecond"

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    published = Column(Boolean, server_default="true", nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))