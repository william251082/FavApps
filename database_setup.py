import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

# Build a one-to-many relationship b/w AppMaker and its Apps
# Main Category : AppMaker, Sub-Category: Apps built by the AppMaker
# A User can create an AppMaker and create sub-categories of its Apps
# Learn Jinja


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class AppMaker(Base):
    __tablename__ = 'appmaker'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class FavApps(Base):
    __tablename__ = 'favapps'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    price = Column(String(8))
    catch_phrase = Column(String(250))
    appmaker_id = Column(Integer, ForeignKey('appmaker.id'))
    appmaker = relationship(AppMaker)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'price': self.price,
            'catch_phrase': self.catch_phrase,
        }


engine = create_engine('sqlite:///appmakerinfowithusers.db')


Base.metadata.create_all(engine)
