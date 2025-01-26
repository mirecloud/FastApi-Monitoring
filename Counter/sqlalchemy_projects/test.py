from fastapi import FastAPI , Response, status, HTTPException, Depends
from fastapi.params  import Body
from pydantic import BaseModel
from random import randrange
from sqlalchemy.orm import Session
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import psycopg
import time
from psycopg import connect, ClientCursor 
from psycopg.rows import dict_row
from sqlalchemy_projects import models
from sqlalchemy_projects.database import engine, SessionLocal, get_db
from prometheus_client import Counter, start_http_server,Histogram


 
REQUESTS_BY_PATH = Counter('http_requests_total_FastAPI','Total number of requests', labelnames=['path','method'])
ERRORS = Counter('http_errors_total_fastAPI', 'Total number of errors', labelnames=['status_code'])
#LATENCY= Histogram(request_latency_second)
start_http_server(8000)


models.Base.metadata.create_all(bind=engine)

app = FastAPI()
 
class Post(BaseModel):
    title: str
    content: str
     
  

@app.get("/")
def read_root():
    REQUESTS_BY_PATH.labels("/",'get').inc()
    return {"Hello": "Welcome to my Fastapi practice World!!!"}

@app.get("/sqlalchemy")
def test_posts(db: Session = Depends(get_db)):

    posts = db.query(models.Post).all()
    REQUESTS_BY_PATH.labels("/sqlalchemy",'get').inc()
    return {"data": posts}


@app.get("/posts")
def get_posts(db: Session = Depends(get_db)):
 
    posts = db.query(models.Post).all()
    print(posts)
    REQUESTS_BY_PATH.labels("/posts",'get').inc()
    return {"data": posts}

  
@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_new_post(post: Post, db: Session = Depends(get_db)):

    #new_post = models.Post(title=post.title, content=post.content, published=post.published)
    new_post = models.Post(**post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    REQUESTS_BY_PATH.labels("/posts",'post').inc() 
    return{"data": new_post}

@app.get("/posts/{id}")
def get_post(id: int, response: Response, db: Session = Depends(get_db)):
   
    posts = db.query(models.Post).filter(models.Post.id == id).first() # instead of .first we could put .all() but it would continue looking if there is no id=2, we already know only one id is equal 2
    if not posts:
        ERRORS.labels('404').inc()
        raise HTTPException(status_code=404, detail= f"the post with id: {id} was not found")
        
    print(posts)
    REQUESTS_BY_PATH.labels("/posts/id",'post').inc()
    return {"post details": posts}

@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db)):
  
    post = db.query(models.Post).filter(models.Post.id == id) # instead of .first we could put .all() but it would continue looking if there is no id=2, we already know only one id is equal 2

    if post.first() == None:
        ERRORS.labels('404').inc()  
        raise HTTPException(status_code=404, detail= f"the post with id: {id} was not found")  
          
    post.delete(synchronize_session=False) 
    db.commit()
    REQUESTS_BY_PATH.labels("/posts/id",'delete').inc()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.put("/posts/{id}")
def update_post(id: int, post: Post, db: Session = Depends(get_db)):
   
    # Rechercher l'objet correspondant
    post_query = db.query(models.Post).filter(models.Post.id == id)
    existing_post = post_query.first()

    if not existing_post:
        ERRORS.labels('404').inc()
        raise HTTPException(status_code=404, detail=f"The post with id: {id} was not found")
        

    # Mettre à jour avec les données envoyées
    post_query.update(post.model_dump(), synchronize_session=False)
    db.commit()
    REQUESTS_BY_PATH.labels("/posts/id",'update').inc()
    return {"data": "success", "updated_post": post_query.first()}



