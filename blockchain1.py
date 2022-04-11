import uvicorn
from fastapi import FastAPI

from class_user import User

app = FastAPI()
user1 = User()

if __name__ == "__main__":
    port = 1000
    uvicorn.run("__main__:app", host=user1.host, port=port)
