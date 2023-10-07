# Foodgram - сайт с рецептами

Foodgram - это сайт где вы можете смотреть и добавлять свои рецепты. Также вы можете подписываться на авторов и добавлять рецепты в корзину. После того, как корзина заполнена, вы можете скачать её. В скачанном файле у вас будут отображаться все ингредиенты, а также необходимое их количество.

Автор: Юрий Филатов
### Стек технологий
* Python 3.9
* Django 3.2
* DRF 3.12
* Docker
* Nginx
* PostgreSQL
* Github actions

### Как запустить проект:

### Как запустить проект локально:

Клонируйте репозиторий и перейдите в корневую папку проекта.

```
git@github.com:fyurikon/foodgram-project-react.git
```

```
cd foodgram-project-react
```

Установите docker на вашей операционно системе.

Создайте и заполните файл .env в корневой директории проекта:

```
SECRET_KEY=paste_your_django_secret_key_here
DEBUG=FALSE
ALLOWED_HOSTS=127.0.0.1 localhost yourdomain.com your_ip_server_address
POSTGRES_DB=foodgram
POSTGRES_USER=user
POSTGRES_PASSWORD=password
DB_NAME=foodgram
DB_HOST=db
DB_PORT=5432
```

Запустите все контейнеры из корневой папки проекта через docker compose

```
sudo docker compose up
```

После сборки, откройте ещё одно окно терминала, если вы запускали контейнеры не в фоновом режим, и выполните миграции:

```
sudo docker compose exec backend python manage.py migrate 
```
Создайте суперпользователя:

```
sudo docker compose exec backend python manage.py createsuperuser
```
Заполните базу ингредиентами:

```
sudo docker compose exec backend python manage.py import_csv data/ingredients.csv
```

Соберите и скопируйте статику django:

```
docker compose exec backend python manage.py collectstatic
```
```
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/ 
```
P.S. Обратите внимание, что проект запускается на порту 9000. Также обратите внимание, что образ nginx собирается из папки infra. Это сделано для того, чтобы картинки с рецептами отображались локально. В проекте, который деплоится через github actions образ собирается из папки nginx и конфиг там другой.


Теперь можно протестировать сайт: http://localhost:9000/

Также, для того, чтобы создать рецепт, вам потребуется добавить несколько тэгов через админку django.

### Особенности запуска проекта через github actions.
Скопируйте файл .env в корневую папку проекта на сервер. Проще всего это сделать, через копирование содержимого вашего .env файла.
В корневой папке выполняем следующее.
```
vi .env
ctrl+shift+v - вставляем содержимое нашего .env файла
:wq
```

Главной отличительной особенностью является то, что образ nginx собирается из другой папки, а именно ./nginx. Сделано это для корректного отображения картинок на вашем сайте.
Также, ОБЯЗАТЕЛЬНО, поправьте общий nginx на сервере, иначе картинки не заработают.
Если находитесь в папки проекта, которая находится в home/your-user, то путь будет следующим.
```
vi ../../etc/nginx/sites-available/default
```
В location должно остаться только "location /". Всё остальное убрать!!!
Пример:
![img.png](img.png)

После внесения изменений перезагрузите или перезапустите nginx.
```
sudo systemctl reload nginx
sudo systemctl restart nginx
```
Проверьте, что миграции выполнились успешно. Если нет запустите процесс ещё раз из корневой папки проекта на сервере.
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```
Если у вас, по каким то причинам, не появился файл ingredients.csv в папке data, то просто скопируйте содержимое csv файла со своего компьютера и создайте файл с этм содержимым.
Перейдите в папку data в контейнере backend и сделайте следующее.
```
cat > ingrediets.csv << EOF
ctrl+shift+v - то есть вставляем содержимое и нажимаем enter.
EOF
```
Теперь можно заполнить базу ингредиентами.
Из корневой папки проекта выполняем.
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_csv data/ingredients.csv
```

Сайт готов, можно пользоваться.