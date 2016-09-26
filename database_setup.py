from sqlalchemy import ForeignKey,Column,Integer,String
import sys
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy import create_engine

Base=declarative_base()

#create User table
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    category = RelationshipProperty("Category")

#create category table
class Category(Base):

    __tablename__='category'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    items=RelationshipProperty("CategoryItem")
    user_id = Column(Integer, ForeignKey('user.id'))
    user = RelationshipProperty(User)

#JSONIFY
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


#create table item for each category
class CategoryItem(Base):
    __tablename__ = 'category_item'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    price=Column(String(8))
    category_id = Column(Integer,ForeignKey('category.id'))
    category=RelationshipProperty(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = RelationshipProperty("User")


#JSONIFY
    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'price': self.price,

        }


#engine creation
engine=create_engine('sqlite:///categorywithitems.db')
Base.metadata.create_all(engine)
