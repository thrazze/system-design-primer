---
lang: ru
en: "[[Design Amazon's sales ranking by category feature]]"
tags: [sdp/задача, sdp/ru]
status: переведено
---

> 🇬🇧 Оригинал: [[Design Amazon's sales ranking by category feature]] · 🗺 [[00 Карта знаний]] · 📖 [[Глоссарий]]

# Задача — ранжирование продаж Amazon

*Примечание: этот документ ссылается напрямую на соответствующие разделы [тем системного дизайна](https://github.com/donnemartin/system-design-primer#index-of-system-design-topics), чтобы избежать дублирования. За общими тезисами, компромиссами и альтернативами обращайтесь к материалам по ссылкам.*

## Шаг 1: Очертить сценарии использования и ограничения

> Собери требования и определи границы задачи.
> Задавай уточняющие вопросы про сценарии использования и ограничения.
> Обсуди допущения.

Без интервьюера, которому можно задать уточняющие вопросы, определим сценарии использования и ограничения сами.

### Сценарии использования

#### Ограничим задачу следующим сценарием

* **Сервис** считает самые популярные товары по категориям за прошедшую неделю
* **Пользователь** просматривает самые популярные товары по категориям за прошедшую неделю
* **Сервис** обладает высокой доступностью

#### Вне рамок задачи

* Общая площадка электронной коммерции
    * Проектируем компоненты только для расчёта ранга продаж

### Ограничения и допущения

#### Формулируем допущения

* Трафик распределён неравномерно
* Товар может относиться сразу к нескольким категориям
* Товар не может сменить категорию
* Подкатегорий нет, то есть вида `foo/bar/baz`
* Результаты нужно обновлять ежечасно
    * Более популярные товары, возможно, придётся обновлять чаще
* 10 миллионов товаров
* 1000 категорий
* 1 миллиард транзакций в месяц
* 100 миллиардов запросов на чтение в месяц
* соотношение чтения к записи 100:1

#### Считаем нагрузку

**Уточни у интервьюера, нужно ли делать расчёты на салфетке по нагрузке.**

* Размер одной транзакции:
    * `created_at` — 5 байт
    * `product_id` — 8 байт
    * `category_id` — 4 байта
    * `seller_id` — 8 байт
    * `buyer_id` — 8 байт
    * `quantity` — 4 байта
    * `total_price` — 5 байт
    * Итого: ~40 байт
* 40 GB нового контента транзакций в месяц
    * 40 bytes per transaction * 1 billion transactions per month
    * 1.44 TB нового контента транзакций за 3 года
    * Предполагаем, что большинство записей — новые транзакции, а не обновления существующих
* 400 транзакций в секунду в среднем
* 40 000 запросов на чтение в секунду в среднем

Памятка по пересчёту:

* 2.5 million seconds per month
* 1 request per second = 2.5 million requests per month
* 40 requests per second = 100 million requests per month
* 400 requests per second = 1 billion requests per month

## Шаг 2: Разработать дизайн верхнего уровня

> Наметь дизайн верхнего уровня со всеми важными компонентами.

![Imgur](http://i.imgur.com/vwMa1Qu.png)

## Шаг 3: Спроектировать ключевые компоненты

> Углубись в детали каждого ключевого компонента.

### Сценарий: Сервис считает самые популярные товары по категориям за прошлую неделю

Сырые лог-файлы сервера **Sales API** можно хранить в управляемом **Object Store**, например Amazon S3, — так не придётся администрировать собственную распределённую файловую систему.

**Уточни у интервьюера, сколько кода от тебя ожидают написать**.

Предположим, что лог-запись выглядит так, поля разделены табуляцией:

```
timestamp   product_id  category_id    qty     total_price   seller_id    buyer_id
t1          product1    category1      2       20.00         1            1
t2          product1    category2      2       20.00         2            2
t2          product1    category2      1       10.00         2            3
t3          product2    category1      3        7.00         3            4
t4          product3    category2      7        2.00         4            5
t5          product4    category1      1        5.00         5            6
...
```

**Sales Rank Service** может использовать **MapReduce**: на вход берутся лог-файлы сервера **Sales API**, а результат записывается в агрегирующую таблицу `sales_rank` в **SQL Database**. Стоит обсудить [сценарии использования и компромиссы выбора между SQL и NoSQL](https://github.com/donnemartin/system-design-primer#sql-or-nosql).

Используем многоэтапный **MapReduce**:

* **Шаг 1** — преобразуем данные в `(category, product_id), sum(quantity)`
* **Шаг 2** — выполняем распределённую сортировку

```python
class SalesRanker(MRJob):

    def within_past_week(self, timestamp):
        """Return True if timestamp is within past week, False otherwise."""
        ...

    def mapper(self, _ line):
        """Parse each log line, extract and transform relevant lines.

        Emit key value pairs of the form:

        (category1, product1), 2
        (category2, product1), 2
        (category2, product1), 1
        (category1, product2), 3
        (category2, product3), 7
        (category1, product4), 1
        """
        timestamp, product_id, category_id, quantity, total_price, seller_id, \
            buyer_id = line.split('\t')
        if self.within_past_week(timestamp):
            yield (category_id, product_id), quantity

    def reducer(self, key, value):
        """Sum values for each key.

        (category1, product1), 2
        (category2, product1), 3
        (category1, product2), 3
        (category2, product3), 7
        (category1, product4), 1
        """
        yield key, sum(values)

    def mapper_sort(self, key, value):
        """Construct key to ensure proper sorting.

        Transform key and value to the form:

        (category1, 2), product1
        (category2, 3), product1
        (category1, 3), product2
        (category2, 7), product3
        (category1, 1), product4

        The shuffle/sort step of MapReduce will then do a
        distributed sort on the keys, resulting in:

        (category1, 1), product4
        (category1, 2), product1
        (category1, 3), product2
        (category2, 3), product1
        (category2, 7), product3
        """
        category_id, product_id = key
        quantity = value
        yield (category_id, quantity), product_id

    def reducer_identity(self, key, value):
        yield key, value

    def steps(self):
        """Run the map and reduce steps."""
        return [
            self.mr(mapper=self.mapper,
                    reducer=self.reducer),
            self.mr(mapper=self.mapper_sort,
                    reducer=self.reducer_identity),
        ]
```

В результате получится следующий отсортированный список, который можно вставить в таблицу `sales_rank`:

```
(category1, 1), product4
(category1, 2), product1
(category1, 3), product2
(category2, 3), product1
(category2, 7), product3
```

Таблица `sales_rank` может иметь такую структуру:

```
id int NOT NULL AUTO_INCREMENT
category_id int NOT NULL
total_sold int NOT NULL
product_id int NOT NULL
PRIMARY KEY(id)
FOREIGN KEY(category_id) REFERENCES Categories(id)
FOREIGN KEY(product_id) REFERENCES Products(id)
```

Создадим [индекс](https://github.com/donnemartin/system-design-primer#use-good-indices) по полям `id`, `category_id` и `product_id`, чтобы ускорить поиск (логарифмическое время вместо сканирования всей таблицы) и удержать данные в памяти. Последовательное чтение 1 МБ из памяти занимает около 250 микросекунд, тогда как чтение с SSD занимает в 4 раза дольше, а с диска — в 80 раз дольше.<sup><a href=https://github.com/donnemartin/system-design-primer#latency-numbers-every-programmer-should-know>1</a></sup>

### Сценарий: Пользователь просматривает самые популярные товары по категориям за прошлую неделю

* **Клиент** отправляет запрос на **Web Server**, работающий как [обратный прокси](https://github.com/donnemartin/system-design-primer#reverse-proxy-web-server)
* **Web Server** пересылает запрос серверу **Read API**
* Сервер **Read API** читает из таблицы `sales_rank` в **SQL Database**

Будем использовать публичный [**REST API**](https://github.com/donnemartin/system-design-primer#representational-state-transfer-rest):

```
$ curl https://amazon.com/api/v1/popular?category_id=1234
```

Ответ:

```
{
    "id": "100",
    "category_id": "1234",
    "total_sold": "100000",
    "product_id": "50",
},
{
    "id": "53",
    "category_id": "1234",
    "total_sold": "90000",
    "product_id": "200",
},
{
    "id": "75",
    "category_id": "1234",
    "total_sold": "80000",
    "product_id": "3",
},
```

Для внутренних коммуникаций можно использовать [удалённый вызов процедур](https://github.com/donnemartin/system-design-primer#remote-procedure-call-rpc).

## Шаг 4: Масштабировать дизайн

> Определи узкие места и устрани их с учётом ограничений.

![Imgur](http://i.imgur.com/MzExP06.png)

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
* [Переключение при отказе для SQL write master-slave](https://github.com/donnemartin/system-design-primer#fail-over)
* [Master-slave-репликация](https://github.com/donnemartin/system-design-primer#master-slave-replication)
* [[Шаблоны согласованности|Consistency patterns]]
* [[Шаблоны доступности|Availability patterns]]

**Analytics Database** может строиться на решении для хранилищ данных вроде Amazon Redshift или Google BigQuery.

Возможно, в базе имеет смысл хранить данные только за ограниченный период, а остальное держать в хранилище данных или в **Object Store**. **Object Store**, например Amazon S3, спокойно справится с ограничением в 40 GB нового контента в месяц.

Чтобы справиться с 40 000 запросами на чтение в секунду *в среднем* (на пиках больше), трафик к популярному контенту (и его рангу продаж) должен обрабатывать **Memory Cache**, а не база напрямую. **Memory Cache** также помогает сглаживать неравномерно распределённый трафик и его всплески. При таком объёме чтений **SQL Read Replicas** могут не справиться с промахами кэша — вероятно, потребуются дополнительные паттерны масштабирования SQL.

400 записей в секунду *в среднем* (на пиках больше) могут оказаться непосильными для одного **SQL Write Master-Slave** — это тоже говорит о необходимости дополнительных техник масштабирования.

Паттерны масштабирования SQL:

* [Федерализация](https://github.com/donnemartin/system-design-primer#federation)
* [Шардирование](https://github.com/donnemartin/system-design-primer#sharding)
* [Денормализация](https://github.com/donnemartin/system-design-primer#denormalization)
* [Тюнинг SQL](https://github.com/donnemartin/system-design-primer#sql-tuning)

Также стоит рассмотреть перенос части данных в **NoSQL Database**.

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

- [ ] Почему здесь MapReduce делает два прохода (map/reduce, затем mapper_sort/reducer_identity), а не один — что даёт распределённая сортировка на втором этапе?
- [ ] Почему ранг продаж считается батчем раз в час, а не обновляется в реальном времени при каждой транзакции? Что изменится, если интервьюер попросит near-real-time обновление?
- [ ] Зачем хранить сырые логи Sales API в Object Store (S3), а не писать транзакции сразу в SQL Database?
- [ ] Как распределить Memory Cache между 1000 категориями с неравномерным трафиком — где здесь риск горячего шарда?
- [ ] Какие есть варианты, если один SQL Write Master-Slave не тянет 400 записей в секунду на пиках — federation по category_id или шардирование? В чём разница?
- [ ] Почему для этой задачи не подходит простой counter-подход (`UPDATE ... SET total_sold = total_sold + qty`) вместо batch MapReduce?

## 🔗 Связано

[[Базы данных]] · [[SQL или NoSQL]] · [[Кэш]] · [[Асинхронность]] · [[Расчёты на салфетке]] · [[Каркас ответа на собеседовании]]
