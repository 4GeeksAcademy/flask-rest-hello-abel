from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
import sys
from graphviz import Digraph

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    full_name = Column(String(120))
    bio = Column(Text)
    website = Column(String(200))
    is_private = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="author",
                         cascade="all, delete-orphan")
    comments = relationship(
        "Comment", back_populates="author", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="user",
                         cascade="all, delete-orphan")
    following = relationship("Follow", foreign_keys='Follow.follower_id',
                             back_populates="follower", cascade="all, delete-orphan")
    followers = relationship("Follow", foreign_keys='Follow.followed_id',
                             back_populates="followed", cascade="all, delete-orphan")

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "bio": self.bio,
            "website": self.website,
            "is_private": self.is_private,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Post(db.Model):
    __tablename__ = 'post'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    caption = Column(Text)
    location = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_archived = Column(Boolean, default=False)

    author = relationship("User", back_populates="posts")
    media = relationship("Media", back_populates="post",
                         cascade="all, delete-orphan")
    comments = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="post",
                         cascade="all, delete-orphan")


class Media(db.Model):
    __tablename__ = 'media'
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('post.id'), nullable=False)
    media_type = Column(String(20))
    url = Column(String(300), nullable=False)
    order = Column(Integer, default=0)

    post = relationship("Post", back_populates="media")


class Comment(db.Model):
    __tablename__ = 'comment'
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('post.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    parent_id = Column(Integer, ForeignKey('comment.id'), nullable=True)

    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")
    replies = relationship("Comment", backref='parent', remote_side=[
                           id], cascade="all, delete-orphan")


class Like(db.Model):
    __tablename__ = 'like'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('post.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="likes")
    post = relationship("Post", back_populates="likes")


class Follow(db.Model):
    __tablename__ = 'follow'
    id = Column(Integer, primary_key=True)
    follower_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    followed_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_accepted = Column(Boolean, default=True)

    follower = relationship("User", foreign_keys=[
                            follower_id], back_populates="following")
    followed = relationship("User", foreign_keys=[
                            followed_id], back_populates="followers")


if __name__ == '__main__':
    import os
    from sqlalchemy import create_engine

    def build_graph(metadata, name, nodesep='0.25', ranksep='0.5', rankdir='TB'):
        g = Digraph(name=name, format='png')
        g.attr('graph', nodesep=str(nodesep), ranksep=str(ranksep), rankdir=rankdir)
        g.attr('node', shape='record')
        tables = list(metadata.tables.items())
        for tname, table in tables:
            fields = []
            for col in table.columns:
                colname = col.name
                if col.primary_key:
                    colname = colname + ' (PK)'
                fields.append(colname + r'\l')
            label = '{' + tname + '|' + ''.join(fields) + '}'
            g.node(tname, label=label)
        for tname, table in tables:
            for col in table.columns:
                for fk in col.foreign_keys:
                    target = fk.column.table.name
                    g.edge(tname, target)
        return g

    try:
        tmp_db = 'tmp_instagram.db'
        if os.path.exists(tmp_db):
            os.remove(tmp_db)
        engine = create_engine(f'sqlite:///{tmp_db}')
        db.metadata.create_all(engine)
        metadata = db.metadata
        g1 = build_graph(metadata, 'compact', nodesep='0.25', ranksep='0.5', rankdir='TB')
        g1.render('diagram_compact', cleanup=True)
        g2 = build_graph(metadata, 'spaced', nodesep='1.0', ranksep='1.2', rankdir='TB')
        g2.render('diagram_spaced', cleanup=True)
        g3 = build_graph(metadata, 'symmetric', nodesep='1.2', ranksep='1.0', rankdir='LR')
        g3.render('diagram_symmetric', cleanup=True)
        os.replace('diagram_spaced.png', 'diagram.png')
    finally:
        try:
            if os.path.exists(tmp_db):
                os.remove(tmp_db)
        except Exception:
            pass
