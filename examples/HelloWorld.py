# -*- coding: utf-8 -*-
import logging
import datetime
from restlet.application import RestletApplication
from restlet.handler import RestletHandler, encoder, decoder, route
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Table, Column, Integer, String, Sequence, MetaData, DateTime, func,
                        ForeignKey, Text, SmallInteger, Boolean, Numeric)
from sqlalchemy.orm import relationship, backref
_logger = logging.getLogger('tornado.restlet')

Base = declarative_base()


group2permission_table = Table('groups2permissions', Base.metadata,
                               Column('group_id', Integer, ForeignKey('groups.id', ondelete='CASCADE')),
                               Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE')))


class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, Sequence('group_id_seq'), primary_key=True)
    name = Column(String(50))
    users = relationship('User', backref="group", cascade="all, delete, delete-orphan",
                         passive_deletes=True)
    permissions = relationship('Permission', secondary=group2permission_table, passive_deletes=True)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    fullname = Column(String(50), nullable=True)
    password = Column(String(40), nullable=True)
    key = Column(String(32), nullable=True, doc='Another key')
    created = Column(DateTime, default=func.NOW())
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)


class Permission(Base):
    __tablename__ = 'permissions'
    id = Column(Integer, Sequence('permission_id_seq'), primary_key=True)
    name = Column(String(24), unique=True, nullable=False)
    description = Column(String(128), nullable=True)


class GroupHandler(RestletHandler):
    class Meta:
        table = Group


class PermissionHandler(RestletHandler):
    class Meta:
        table = Permission


class UserHandler(RestletHandler):
    """UserHandler to process User table."""
    def __init__(self, *args, **kwargs):
        super(UserHandler, self).__init__(*args, **kwargs)
        self.t1 = datetime.datetime.now()
        self.t2 = None

    def on_finish(self):
        self.t2 = datetime.datetime.now()
        _logger.info('Total Spent: %s', self.t2 - self.t1)

    class Meta:
        table = User
        allowed = ('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS')
        denied = None  # Can be a tuple of HTTP METHODs
        changable = ('fullname', 'password')  # None will make all fields changable
        readonly = ('name', 'id')  # None means no field is read only
        invisible = ('password', )  # None means no fields is invisible
        encoders = None  # {'password': lambda x, obj: hashlib.new('md5', x).hexdigest()}
                             # or use decorator @encoder(*fields)
        decoders = None  # User a dict or decorator @decoder(*fields)
        generators = None  # User a dict or decorator @generator(*fields)
        extensible = None  # None means no fields is extensible or a tuple with fields.

    @encoder('password')
    def password_encoder(passwd, inst=None):  # All the encoder/decoder/generator/validator can not bound
    # to class or instance
        import hashlib
        return hashlib.new('md5', passwd).hexdigest()

    @route(r'/(?P<uid>[0-9]+)/login', 'POST', 'PUT')
    @route(r'/login', 'POST', 'PUT')
    def do_login(self, *args, **kwargs):
        _logger.info("OK, It's done!: %s, %s, %s", args, kwargs, self.request.arguments)
        self.write("OK, It's done!: %s, %s" % (args, kwargs))


if __name__ == "__main__":
    import tornado.ioloop
    logging.basicConfig(level=logging.DEBUG)
    application = RestletApplication([UserHandler.route_to('/users'),
                                      GroupHandler.route_to('/groups'),
                                      PermissionHandler.route_to('/permissions')],
                                     dburi='postgresql://postgres:postgres@localhost/test',  # 'sqlite:///:memory:',
                                     loglevel='DEBUG', debug=True, dblogging=True)
    if True:
        Base.metadata.create_all(application.db_engine)
        session = application.new_db_session()
        group1 = Group(name='Group 1')
        group2 = Group(name='Group 2')

        p1 = Permission(name='Read')
        p2 = Permission(name='Update')
        p3 = Permission(name='Create')
        p4 = Permission(name='Delete')

        group1.permissions = [p1, p2, p3, p4]
        group2.permissions = [p1, p2]

        def password_encoder(passwd, inst=None):  # All the encoder/decoder/generator/validator can not bound
        # to class or instance
            import hashlib
            return hashlib.new('md5', passwd).hexdigest()

        u1 = User(name='u1', fullname='User 1', password=password_encoder('password 1'), key='key 1', group=group1)
        u2 = User(name='u2', fullname='User 2', password=password_encoder('password 2'), key='key 2', group=group2)
        u3 = User(name='u3', fullname='User 3', password=password_encoder('password 3'), key='key 3', group=group1)
        u4 = User(name='u4', fullname='User 4', password=password_encoder('password 4'), key='key 4', group=group2)

        session.add_all([group1, group2])
        session.commit()

    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()