# Example: FastAPI endpoint with typing

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.post("/items")
async def create_item(item: Item) -> dict:
    if item.price < 0:
        raise HTTPException(status_code=400, detail="price must be >= 0")
    return {"name": item.name, "price": item.price}
```
