# Социальная сеть YaTube
-----
## Описание проекта

Проект был создан в рамках учебного курса Яндекс.Практикум.

Yatube представляет собой социальную сеть, в которой реализованы следующие операции:
* регистрация пользователей
* публикация постов с распределением по группам
* комментирование постов
* подписка/отписка на/от автора
-----
## Стек технологий

* Django 2.2
* Python 3.8
* Djangorestframework 3.12
-----
## Запуск проекта

1. Клонируйте репозитроий с проектом:

```git clone git@github.com:Alex9568rus/hw05_final.git```

2. Перейдите в созданную директорию, установите виртуальное окружение, активируйте его и установите необходимые зависимости:
* `cd api_final_yatube`
* `python3 -m venv venv`
* `source venv/bin/activate`
* `python3 -m pip install --upgrade pip`
* `pip install -r requirements.txt`

3. Выполните миграции:

- `cd yatube_api` 
- `python3 manage.py migrate`

4. запустите проект: 

`python3 manage.py runserver`

-----
