from sqlalchemy import Column, Integer, String, TIMESTAMP, create_engine, ForeignKey, func, LargeBinary, Text, \
    Boolean, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
import json
from references import LOCATIONS
from typing import Union, Any, Optional, List


Base = declarative_base()


class UserDb(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True, nullable=False)
    name = Column(String(100), nullable=True)
    fullname = Column(String(200), nullable=False)
    photo = Column(LargeBinary, nullable=False)
    age = Column(BigInteger, nullable=False)
    types_activity = Column(Text, nullable=False)
    interests = Column(Text, nullable=True)
    community = Column(Text, nullable=False)
    personal_info = Column(Text, nullable=True)
    city = Column(String(200), nullable=False)
    phone = Column(String(150), nullable=False)
    email = Column(String(200), nullable=False)
    telegram_name = Column(String(200), nullable=True)
    id_telegram = Column(BigInteger, unique=True, nullable=False)
    targets = Column(Text, nullable=False)
    location = Column(Integer, nullable=False)
    # TODO необходимо подумать, как наиболее правильно интегрировать данный параметр
    paid = Column(Boolean, default=True, nullable=False)


class MatchesResult(Base):
    __tablename__ = 'matches'
    id = Column(BigInteger, primary_key=True, nullable=False)
    matches = Column(Text, nullable=False)
    cursor = Column(BigInteger, nullable=False, default=0)


class DbClient:
    def __init__(self, connection: str):
        self.engine = create_engine(connection)
        self.Base = Base
        self.session = scoped_session(sessionmaker(bind=self.engine))

    def create_tables(self):
        self.Base.metadata.create_all(self.engine)

    def get_matching_list_user_id(self, user_id: int) -> List[Optional[int]]:
        try:
            result = self.session.query(MatchesResult).get(user_id)
            result = result.matches
            result = json.loads(result)
            return result
        except Exception as er:
            print(er)
        finally:
            self.session.close()

    def get_matching_user_id(self, user_id: int, cursor: int) -> int:
        try:
            result = self.session.query(MatchesResult).get(user_id)
            result = result.matches
            result = json.loads(result)
            result = result[cursor]
            return result
        except Exception as er:
            print(er)
        finally:
            self.session.close()

    def get_cursor(self, user_id: int) -> Optional[int]:
        try:
            result = self.session.query(MatchesResult).get(user_id)
            result = result.cursor
            return result
        except Exception as er:
            print(er)
        finally:
            self.session.close()

    def get_user(self, user_id: int):
        try:
            result = self.session.query(UserDb).filter(
                UserDb.id_telegram == user_id
            ).first()
            return result
        except Exception as er:
            print(er)
        finally:
            self.session.close()

    def _check_matches(self, user_id: int) -> bool:
        try:
            result = self.session.query(MatchesResult).filter(
                MatchesResult.id == user_id
            ).first()
            if result:
                return True
            else:
                return False
        except Exception as er:
            print(er)
        finally:
            self.session.close()

    def add_matches(self, matches: MatchesResult, user_id: int):
        try:
            if self._check_matches(user_id):
                self.session.query(MatchesResult).filter(
                    MatchesResult.id == user_id
                ).update({'matches': matches.matches})
                self.session.commit()
            else:
                self.session.add(matches)
                self.session.commit()
        except Exception as er:
            print(er)
        finally:
            self.session.close()

    def add_user(self, user: UserDb):
        try:
            self.session.add(user)
            self.session.commit()
        except Exception as er:
            print(er)
        finally:
            self.session.close()

    def update_field(self, table: Union[UserDb, MatchesResult], field: str, new_value: Any, user_id: int):
        try:
            self.session.query(table).filter(
                table.id_telegram == user_id
            ).update({field: new_value})
            self.session.commit()
        except Exception as er:
            print(er)
        finally:
            self.session.close()

    def get_community(self, table, user_id: int):
        try:
            result = self.session.query(table).filter(
                table.id_telegram == user_id
            ).first().community
            result = json.loads(result)
            return result
        except Exception as er:
            print(er)
        finally:
            self.session.close()

    def get_targets(self, table, user_id):
        try:
            result = self.session.query(table).filter(
                table.id_telegram == user_id
            ).first().targets
            result = json.loads(result)
            return result
        except Exception as er:
            print(er)
        finally:
            self.session.close()

    def get_location(self, table, user_id):
        try:
            result = self.session.query(table).filter(
                table.id_telegram == user_id
            ).first().location

            return LOCATIONS[result]
        except Exception as er:
            print(er)
        finally:
            self.session.close()

    def get_matching_users(self, table, location):
        try:
            location = int(location[-1])
            result = self.session.query(table).filter(
                table.location == location
            ).all()

            return result
        except Exception as er:
            print(er)
        finally:
            self.session.close()
