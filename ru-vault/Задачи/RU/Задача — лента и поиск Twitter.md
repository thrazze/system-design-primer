---
lang: ru
en: "[[Design the Twitter timeline and search]]"
tags: [sdp/задача, sdp/ru]
status: переведено
---

> 🇬🇧 Оригинал: [[Design the Twitter timeline and search]] · 🗺 [[00 Карта знаний]] · 📖 [[Глоссарий]]

# Задача — лента и поиск Twitter

*Примечание: этот документ ссылается напрямую на соответствующие разделы [тем системного дизайна](https://github.com/donnemartin/system-design-primer#index-of-system-design-topics), чтобы избежать дублирования. За общими тезисами, компромиссами и альтернативами обращайся к материалам по ссылкам.*

**Design the Facebook feed** и **Design Facebook search** — похожие по духу задачи.

## Шаг 1: Очертить сценарии использования и ограничения

> Собери требования и определи границы задачи.
> Задавай уточняющие вопросы про сценарии использования и ограничения.
> Обсуди допущения.

Без интервьюера, которому можно задать уточняющие вопросы, определим сценарии использования и ограничения сами.

### Сценарии использования

#### Ограничим задачу следующими сценариями

* **Пользователь** публикует твит
    * **Сервис** рассылает твиты подписчикам, отправляя push-уведомления и письма
* **Пользователь** просматривает свою ленту (user timeline — активность самого пользователя)
* **Пользователь** просматривает домашнюю ленту (home timeline — активность людей, на которых он подписан)
* **Пользователь** ищет по ключевым словам
* **Сервис** обладает высокой доступностью

#### Вне рамок задачи

* **Сервис** отправляет твиты в Twitter Firehose и другие потоки
* **Сервис** скрывает твиты в соответствии с настройками видимости пользователей
    * Скрывать @reply, если пользователь не подписан также на того, кому адресован ответ
    * Учитывать настройку «скрыть ретвиты»
* Аналитика

### Ограничения и допущения

#### Формулируем допущения

Общее

* Трафик распределён неравномерно
* Публикация твита должна быть быстрой
    * Fan-out твита по всем подписчикам должен быть быстрым — разве что у пользователя миллионы подписчиков
* 100 million active users
* 500 million tweets per day or 15 billion tweets per month
    * Each tweet averages a fanout of 10 deliveries
    * 5 billion total tweets delivered on fanout per day
    * 150 billion tweets delivered on fanout per month
* 250 billion read requests per month
* 10 billion searches per month

Лента

* Просмотр ленты должен быть быстрым
* У Twitter нагрузка сильнее смещена в сторону чтения, чем записи
    * Оптимизируем под быстрое чтение твитов
* Приём твитов — это нагрузка, смещённая в сторону записи

Поиск

* Поиск должен быть быстрым
* Поиск — это нагрузка, смещённая в сторону чтения

#### Прикидываем нагрузку

**Уточни у интервьюера, нужно ли делать расчёты на салфетке по нагрузке.**

* Размер одного твита:
    * `tweet_id` - 8 bytes
    * `user_id` - 32 bytes
    * `text` - 140 bytes
    * `media` - 10 KB average
    * Total: ~10 KB
* 150 TB of new tweet content per month
    * 10 KB per tweet * 500 million tweets per day * 30 days per month
    * 5.4 PB of new tweet content in 3 years
* 100 thousand read requests per second
    * 250 billion read requests per month * (400 requests per second / 1 billion requests per month)
* 6,000 tweets per second
    * 15 billion tweets per month * (400 requests per second / 1 billion requests per month)
* 60 thousand tweets delivered on fanout per second
    * 150 billion tweets delivered on fanout per month * (400 requests per second / 1 billion requests per month)
* 4,000 search requests per second
    * 10 billion searches per month * (400 requests per second / 1 billion requests per month)

Памятка по пересчёту:

* 2.5 million seconds per month
* 1 request per second = 2.5 million requests per month
* 40 requests per second = 100 million requests per month
* 400 requests per second = 1 billion requests per month

## Шаг 2: Разработать дизайн верхнего уровня

> Наметь дизайн верхнего уровня со всеми важными компонентами.

![Imgur](http://i.imgur.com/48tEA2j.png)

## Шаг 3: Спроектировать ключевые компоненты

> Углубись в детали каждого ключевого компонента.

### Сценарий: Пользователь публикует твит

Собственные твиты пользователя, из которых строится лента пользователя (user timeline — активность самого пользователя), можно хранить в [реляционной базе данных](https://github.com/donnemartin/system-design-primer#relational-database-management-system-rdbms). Стоит обсудить [сценарии использования и компромиссы выбора между SQL и NoSQL](https://github.com/donnemartin/system-design-primer#sql-or-nosql).

Доставка твитов и построение домашней ленты (home timeline — активность людей, на которых подписан пользователь) — задача сложнее. Fan-out твитов по всем подписчикам (60 thousand tweets delivered on fanout per second) перегрузит обычную [реляционную базу данных](https://github.com/donnemartin/system-design-primer#relational-database-management-system-rdbms). Скорее всего, здесь понадобится хранилище с быстрой записью — например, **NoSQL-база** или **кэш в памяти**. Последовательное чтение 1 МБ из памяти занимает около 250 микросекунд, тогда как чтение с SSD занимает в 4 раза дольше, а с диска — в 80 раз дольше.<sup><a href=https://github.com/donnemartin/system-design-primer#latency-numbers-every-programmer-should-know>1</a></sup>

Медиафайлы — фото или видео — можно хранить в **Object Store**.

* **Клиент** отправляет твит на **Web Server**, работающий как [обратный прокси](https://github.com/donnemartin/system-design-primer#reverse-proxy-web-server)
* **Web Server** пересылает запрос серверу **Write API**
* **Write API** сохраняет твит в ленте пользователя в **SQL-базе**
* **Write API** обращается к **Fan Out Service**, который делает следующее:
    * Запрашивает у **User Graph Service** подписчиков пользователя, хранящихся в **кэше в памяти**
    * Сохраняет твит в *домашней ленте подписчиков пользователя* в **кэше в памяти**
        * O(n) operation: 1,000 followers = 1,000 lookups and inserts
    * Сохраняет твит в **Search Index Service**, чтобы обеспечить быстрый поиск
    * Сохраняет медиа в **Object Store**
    * Использует **Notification Service**, чтобы разослать push-уведомления подписчикам:
        * Использует **очередь (Queue)** (не показана на схеме), чтобы асинхронно рассылать уведомления

**Уточни у интервьюера, сколько кода от тебя ожидают написать**.

Если наш **кэш в памяти** — это Redis, можно использовать нативный список Redis (Redis list) вот такой структуры:

```
           tweet n+2                   tweet n+1                   tweet n
| 8 bytes   8 bytes  1 byte | 8 bytes   8 bytes  1 byte | 8 bytes   8 bytes  1 byte |
| tweet_id  user_id  meta   | tweet_id  user_id  meta   | tweet_id  user_id  meta   |
```

Новый твит попадёт в **кэш в памяти**, откуда наполняется домашняя лента пользователя (активность людей, на которых он подписан).

Будем использовать публичный [**REST API**](https://github.com/donnemartin/system-design-primer#representational-state-transfer-rest):

```
$ curl -X POST --data '{ "user_id": "123", "auth_token": "ABC123", \
    "status": "hello world!", "media_ids": "ABC987" }' \
    https://twitter.com/api/v1/tweet
```

Ответ:

```
{
    "created_at": "Wed Sep 05 00:37:15 +0000 2012",
    "status": "hello world!",
    "tweet_id": "987",
    "user_id": "123",
    ...
}
```

Для внутренних коммуникаций можно использовать [удалённые вызовы процедур](https://github.com/donnemartin/system-design-primer#remote-procedure-call-rpc).

### Сценарий: Пользователь просматривает домашнюю ленту

* **Клиент** отправляет запрос домашней ленты на **Web Server**
* **Web Server** пересылает запрос серверу **Read API**
* **Read API** обращается к **Timeline Service**, который делает следующее:
    * Получает данные ленты, хранящиеся в **кэше в памяти** и содержащие tweet_id и user_id, — за O(1)
    * Запрашивает у **Tweet Info Service** через [multiget](http://redis.io/commands/mget) дополнительную информацию о tweet_id — за O(n)
    * Запрашивает у **User Info Service** через multiget дополнительную информацию о user_id — за O(n)

REST API:

```
$ curl https://twitter.com/api/v1/home_timeline?user_id=123
```

Ответ:

```
{
    "user_id": "456",
    "tweet_id": "123",
    "status": "foo"
},
{
    "user_id": "789",
    "tweet_id": "456",
    "status": "bar"
},
{
    "user_id": "789",
    "tweet_id": "579",
    "status": "baz"
},
```

### Сценарий: Пользователь просматривает свою ленту

* **Клиент** отправляет запрос ленты пользователя на **Web Server**
* **Web Server** пересылает запрос серверу **Read API**
* **Read API** получает ленту пользователя из **SQL-базы**

REST API будет похож на API домашней ленты, только все твиты будут принадлежать самому пользователю, а не людям, на которых он подписан.

### Сценарий: Пользователь ищет по ключевым словам

* **Клиент** отправляет поисковый запрос на **Web Server**
* **Web Server** пересылает запрос серверу **Search API**
* **Search API** обращается к **Search Service**, который делает следующее:
    * Разбирает/токенизирует входной запрос, определяя, что нужно искать
        * Убирает разметку
        * Разбивает текст на термины
        * Исправляет опечатки
        * Нормализует регистр
        * Преобразует запрос в булевы операции
    * Запрашивает результаты у **Search Cluster** (например, [Lucene](https://lucene.apache.org/)):
        * Делает [scatter-gather-запрос](https://github.com/donnemartin/system-design-primer#under-development) по каждому серверу кластера, чтобы определить, есть ли результаты по запросу
        * Объединяет, ранжирует, сортирует и возвращает результаты

REST API:

```
$ curl https://twitter.com/api/v1/search?query=hello+world
```

Ответ будет похож на ответ домашней ленты, но с твитами, соответствующими заданному запросу.

## Шаг 4: Масштабировать дизайн

> Определи узкие места и устрани их с учётом ограничений.

![Imgur](http://i.imgur.com/jrUBAF7.png)

**Важно: не переходи сразу от исходного дизайна к финальному!**

Проговори, что ты будешь: 1) **бенчмаркать/нагрузочно тестировать**, 2) **профилировать** узкие места, 3) устранять узкие места, оценивая альтернативы и компромиссы, и 4) повторять цикл. Смотри [[Задача — масштабирование до миллионов пользователей на AWS|Design a system that scales to millions of users on AWS]] как пример итеративного масштабирования исходного дизайна.

Важно обсудить, какие узкие места могут возникнуть в исходном дизайне и как их устранить. Например, какие проблемы решает добавление **балансировщика нагрузки** с несколькими **веб-серверами**? **CDN**? **Master-Slave-репликами**? Какие есть альтернативы и **компромиссы** для каждого из этих решений?

Добавим несколько компонентов, чтобы завершить дизайн и решить проблемы масштабируемости. Внутренние балансировщики нагрузки на схеме не показаны — чтобы не загромождать её.

*Чтобы не повторять уже раскрытые темы*, обратись к следующим [темам системного дизайна](https://github.com/donnemartin/system-design-primer#index-of-system-design-topics) за основными тезисами, компромиссами и альтернативами:

* [[Система доменных имён (DNS)|DNS]]
* [[Сеть доставки контента (CDN)|CDN]]
* [[Балансировщик нагрузки|Load balancer]]
* [Горизонтальное масштабирование](https://github.com/donnemartin/system-design-primer#horizontal-scaling)
* [[Обратный прокси|Web server (reverse proxy)]]
* [[Уровень приложений|API server (application layer)]]
* [[Кэш|Cache]]
* [[Реляционные БД (RDBMS)|Relational database management system (RDBMS)]]
* [переключение при отказе write-мастера в SQL, master-slave (SQL write master-slave failover)](https://github.com/donnemartin/system-design-primer#fail-over)
* [Репликация master-slave](https://github.com/donnemartin/system-design-primer#master-slave-replication)
* [[Шаблоны согласованности|Consistency patterns]]
* [[Шаблоны доступности|Availability patterns]]

**Fanout Service** — потенциальное узкое место. У пользователей Twitter с миллионами подписчиков прохождение твита через fan-out может занять несколько минут. Это может привести к состояниям гонки (race conditions) с @reply на твит, что можно смягчить, переупорядочивая твиты уже во время выдачи (serve time).

Можно также вообще не делать fan-out для твитов пользователей с большим числом подписчиков. Вместо этого твиты таких пользователей можно находить поиском, объединять результаты поиска с результатами домашней ленты пользователя, а затем переупорядочивать твиты во время выдачи.

Дополнительные оптимизации:

* Хранить в **кэше в памяти** лишь несколько сотен твитов для каждой домашней ленты
* Хранить в **кэше в памяти** данные домашней ленты только для активных пользователей
    * Если пользователь не был активен последние 30 дней, ленту можно перестроить из **SQL-базы**
        * Запросить у **User Graph Service**, на кого подписан пользователь
        * Получить твиты из **SQL-базы** и добавить их в **кэш в памяти**
* Хранить в **Tweet Info Service** только твиты за последний месяц
* Хранить в **User Info Service** только активных пользователей
* **Search Cluster**, скорее всего, придётся держать твиты в памяти, чтобы сохранить низкую задержку

Также стоит решить проблему узкого места в **SQL-базе**.

Хотя **кэш в памяти** должен снизить нагрузку на базу, вряд ли одних только **SQL Read Replicas** хватит, чтобы справляться с промахами кэша. Скорее всего, потребуются дополнительные приёмы масштабирования SQL.

Большой объём записи перегрузит единственную схему **SQL Write Master-Slave**, что тоже говорит о необходимости дополнительных техник масштабирования.

* [Федерализация](https://github.com/donnemartin/system-design-primer#federation)
* [Шардирование](https://github.com/donnemartin/system-design-primer#sharding)
* [Денормализация](https://github.com/donnemartin/system-design-primer#denormalization)
* [Тюнинг SQL](https://github.com/donnemartin/system-design-primer#sql-tuning)

Стоит также подумать о переносе части данных в **NoSQL-базу**.

## Дополнительные темы для обсуждения

> Дополнительные темы для углубления, в зависимости от рамок задачи и оставшегося времени.

#### NoSQL

* [Хранилище «ключ-значение»](https://github.com/donnemartin/system-design-primer#key-value-store)
* [Документное хранилище](https://github.com/donnemartin/system-design-primer#document-store)
* [Колоночное хранилище](https://github.com/donnemartin/system-design-primer#wide-column-store)
* [Графовая база данных](https://github.com/donnemartin/system-design-primer#graph-database)
* [[SQL или NoSQL|SQL vs NoSQL]]

### Кэширование

* Где кэшировать
    * [Клиентское кэширование](https://github.com/donnemartin/system-design-primer#client-caching)
    * [Кэширование в CDN](https://github.com/donnemartin/system-design-primer#cdn-caching)
    * [Кэширование на веб-сервере](https://github.com/donnemartin/system-design-primer#web-server-caching)
    * [Кэширование в базе данных](https://github.com/donnemartin/system-design-primer#database-caching)
    * [Кэширование на уровне приложения](https://github.com/donnemartin/system-design-primer#application-caching)
* Что кэшировать
    * [Кэширование на уровне запроса к базе](https://github.com/donnemartin/system-design-primer#caching-at-the-database-query-level)
    * [Кэширование на уровне объекта](https://github.com/donnemartin/system-design-primer#caching-at-the-object-level)
* Когда обновлять кэш
    * [Cache-aside](https://github.com/donnemartin/system-design-primer#cache-aside)
    * [Write-through](https://github.com/donnemartin/system-design-primer#write-through)
    * [Write-behind (write-back)](https://github.com/donnemartin/system-design-primer#write-behind-write-back)
    * [Refresh-ahead](https://github.com/donnemartin/system-design-primer#refresh-ahead)

### Асинхронность и микросервисы

* [Очереди сообщений](https://github.com/donnemartin/system-design-primer#message-queues)
* [Очереди задач](https://github.com/donnemartin/system-design-primer#task-queues)
* [Обратное давление](https://github.com/donnemartin/system-design-primer#back-pressure)
* [Микросервисы](https://github.com/donnemartin/system-design-primer#microservices)

### Коммуникации

* Обсуди компромиссы:
    * Внешние коммуникации с клиентами — [HTTP API по REST](https://github.com/donnemartin/system-design-primer#representational-state-transfer-rest)
    * Внутренние коммуникации — [[RPC и REST|RPC]]
* [Обнаружение сервисов](https://github.com/donnemartin/system-design-primer#service-discovery)

### Безопасность

Смотри раздел [[Безопасность|про безопасность]].

### Цифры про задержку

Смотри [[Цифры, которые надо знать наизусть|Latency numbers every programmer should know]].

### Дальнейшие шаги

* Продолжай бенчмаркать и мониторить систему, чтобы устранять узкие места по мере появления
* Масштабирование — это итеративный процесс

---

## 🧠 Своими словами

> Заполняется после того, как решишь задачу соло за 45 минут. Пока пусто.

## ❓ Самопроверка

- [ ] Почему fan-out on write ломается для пользователей с миллионами подписчиков, и как fan-out on read (поиск + мердж на serve time) решает эту проблему для «горячих» аккаунтов?
- [ ] Нарисуй путь одного твита от POST-запроса клиента до появления в домашней ленте подписчика — через какие сервисы он проходит и что кладётся в кэш.
- [ ] Почему домашнюю ленту строят через денормализованный fan-out в кэш, а не через JOIN по SQL-базе на каждое чтение?
- [ ] Что произойдёт с системой, если Fan Out Service отстанет на несколько минут во время публикации твита знаменитостью, и как это связано с race condition на @reply?
- [ ] Какие данные можно безопасно выкинуть из Memory Cache (неактивные пользователи, старые твиты) и почему это не ломает продукт?
- [ ] Как ты объяснишь интервьюеру компромисс между fan-out on write и fan-out on read в терминах задержки записи vs задержки чтения?

## 🔗 Связано

[[Кэш]] · [[Асинхронность]] · [[Базы данных]] · [[NoSQL — типы хранилищ]] · [[Шаблоны согласованности]] · [[Расчёты на салфетке]]
