from pydantic import BaseModel


class BingoSquare(BaseModel):
    id: int
    label: str
    category: str


class BingoBoard(BaseModel):
    user_id: str
    month: str          # "2026-05"
    squares: list[BingoSquare]
    checked: list[int] = [13]   # 13 is FREE, checked by default
