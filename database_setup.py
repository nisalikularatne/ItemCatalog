from sqlalchemy import ForeignKey,Column,Integer,String
import sys
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy import create_engine

Base=declarative_base()

class Restaurant(Base):

    __tablename__='restaurant'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    items=RelationshipProperty("MenuItem")


class MenuItem(Base):
    __tablename__ = 'menu_item'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    course=Column(String(250))
    description = Column(String(250))
    price=Column(String(8))
    restaurant_id = Column(Integer,ForeignKey('restaurant.id'))
    restaurant=RelationshipProperty(Restaurant)


engine=create_engine('sqlite:///restaurantmenu.db')
Base.metadata.create_all(engine)
