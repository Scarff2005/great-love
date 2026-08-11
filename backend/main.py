from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama

from database import engine, Base, SessionLocal
from models import Memory


app = FastAPI()

Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


@app.get("/")
def home():
    return {
        "message": "Great Love backend is alive 🤖❤️"
    }


def save_memory(category: str, memory_text: str):
    db = SessionLocal()

    try:
        memory = Memory(
            user_id="default_user",
            category=category,
            memory=memory_text
        )

        db.add(memory)
        db.commit()

    finally:
        db.close()


def get_memories():
    db = SessionLocal()

    try:
        memories = db.query(Memory).all()

        return [
            {
                "id": memory.id,
                "category": memory.category,
                "memory": memory.memory
            }
            for memory in memories
        ]

    finally:
        db.close()


def update_memory(memory_id: int, category: str, memory_text: str):
    db = SessionLocal()

    try:
        memory = db.query(Memory).filter(
            Memory.id == memory_id
        ).first()

        if memory:
            memory.category = category
            memory.memory = memory_text
            db.commit()

            return True

        return False

    finally:
        db.close()


def delete_memory(memory_id: int):
    db = SessionLocal()

    try:
        memory = db.query(Memory).filter(
            Memory.id == memory_id
        ).first()

        if memory:
            db.delete(memory)
            db.commit()

            return True

        return False

    finally:
        db.close()


def find_related_memory(category: str, new_memory: str):
    db = SessionLocal()

    try:
        memories = db.query(Memory).filter(
            Memory.category == category
        ).all()

        if not memories:
            return None

        memory_text = "\n".join(
            f"{memory.id}: {memory.memory}"
            for memory in memories
        )

        response = ollama.chat(
            model="llama3.2",
            messages=[
                {
                    "role": "system",
                    "content": """
You determine whether a new piece of user information
updates an existing memory.

Return ONLY the ID of the existing memory that should be
updated.

If none of the existing memories are related, return:

NONE

Do not explain your answer.
"""
                },
                {
                    "role": "user",
                    "content": f"""
Existing memories:

{memory_text}

New information:

{new_memory}
"""
                }
            ]
        )

        result = response["message"]["content"].strip()

        if result.upper() == "NONE":
            return None

        try:
            return int(result)

        except ValueError:
            return None

    finally:
        db.close()


def extract_memory(user_message: str):
    response = ollama.chat(
        model="llama3.2",
        messages=[
            {
                "role": "system",
                "content": """
You are Great Love's memory extraction system.

Determine whether the user's message contains useful personal
information that should be remembered.

If there is nothing useful to remember, return exactly:

NONE

If there is useful information, return exactly:

CATEGORY|MEMORY

Allowed categories:

personal
education
preference
project
general

Examples:

User:
"My favorite programming language is Java."

Return:
preference|User's favorite programming language is Java.

User:
"I study Applications Development."

Return:
education|User studies Applications Development.

User:
"My name is Sibusiso."

Return:
personal|User's name is Sibusiso.

User:
"I'm building Great Love."

Return:
project|User is building Great Love.

User:
"What's the weather today?"

Return:
NONE

User:
"Hello."

Return:
NONE

Do not explain your answer.
Do not use markdown.
"""
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    result = response["message"]["content"].strip()

    if result.upper() == "NONE":
        return None

    if "|" not in result:
        return None

    category, memory = result.split("|", 1)

    return {
        "category": category.strip(),
        "memory": memory.strip()
    }


def detect_forget_request(user_message: str):
    response = ollama.chat(
        model="llama3.2",
        messages=[
            {
                "role": "system",
                "content": """
Determine whether the user is asking Great Love to forget
or delete something from its memory.

Return:

YES

if the user is clearly asking to forget/delete something.

Otherwise return:

NO

Return only YES or NO.
"""
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    result = response["message"]["content"].strip().upper()

    return result == "YES"


def find_memory_to_forget(user_message: str):
    memories = get_memories()

    if not memories:
        return None

    memory_text = "\n".join(
        f"{memory['id']}: {memory['memory']}"
        for memory in memories
    )

    response = ollama.chat(
        model="llama3.2",
        messages=[
            {
                "role": "system",
                "content": """
Find the memory that the user wants Great Love to forget.

Return ONLY the ID of the memory.

If no memory matches, return:

NONE

Do not explain your answer.
"""
            },
            {
                "role": "user",
                "content": f"""
Stored memories:

{memory_text}

User request:

{user_message}
"""
            }
        ]
    )

    result = response["message"]["content"].strip()

    if result.upper() == "NONE":
        return None

    try:
        return int(result)

    except ValueError:
        return None


@app.post("/memory")
def create_memory(memory: str, category: str = "general"):
    save_memory(category, memory)

    return {
        "message": "Memory saved successfully."
    }


@app.get("/memories")
def memories():
    return get_memories()


@app.delete("/memory/{memory_id}")
def remove_memory(memory_id: int):
    deleted = delete_memory(memory_id)

    if not deleted:
        return {
            "success": False,
            "message": "Memory not found."
        }

    return {
        "success": True,
        "message": "Memory deleted successfully."
    }


@app.post("/chat")
def chat(request: ChatRequest):

    latest_user_message = request.messages[-1].content

    # Check if the user wants Great Love to forget something
    if detect_forget_request(latest_user_message):

        memory_id = find_memory_to_forget(latest_user_message)

        if memory_id is not None:
            delete_memory(memory_id)

    else:

        # Check whether the message contains useful information
        new_memory = extract_memory(latest_user_message)

        if new_memory:

            # Check whether this information updates an existing memory
            existing_memory_id = find_related_memory(
                new_memory["category"],
                new_memory["memory"]
            )

            if existing_memory_id is not None:
                update_memory(
                    existing_memory_id,
                    new_memory["category"],
                    new_memory["memory"]
                )

            else:
                save_memory(
                    new_memory["category"],
                    new_memory["memory"]
                )

    memories = get_memories()

    messages = [
        {
            "role": "system",
            "content": f"""
You are Great Love, a personal AI assistant.

You were created by Sibusiso Dlamini.

Sibusiso is your creator and the person developing you.

Your name is Great Love.

If someone asks who you are, identify yourself as Great Love.

If someone asks who created you, say that Sibusiso Dlamini
created you.

Do not claim that you created Sibusiso.
Do not claim that Sibusiso is your creation.

Here are memories you have stored about the user:

{memories}

Use these memories when they are relevant to the conversation.

If the user has just asked you to forget something and it was
successfully removed, acknowledge that naturally.

Do not mention the memory database unless the user asks about
how your memory works.
"""
        }
    ]

    messages.extend(
        {
            "role": message.role,
            "content": message.content
        }
        for message in request.messages
    )

    response = ollama.chat(
        model="llama3.2",
        messages=messages
    )

    return {
        "reply": response["message"]["content"]
    }