import json
import os
import redis
from datetime import timedelta
from fastapi import Depends, FastAPI, HTTPException, status, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from . import crud, models, schemas, security
from .database import SessionLocal, engine
from .ws_manager import manager

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_client = redis.Redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.get("/messages/", response_model=list[schemas.Message])
def read_messages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    messages = crud.get_messages(db, skip=skip, limit=limit)
    return messages


@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str, db: Session = Depends(get_db)):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # On message, create in DB and publish to Redis
            message_data = schemas.Message(text=data, username=username)
            user = crud.get_user_by_username(db, username=username)
            crud.create_message(db, message=message_data, user_id=user.id)

            # Publish to redis so other server instances can broadcast it
            redis_client.publish("chat_channel", json.dumps(message_data.dict()))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        manager.disconnect(websocket)


# A background task to listen to Redis and broadcast messages
@app.on_event("startup")
async def startup_event():
    import asyncio
    async def redis_listener():
        pubsub = redis_client.pubsub()
        pubsub.subscribe("chat_channel")
        for message in pubsub.listen():
            if message['type'] == 'message':
                await manager.broadcast(message['data'])

    asyncio.create_task(redis_listener())