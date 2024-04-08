# Дипломный проект - foodgram
[![CI](https://github.com/soloviev-andrey/foodgram-project-react/actions/workflows/main.yml/badge.svg)](https://github.com/soloviev-andrey/foodgram-project-react/actions/workflows/main.yml)


## Описание
Foodgram - это вдохновляющая платформа для любителей как приготовить, так и вкусно покушать. Вы можете делится своими гастрономическими шедеврами с другими участниками или гостями форума.


## Что было сделано?
В рамках этого проекта было выполнено следующее:
- Разработана веб-платформа foodgram.
- Создан Docker-контейнер для бэкенд-части проекта foodgram.
- Настроен Nginx-сервер для проксирования запросов к разным частям проекта.
- Разработан Docker-контейнер для фронтенд-части.
- Произведена интеграция с базой данных PostgreSQL.
- Развернут проект на сервере.


## Использованные технологии
Проект был реализован с использованием следующих технологий:
- Django и Django REST framework для бэкенд-части
- React.js для фронтенд-части 
- Docker для контейнеризации приложений.
- PostgreSQL для хранения данных.
- Nginx для обеспечения балансировки и проксирования запросов.
- GitHub Actions для настройки непрерывной интеграции и доставки.

## Проверка работоспособности
Вы можете проверить работу проекта, перейдя по следующей ссылке:
- [https://foodgramsolovev.zapto.org/](https://foodgramsolovev.zapto.org/)

## Автор
Андрей Соловьев

## Как запустить проект:
1. Клонировать репозиторий и перейти в него в командной строке:
```bash
git clone git@github.com:soloviev-andrey/foodgram-project-react.git
cd foodgram-project-react
```
2. Создать файл .env для хранения ключей:
```bash
SECRET_KEY='указать секретный ключ'
ALLOWED_HOSTS='указать имя или IP хоста'
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_NAME=foodgram
DB_HOST=db
DB_PORT=5432
DEBUG=False
```
3. Запустить docker-compose.production:
```bash
docker compose \-f docker\-compose\.production\.yml up
```
4. Выполнить миграции, сбор статики:
```bash
docker compose \-f docker\-compose\.production\.yml exec backend python manage\.py migrate
docker compose \-f docker\-compose\.production\.yml exec backend python manage\.py collectstatic
docker compose \-f docker\-compose\.production\.yml exec backend cp \-r /app/collected\_static/\. /static/static/
```
5. Создать суперпользователя, ввести почту, логин, пароль:
```bash
docker compose \-f docker\-compose\.production\.yml exec backend python manage\.py createsuperuser
```