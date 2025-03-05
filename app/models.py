from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey, Numeric, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID


Base = declarative_base()


class Account(Base):
    __tablename__ = 'account'

    id = Column(BigInteger, primary_key=True, index=True)
    external_id = Column(BigInteger, unique=True, default=0, nullable=False, comment='Id tg')
    first_name = Column(String(150), nullable=True)
    last_name = Column(String(150), nullable=True)
    username = Column(String(150), nullable=True)
    ticket = Column(Numeric(8, 2), default=1)
    limit = Column(Integer, default=1)
    is_sub = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_stars_verified = Column(Boolean, default=False)
    from_memhash = Column(Boolean, default=False)
    parent_id = Column(BigInteger, ForeignKey('account.id'), nullable=True, comment='parent')
    parent = relationship('Account', remote_side=[id], backref='referrals')
    wallet_address = Column(String(250), nullable=True)


class Raffle(Base):
    __tablename__ = 'raffle'

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(250), nullable=True)
    date_create = Column(DateTime, default=datetime.utcnow)
    date_end = Column(DateTime, default=datetime.utcnow)
    date_all_stars_end = Column(DateTime, default=datetime.utcnow)
    status = Column(String(250), default='active')
    status_all_stars = Column(String(250), default='active')
    stars = Column(Integer, default=0)
    prize_fund = Column(String(250), default='50,000 memhash')


class Prize(Base):
    __tablename__ = 'prize'

    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=True)
    raffle_id = Column(BigInteger, ForeignKey('raffle.id'), nullable=False)
    raffle = relationship("Raffle", backref="prize")
    count = Column(Integer, default=0)
    amount = Column(Integer, default=0)
    currency = Column(String(250), default='memhash')
    is_stars = Column(Boolean, default=False)


class Ticket(Base):
    __tablename__ = 'ticket'

    id = Column(Integer, primary_key=True)
    account_id = Column(BigInteger, ForeignKey('account.id'), nullable=False)
    account = relationship("Account", backref="tickets")
    raffle_id = Column(BigInteger, ForeignKey('raffle.id'), nullable=False)
    raffle = relationship("Raffle", backref="tickets")
    prize_id = Column(Integer, ForeignKey("prize.id", ondelete="SET NULL"), nullable=True)
    prize = relationship("Prize", backref="tickets")
    date_create = Column(DateTime(timezone=True), default=datetime.utcnow)
    is_win = Column(Boolean, default=False)
    is_payout = Column(Boolean, default=False)
    is_win_all_stars = Column(Boolean, default=False)
    is_stars = Column(Boolean, default=False)
    is_refund = Column(Boolean, default=False)


