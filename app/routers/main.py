import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from typing import Annotated, List

from app.config.settings import SECRET_KEY, ALGORITHM
from app.schema import TicketSchema, PrizeSchema, TicketWinnersSchema, TicketWinnersStarsSchema
from app.models import Ticket, Raffle, Prize
from app.config.db import get_session


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
Session = Annotated[AsyncSession, Depends(get_session)]
templates = Jinja2Templates(directory="app/templates")


async def auth(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/", response_class=HTMLResponse)
async def raffles_view(session: Session, request: Request):
    query = select(Raffle).order_by(desc(Raffle.id))
    result = await session.execute(query)
    raffles = result.scalars().all()

    return templates.TemplateResponse("raffles.html", {"request": request, "raffles": raffles})


@router.get("/{raffle_id}", response_model=List[PrizeSchema])
async def prize_by_raffle_view(raffle_id: int, session: Session):
    query = select(Prize).where(Prize.raffle_id == raffle_id)
    result = await session.execute(query)
    raffle = result.scalars().all()

    if raffle is None:
        raise HTTPException(status_code=404, detail="Not found")

    return raffle


@router.get("/tickets/{raffle_id}", response_model=List[TicketSchema])
async def tickets_by_raffle_view(raffle_id: int, session: Session, is_stars: bool | None = Query(None),
                                 is_win: bool | None = Query(None), is_win_all_stars: bool | None = Query(None),
):
    query = select(Ticket).where(Ticket.raffle_id == raffle_id, Ticket.is_refund == False)

    if is_stars is not None:
        query = query.where(Ticket.is_stars == is_stars)
    if is_win is not None:
        query = query.where(Ticket.is_win == is_win)
    if is_win_all_stars is not None:
        query = query.where(Ticket.is_win_all_stars == is_win_all_stars)

    result = await session.execute(query)
    tickets = result.scalars().all()

    return tickets


@router.post("/raffle/{raffle_id}", response_model=List[TicketWinnersSchema])
async def do_reward_view(raffle_id: int, session: Session, token: str = Depends(auth)):

    query = select(Raffle).where(Raffle.id == raffle_id, Raffle.status == 'complete')
    result = await session.execute(query)
    raffle = result.scalars().first()

    if not raffle:
        raise HTTPException(status_code=404, detail="Not found")

    prizes_query = select(Prize).filter(Prize.raffle_id == raffle_id, Prize.is_stars == False)
    prizes_result = await session.execute(prizes_query)
    prizes = prizes_result.scalars().all()

    result = []

    for prize in prizes:
        tickets_query = select(Ticket).filter(
            Ticket.raffle_id == raffle_id, Ticket.is_win == False, Ticket.prize_id == None, Ticket.is_refund == False
        ).order_by(func.random()).limit(prize.count)

        tickets_result = await session.execute(tickets_query)
        tickets = tickets_result.scalars().all()

        updates = []
        for ticket in tickets:
            updates.append({'id': ticket.id, 'is_win': True, 'prize_id': prize.id})
            result.append({
                'id': ticket.id, 'raffle_id': raffle.id, 'is_win': True, 'prize_id': prize.id,
                'account_id': ticket.account_id, 'is_stars': ticket.is_stars
            })
        await session.run_sync(lambda sync_session: sync_session.bulk_update_mappings(Ticket, updates))

        await session.commit()

    return result


@router.post("/raffle/{raffle_id}/stars", response_model=List[TicketWinnersStarsSchema])
async def do_reward_all_stars_view(raffle_id: int, session: Session, token: str = Depends(auth)):
    query = select(Raffle).where(
        Raffle.id == raffle_id, Raffle.status == 'complete', Raffle.status_all_stars == 'complete'
    )
    result = await session.execute(query)
    raffle = result.scalars().first()

    if not raffle:
        raise HTTPException(status_code=404, detail="Not found")

    prizes_query = select(Prize).filter(
        Prize.raffle_id == raffle_id, Prize.is_stars == True
    )
    prizes_result = await session.execute(prizes_query)
    prizes = prizes_result.scalars().all()

    result = []

    for prize in prizes:
        tickets_query = select(Ticket).filter(
            Ticket.raffle_id == raffle_id, Ticket.is_win_all_stars == False, Ticket.is_stars == True,
            Ticket.prize_id == None, Ticket.is_refund == False
        ).order_by(func.random()).limit(prize.count)

        tickets_result = await session.execute(tickets_query)
        tickets = tickets_result.scalars().all()

        updates = []
        for ticket in tickets:
            updates.append({'id': ticket.id, 'is_win_all_stars': True, 'prize_id': prize.id})
            result.append({'id': ticket.id, 'raffle_id': raffle.id, 'is_win_all_stars': True, 'prize_id': prize.id,
                           'account_id': ticket.account_id, 'is_stars': ticket.is_stars})

        await session.run_sync(lambda sync_session: sync_session.bulk_update_mappings(Ticket, updates))
        await session.commit()

    return result


@router.get("/shaffle/{raffle_id}", response_model=List[TicketWinnersSchema])
async def do_shaffle_view(raffle_id: int, session: Session):

    query = select(Raffle).where(Raffle.id == raffle_id, Raffle.status == 'active')
    result = await session.execute(query)
    raffle = result.scalars().first()

    if not raffle:
        raise HTTPException(status_code=404, detail="Not found")

    prizes_query = select(Prize).filter(Prize.raffle_id == raffle_id, Prize.is_stars == False)
    prizes_result = await session.execute(prizes_query)
    prizes = prizes_result.scalars().all()

    result = []

    for prize in prizes:
        tickets_query = select(Ticket).filter(
            Ticket.raffle_id == raffle_id, Ticket.is_win == False, Ticket.prize_id == None, Ticket.is_refund == False
        ).order_by(func.random()).limit(prize.count)

        tickets_result = await session.execute(tickets_query)
        tickets = tickets_result.scalars().all()

        for ticket in tickets:
            result.append({
                'id': ticket.id, 'raffle_id': raffle.id, 'is_win': True, 'prize_id': prize.id,
                'account_id': ticket.account_id, 'is_stars': ticket.is_stars
            })

    return result


@router.get("/shaffle/{raffle_id}/stars", response_model=List[TicketWinnersStarsSchema])
async def do_shaffle_all_stars_view(raffle_id: int, session: Session):
    query = select(Raffle).where(
        Raffle.id == raffle_id, Raffle.status == 'active', Raffle.status_all_stars == 'active'
    )
    result = await session.execute(query)
    raffle = result.scalars().first()

    if not raffle:
        raise HTTPException(status_code=404, detail="Not found")

    prizes_query = select(Prize).filter(
        Prize.raffle_id == raffle_id, Prize.is_stars == True
    )
    prizes_result = await session.execute(prizes_query)
    prizes = prizes_result.scalars().all()

    result = []

    for prize in prizes:
        tickets_query = select(Ticket).filter(
            Ticket.raffle_id == raffle_id, Ticket.is_win_all_stars == False, Ticket.is_stars == True,
            Ticket.prize_id == None, Ticket.is_refund == False
        ).order_by(func.random()).limit(prize.count)

        tickets_result = await session.execute(tickets_query)
        tickets = tickets_result.scalars().all()

        for ticket in tickets:
            result.append({'id': ticket.id, 'raffle_id': raffle.id, 'is_win_all_stars': True, 'prize_id': prize.id,
                           'account_id': ticket.account_id, 'is_stars': ticket.is_stars})
    return result
