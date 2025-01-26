from fastapi import FastAPI , Response, status, HTTPException, Depends, Request
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
from prometheus_client import Counter, start_http_server,Histogram, Summary


 
# Initialize Prometheus metrics
REQUESTS_BY_PATH = Counter('http_requests_total_FastAPI', 'Total number of requests', labelnames=['path', 'method'])
ERRORS = Counter('http_errors_total_fastAPI', 'Total number of errors', labelnames=['status_code'])
LATENCY = Histogram('request_latency_seconds', 'Latency of HTTP requests in seconds', labelnames=['path', 'method'])
REQUEST_LATENCY = Summary('REQUEST_LATENCY_SECONDS', 'Latency of HTTP requests in seconds', ['path', 'method'])


start_http_server(7000)

# Create database models
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Middleware to measure latency
@app.middleware("http")
async def measure_latency(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Record request latency
    LATENCY.labels(path=request.url.path, method=request.method).observe(process_time)
    REQUEST_LATENCY.labels(path=request.url.path, method=request.method).observe(process_time)


    return response


# Define your routes
class Post(BaseModel):
    title: str
    content: str


@app.get("/")
def read_root():
    REQUESTS_BY_PATH.labels("/", 'get').inc()
    return {"Hello": "Welcome to my FastAPI practice World!!!"}


@app.get("/sqlalchemy")
def test_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).all()
    REQUESTS_BY_PATH.labels("/sqlalchemy", 'get').inc()
    return {"data": posts}


@app.get("/posts")
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).all()
    REQUESTS_BY_PATH.labels("/posts", 'get').inc()
    return {"data": posts}


@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_new_post(post: Post, db: Session = Depends(get_db)):
    new_post = models.Post(**post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    REQUESTS_BY_PATH.labels("/posts", 'post').inc()
    return {"data": new_post}


@app.get("/posts/{id}")
def get_post(id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        ERRORS.labels('404').inc()
        raise HTTPException(status_code=404, detail=f"The post with id: {id} was not found")
    REQUESTS_BY_PATH.labels("/posts/{id}", 'get').inc()
    return {"post details": post}


@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        ERRORS.labels('404').inc
