import os

from sqlalchemy import Column, Integer, String, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


# 场景：包含名字和图片
class Place(Base):
    __tablename__ = 'places'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    image = Column(String)
    items = relationship('Item', back_populates='place')

    def __repr__(self):
        return "<Place(name='%s', image='%s')>" % (self.name, self.image)


# 物品：一件物品，包含名字、介绍、坐标、所属场景
class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    place_id = Column(Integer, ForeignKey('places.id'))
    place = relationship('Place', back_populates='items')
    x = Column(Integer)
    y = Column(Integer)

    def __repr__(self):
        return "<Item(name='%s', x='%d', y='%d')>" % (self.name, self.x, self.y)


# 初始化数据库并且用测试数据填充
def init_db():
    if os.path.exists('db.sqlite3'):
        os.remove('db.sqlite3')

    engine = create_engine('sqlite:///db.sqlite3')
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine)
    session = Session()

    for i in range(1, 8):
        name = '柜子' + str(i)
        image = 'images/{}.jpg'.format(str(i))
        place = Place(name=name, image=image)
        description = '这是一个手机'
        item1 = Item(name='手机', place=place, x=100, y=100, description=description)
        item2 = Item(name='毛巾', place=place, x=100, y=200, description=description)
        item3 = Item(name='打火机', place=place, x=100, y=300, description=description)
        item4 = Item(name='钱包', place=place, x=200, y=100, description=description)
        item5 = Item(name='书包', place=place, x=200, y=200, description=description)
        item6 = Item(name='港币', place=place, x=200, y=300, description=description)
        session.add_all([item1, item2, item3, item4, item5, item6])
    session.commit()


engine = create_engine('sqlite:///db.sqlite3')
Base.metadata.create_all(engine)
Session = sessionmaker(engine)
session = Session()