from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import AppMaker, Base, FavApps, User

engine = create_engine('sqlite:///appmakerinfowithusers.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
        picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')  # noqa
session.add(User1)
session.commit()


# Info for Tres_Zap
appmaker1 = AppMaker(user_id=1, name="Tres_Zap")

session.add(appmaker1)
session.commit()

favApps1 = FavApps(user_id=1, name="prigmand0", description="Suspendisse ornare consequat lectus.",  # noqa
                     price="$2.99", catch_phrase="Configurable bandwidth-monitored groupware",  # noqa
                     appmaker=appmaker1, user=User1)

session.add(favApps1)
session.commit()

favApps2 = FavApps(user_id=1, name="mmonkley1", description="Curabitur convallis.",  # noqa
                     price="$2.99", catch_phrase="Profit-focused 5th generation standardization",   # noqa
                     appmaker=appmaker1, user=User1)

session.add(favApps2)
session.commit()

# Info for Subin
appmaker2 = AppMaker(user_id=1, name="Subin", user=User1)

session.add(appmaker1)
session.commit()

favApps1 = FavApps(user_id=1, name="nrolland2", description="Suspendisse ornare consequat lectus.",  # noqa
                     price="$2.99", catch_phrase="Configurable bandwidth-monitored groupware",  # noqa
                     appmaker=appmaker2, user=User1)

session.add(favApps1)
session.commit()

favApps2 = FavApps(user_id=1, name="mmonkley1", description="Integer a nibh. In quis justo.",  # noqa
                     price="$2.99", catch_phrase="Distributed solution-oriented methodology",   # noqa
                     appmaker=appmaker2, user=User1)

session.add(favApps2)
session.commit()


# Info for Bamity
appmaker3 = AppMaker(user_id=1, name="Bamity", user=User1)

session.add(appmaker3)
session.commit()


favApps1 = FavApps(user_id=1, name="moseland3", description="Integer ac leo. Pellentesque ultrices mattis odio.",  # noqa
                     price="$2.99", catch_phrase="Enhanced client-driven focus group.",  # noqa
                     appmaker=appmaker3, user=User1)

session.add(favApps1)
session.commit()

favApps2 = FavApps(user_id=1, name="sduley4", description="Donec diam neque, vestibulum eget.",  # noqa
                     price="$2.99", catch_phrase="Object-based 4th generation artificial intelligence.",  # noqa
                     appmaker=appmaker3, user=User1)

session.add(favApps2)
session.commit()


# Info for Gembucket
appmaker4 = AppMaker(user_id=1, name="Gembucket", user=User1)

session.add(appmaker4)
session.commit()


favapps1 = FavApps(user_id=1, name="jtaylorsont", description="Proin risus. Praesent lectus.",  # noqa
                     price="$2.99", catch_phrase="Configurable bandwidth-monitored groupware",  # noqa
                     appmaker=appmaker4, user=User1)

session.add(favApps1)
session.commit()

favapps2 = FavApps(user_id=1, name="mmonkley1", description="Curabitur convallis.",  # noqa
                     price="$2.99", catch_phrase="Realigned multimedia array",  # noqa
                     appmaker=appmaker4, user=User1)

session.add(favApps2)
session.commit()

# Info for Job
appmaker5 = AppMaker(user_id=1, name="Job", user=User1)

session.add(appmaker5)
session.commit()


favapps1 = FavApps(user_id=1, name="mnangleq", description="Suspendisse ornare consequat lectus.",   # noqa
                     price="$2.99", catch_phrase="Extended context-sensitive software",  # noqa
                     appmaker=appmaker5, user=User1)

session.add(favApps1)
session.commit()

favapps2 = FavApps(user_id=1, name="bbutland11", description="hasellus sit amet erat.",  # noqa
                     price="$2.99", catch_phrase="Synergistic interactive core",  # noqa
                     appmaker=appmaker5, user=User1)

session.add(favApps2)
session.commit()


print "added FavApps info!"

