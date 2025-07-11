import json
import uuid
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --- Constants ---
DB_FILE = "db.json"

# --- Pydantic Models ---
class TodoItem(BaseModel):
    """
    Represents a todo item.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique identifier for the todo item")
    title: str = Field(..., description="The title of the todo item", min_length=1)
    description: Optional[str] = Field(None, description="An optional description of the todo item")
    completed: bool = Field(False, description="Indicates if the todo item is completed")

class TodoCreate(BaseModel):
    """
    Model for creating a new todo item. ID is generated automatically.
    """
    title: str = Field(..., description="The title of the todo item", min_length=1)
    description: Optional[str] = Field(None, description="An optional description of the todo item")
    completed: bool = Field(False, description="Indicates if the todo item is completed")

class TodoUpdate(BaseModel):
    """
    Model for updating an existing todo item. All fields are optional.
    """
    title: Optional[str] = Field(None, description="The new title of the todo item", min_length=1)
    description: Optional[str] = Field(None, description="The new optional description of the todo item")
    completed: Optional[bool] = Field(None, description="The new completion status of the todo item")

# --- Database Helper Functions ---
def load_db() -> List[TodoItem]:
    """
    Loads todo items from the JSON database file.
    Returns an empty list if the file doesn't exist or is empty.
    """
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            return [TodoItem(**item) for item in data]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_db(todos: List[TodoItem]):
    """
    Saves the list of todo items to the JSON database file.
    """
    with open(DB_FILE, "w") as f:
        json_data = [todo.model_dump(mode='json') for todo in todos]
        json.dump(json_data, f, indent=4)

# --- FastAPI Application ---
app = FastAPI(
    title="Todo List API",
    description="A simple API to manage a list of todo items.",
    version="0.1.0"
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- API Endpoints ---
@app.post("/todos/", response_model=TodoItem, status_code=status.HTTP_201_CREATED, summary="Create a new todo item")
async def create_todo(todo_create: TodoCreate):
    """
    Create a new todo item.

    - **title**: The title of the todo item (required).
    - **description**: An optional description of the todo item.
    - **completed**: The completion status of the todo item (defaults to false).
    """
    todos = load_db()
    new_todo = TodoItem(id=uuid.uuid4(), **todo_create.model_dump())
    todos.append(new_todo)
    save_db(todos)
    return new_todo

@app.get("/todos/", response_model=List[TodoItem], summary="Get all todo items")
async def get_all_todos():
    """
    Retrieve a list of all todo items.
    """
    return load_db()

@app.get("/todos/{todo_id}", response_model=TodoItem, summary="Get a specific todo item by ID")
async def get_todo_by_id(todo_id: uuid.UUID):
    """
    Retrieve a specific todo item by its unique ID.

    - **todo_id**: The UUID of the todo item to retrieve.
    """
    todos = load_db()
    for todo in todos:
        if todo.id == todo_id:
            return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo item not found")

@app.put("/todos/{todo_id}", response_model=TodoItem, summary="Update a todo item")
async def update_todo(todo_id: uuid.UUID, todo_update: TodoUpdate):
    """
    Update an existing todo item.
    Only provided fields will be updated.

    - **todo_id**: The UUID of the todo item to update.
    - **title**: The new title (optional).
    - **description**: The new description (optional).
    - **completed**: The new completion status (optional).
    """
    todos = load_db()
    for index, current_todo in enumerate(todos):
        if current_todo.id == todo_id:
            update_data = todo_update.model_dump(exclude_unset=True)
            updated_todo = current_todo.model_copy(update=update_data)
            todos[index] = updated_todo
            save_db(todos)
            return updated_todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo item not found")

@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a todo item")
async def delete_todo(todo_id: uuid.UUID):
    """
    Delete a todo item by its unique ID.

    - **todo_id**: The UUID of the todo item to delete.
    """
    todos = load_db()
    updated_todos = [todo for todo in todos if todo.id != todo_id]
    if len(todos) == len(updated_todos):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo item not found")
    save_db(updated_todos)
    return None

# To run this application:
# 1. Install FastAPI and Uvicorn: pip install fastapi uvicorn
# 2. Run Uvicorn: uvicorn main:app --reload
# 3. Open your browser at http://127.0.0.1:8000/docs for the API documentation.
