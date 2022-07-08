from bot import Bot


def connect_to_db(bot: Bot):
    try:
        bot.db_client.create_tables()
    except Exception as e:
        print(e)
