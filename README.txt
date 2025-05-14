
# Telegram-Бот для жалоб в ФАС

Этот контейнер запускает Telegram-бота, предназначенного для генерации и отправки жалоб в УФАС по фактам спам-звонков и СМС.

## Содержимое

- `spam_complaint_bot.py` — основной код бота
- `pdf_utils.py` — генерация PDF жалобы
- `mailto_link.py` — генерация mailto-ссылки
- `requirements.txt` — зависимости

## Как собрать и запустить

1. Создайте файл `.env` или задайте переменную окружения:

```bash
export BOT_TOKEN=your_token_here
```

2. Соберите образ:

```bash
docker build -t spam-fas-bot .
```

3. Запустите контейнер:

```bash
docker run -d --name fasbot -e BOT_TOKEN=$BOT_TOKEN spam-fas-bot
```

## Примечания

- Контейнер не сохраняет историю между перезапусками. Для сохранения истории смонтируйте volume:

```bash
docker run -d --name fasbot -v $(pwd)/data:/app/data -e BOT_TOKEN=$BOT_TOKEN spam-fas-bot
```

- По умолчанию база `complaints.db` хранится в `/app`.

