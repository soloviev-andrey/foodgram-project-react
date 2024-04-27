# Foodgram - платформа для гастрономических шедевров

[![CI](https://github.com/soloviev-andrey/foodgram-project-react/actions/workflows/main.yml/badge.svg)](https://github.com/soloviev-andrey/foodgram-project-react/actions/workflows/main.yml)

## Описание
Foodgram - это платформа, предназначенная для любителей готовить и наслаждаться вкусной едой. Здесь вы можете делиться своими кулинарными шедеврами с другими участниками или гостями форума.

## Особенности проекта
- Регистрация пользователей и возможность добавления рецептов.
- Возможность добавления рецептов в избранное и в список покупок.
- Поиск рецептов по различным критериям.
- Автоматическое формирование списка покупок на основе выбранных рецептов.
- Интерфейс администратора для управления контентом.

## Технологии
Проект был реализован с использованием следующих технологий:
- Django и Django REST framework для бэкенд-части.
- React.js для фронтенд-части.
- Docker для контейнеризации приложений.
- PostgreSQL для хранения данных.
- Nginx для балансировки и проксирования запросов.
- GitHub Actions для настройки непрерывной интеграции и доставки.

## Демонстрация работы
Вы можете ознакомиться с работой проекта, перейдя по ссылке: [https://foodandysololist.ddns.net/](https://foodandysololist.ddns.net/)

## Автор
Андрей Соловьев

## Запуск проекта
1. **Клонирование репозитория**: 
   - Сначала необходимо склонировать репозиторий с проектом на свой компьютер. Для этого используйте команду git clone git@github.com:soloviev-andrey/foodgram-project-react.git.
   - Перейдите в директорию проекта с помощью команды cd foodgram-project-react.

2. **Настройка переменных окружения**:
   - Создайте файл .env в корне проекта и добавьте необходимые переменные окружения. Примеры переменных можно найти в файле .env.example

3. **Запуск Docker Compose**:
   - Запустите Docker Compose в production режиме с помощью команды docker-compose -f docker-compose.production.yml up. Это запустит все необходимые контейнеры для работы проекта.

4. **Выполнение миграций и сборка статики**:
   - Выполните миграции для базы данных с помощью команды sudo docker-compose -f docker-compose.production.yml exec backend python manage.py migrate.
   - Соберите статику с помощью команды sudo docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic.
   - Скопируйте собранную статику в нужную директорию с помощью команды sudo docker-compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/.

5. **Создание суперпользователя**:
   - Создайте суперпользователя для доступа к админ-панели с помощью команды sudo docker-compose -f docker-compose.production.yml exec backend python manage.py createsuperuser.

6. **Проверка работоспособности**:
   - Откройте ваш браузер и перейдите по адресу http://localhost/. Теперь вы можете использовать функционал проекта Foodgram.


## Благодарности
Спасибо за интерес к проекту Foodgram! Если у вас есть вопросы или предложения, не стесняйтесь связаться со мной.