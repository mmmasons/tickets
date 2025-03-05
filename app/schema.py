from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PrizeSchema(BaseModel):
    id: int
    title: str
    raffle_id: int
    count: int
    amount: int
    currency: str
    is_stars: bool


class RaffleSchema(BaseModel):
    id: int
    title: str | None
    date_create: datetime
    date_end: datetime
    date_all_stars_end: datetime
    status: str
    status_all_stars: str
    count: int
    stars: int
    prize_fund: str

    class Config:
        from_attributes = True


class TicketSchema(BaseModel):
    id: int
    account_id: int
    raffle_id: int
    prize_id: Optional[int]
    date_create: datetime
    is_win: bool
    is_win_all_stars: bool
    is_stars: bool

    class Config:
        from_attributes = True


class TicketWinnersSchema(BaseModel):
    id: int
    account_id: int
    raffle_id: int
    prize_id: int
    is_win: bool
    is_stars: bool

    class Config:
        from_attributes = True


class TicketWinnersStarsSchema(BaseModel):
    id: int
    account_id: int
    raffle_id: int
    prize_id: int
    is_win_all_stars: bool
    is_stars: bool

    class Config:
        from_attributes = True


class TokenSchema(BaseModel):
    access_token: str
