---
lang: ru
en: "[[Design Pastebin.com]]"
tags: [sdp/задача, sdp/ru]
status: переведено
---

> 🇬🇧 Оригинал: [[Design Pastebin.com]] · 🗺 [[00 Карта знаний]] · 📖 [[Глоссарий]]

# Задача — Pastebin и bit.ly

*Примечание: этот документ ссылается напрямую на соответствующие разделы [обзора тем system design](https://github.com/donnemartin/system-design-primer#index-of-system-design-topics), чтобы не дублировать материал. За общими тезисами, компромиссами и альтернативами обращайся по этим ссылкам.*

**Дизайн Bit.ly** — похожая задача, с той разницей, что Pastebin нужно хранить содержимое пасты, а не оригинальный (несокращённый) url.

## Шаг 1: Наметить сценарии использования и ограничения

> Собери требования и очерти границы задачи.
> Задавай вопросы, чтобы прояснить сценарии использования и ограничения.
> Обсуди допущения.

Раз интервьюера, которому можно задать уточняющие вопросы, нет, определим сценарии использования и ограничения самостоятельно.

### Сценарии использования

#### Ограничим задачу следующими сценариями использования

* **Пользователь** вводит блок текста и получает случайно сгенерированную ссылку
    * Срок действия
        * По умолчанию не истекает
        * Можно опционально задать срок действия по времени
* **Пользователь** вводит url пасты и просматривает её содержимое
* **Пользователь** анонимен
* **Сервис** собирает аналитику по страницам
    * Статистика посещений по месяцам
* **Сервис** удаляет пасты с истёкшим сроком действия
* **Сервис** обладает высокой доступностью

#### Вне рамок задачи

* **Пользователь** регистрирует аккаунт
    * **Пользователь** подтверждает email
* **Пользователь** входит в зарегистрированный аккаунт
    * **Пользователь** редактирует документ
* **Пользователь** может задавать видимость
* **Пользователь** может задавать собственную короткую ссылку

### Ограничения и допущения

#### Сформулируем допущения

* Трафик распределён неравномерно
* Переход по короткой ссылке должен быть быстрым
* Пасты содержат только текст
* Аналитика просмотров страниц не обязана быть в реальном времени
* 10 million users
* 10 million paste writes per month
* 100 million paste reads per month
* 10:1 read to write ratio

#### Прикинем нагрузку

**Уточни у интервьюера, нужно ли прогонять расчёты на салфетке (back-of-the-envelope) по нагрузке.**

* Размер одной пасты
    * 1 KB content per paste
    * `shortlink` - 7 bytes
    * `expiration_length_in_minutes` - 4 bytes
    * `created_at` - 5 bytes
    * `paste_path` - 255 bytes
    * total = ~1.27 KB
* 12.7 GB of new paste content per month
    * 1.27 KB per paste * 10 million pastes per month
    * ~450 GB of new paste content in 3 years
    * 360 million shortlinks in 3 years
    * Предполагаем, что это в основном новые пасты, а не обновления уже существующих
* 4 paste writes per second on average
* 40 read requests per second on average

Памятка для перевода единиц:

* 2.5 million seconds per month
* 1 request per second = 2.5 million requests per month
* 40 requests per second = 100 million requests per month
* 400 requests per second = 1 billion requests per month

## Шаг 2: Разработать high-level дизайн

> Наметь high-level дизайн со всеми ключевыми компонентами.

![Imgur](http://i.imgur.com/BKsBnmG.png)

## Шаг 3: Спроектировать ключевые компоненты

> Разберись в деталях с каждым ключевым компонентом.

### Сценарий: пользователь вводит блок текста и получает случайно сгенерированную ссылку

Можно использовать [реляционную базу данных](https://github.com/donnemartin/system-design-primer#relational-database-management-system-rdbms) как большую хеш-таблицу, сопоставляющую сгенерированный url с файловым сервером и путём, где лежит файл пасты.

Вместо того чтобы держать собственный файловый сервер, можно использовать управляемое **объектное хранилище (Object Store)**, например Amazon S3, или [документное NoSQL-хранилище](https://github.com/donnemartin/system-design-primer#document-store).

В качестве альтернативы реляционной базе в роли большой хеш-таблицы можно взять [NoSQL-хранилище «ключ-значение»](https://github.com/donnemartin/system-design-primer#key-value-store). Стоит обсудить [компромиссы выбора между SQL и NoSQL](https://github.com/donnemartin/system-design-primer#sql-or-nosql). Дальше рассматриваем вариант с реляционной базой.

* **Клиент** отправляет запрос на создание пасты **веб-серверу**, работающему как [обратный прокси](https://github.com/donnemartin/system-design-primer#reverse-proxy-web-server)
* **Веб-сервер** передаёт запрос серверу **Write API**
* Сервер **Write API** делает следующее:
    * Генерирует уникальный url
        * Проверяет уникальность url, ища дубликат в **SQL-базе**
        * Если url не уникален, генерирует другой
        * Если бы поддерживался пользовательский url, можно было бы использовать введённый пользователем вариант (тоже с проверкой на дубликат)
    * Сохраняет запись в таблицу `pastes` **SQL-базы**
    * Сохраняет данные пасты в **объектное хранилище**
    * Возвращает url

**Уточни у интервьюера, сколько кода от тебя ожидают**.

Таблица `pastes` может иметь такую структуру:

```
shortlink char(7) NOT NULL
expiration_length_in_minutes int NOT NULL
created_at datetime NOT NULL
paste_path varchar(255) NOT NULL
PRIMARY KEY(shortlink)
```

Если сделать первичным ключом столбец `shortlink`, на нём появится [индекс](https://github.com/donnemartin/system-design-primer#use-good-indices), который база использует для обеспечения уникальности. Добавим ещё один индекс по `created_at`, чтобы ускорить поиск (логарифмическое время вместо сканирования всей таблицы) и удерживать эти данные в памяти. Последовательное чтение 1 MB из памяти занимает около 250 микросекунд, тогда как с SSD — в 4 раза дольше, а с диска — в 80 раз дольше.<sup><a href=https://github.com/donnemartin/system-design-primer#latency-numbers-every-programmer-should-know>1</a></sup>

Чтобы сгенерировать уникальный url, можно:

* Взять [**MD5**](https://en.wikipedia.org/wiki/MD5)-хеш от ip_address пользователя + timestamp
    * MD5 — широко используемая хеш-функция, дающая 128-битное хеш-значение
    * MD5 равномерно распределён
    * Как вариант, можно взять MD5-хеш от случайно сгенерированных данных
* Закодировать MD5-хеш в [**Base 62**](https://www.kerstner.at/2012/07/shortening-strings-using-base-62-encoding/)
    * Base 62 кодирует в алфавит `[a-zA-Z0-9]`, что хорошо подходит для url и избавляет от необходимости экранировать спецсимволы
    * У исходных данных лишь один результат хеширования, а Base 62 детерминирован (без элемента случайности)
    * Base 64 — другая популярная кодировка, но она проблематична для url из-за дополнительных символов `+` и `/`
    * Следующий [псевдокод Base 62](http://stackoverflow.com/questions/742013/how-to-code-a-url-shortener) выполняется за O(k), где k — число цифр = 7:

```python
def base_encode(num, base=62):
    digits = []
    while num > 0
      remainder = modulo(num, base)
      digits.push(remainder)
      num = divide(num, base)
    digits = digits.reverse
```

* Взять первые 7 символов результата — это даёт 62^7 возможных значений, чего должно с запасом хватить под наше ограничение в 360 миллионов коротких ссылок за 3 года:

```python
url = base_encode(md5(ip_address+timestamp))[:URL_LENGTH]
```

Для внешнего взаимодействия используем публичный [**REST API**](https://github.com/donnemartin/system-design-primer#representational-state-transfer-rest):

```
$ curl -X POST --data '{ "expiration_length_in_minutes": "60", \
    "paste_contents": "Hello World!" }' https://pastebin.com/api/v1/paste
```

Ответ:

```
{
    "shortlink": "foobar"
}
```

Для внутренних коммуникаций можно использовать [Remote Procedure Calls](https://github.com/donnemartin/system-design-primer#remote-procedure-call-rpc).

### Сценарий: пользователь вводит url пасты и просматривает её содержимое

* **Клиент** отправляет **веб-серверу** запрос на получение пасты
* **Веб-сервер** передаёт запрос серверу **Read API**
* Сервер **Read API** делает следующее:
    * Проверяет наличие сгенерированного url в **SQL-базе**
        * Если url найден, забирает содержимое пасты из **объектного хранилища**
        * Иначе возвращает пользователю сообщение об ошибке

REST API:

```
$ curl https://pastebin.com/api/v1/paste?shortlink=foobar
```

Ответ:

```
{
    "paste_contents": "Hello World"
    "created_at": "YYYY-MM-DD HH:MM:SS"
    "expiration_length_in_minutes": "60"
}
```

### Сценарий: сервис собирает аналитику по страницам

Поскольку аналитика в реальном времени не требуется, можно просто прогнать логи **веб-сервера** через **MapReduce** и получить счётчики обращений.

**Уточни у интервьюера, сколько кода от тебя ожидают**.

```python
class HitCounts(MRJob):

    def extract_url(self, line):
        """Extract the generated url from the log line."""
        ...

    def extract_year_month(self, line):
        """Return the year and month portions of the timestamp."""
        ...

    def mapper(self, _, line):
        """Parse each log line, extract and transform relevant lines.

        Emit key value pairs of the form:

        (2016-01, url0), 1
        (2016-01, url0), 1
        (2016-01, url1), 1
        """
        url = self.extract_url(line)
        period = self.extract_year_month(line)
        yield (period, url), 1

    def reducer(self, key, values):
        """Sum values for each key.

        (2016-01, url0), 2
        (2016-01, url1), 1
        """
        yield key, sum(values)
```

### Сценарий: сервис удаляет пасты с истёкшим сроком действия

Чтобы удалять пасты с истёкшим сроком действия, можно просто сканировать **SQL-базу** на предмет записей, у которых временная метка истечения раньше текущего момента. Все такие записи затем удаляются из таблицы (либо помечаются как истёкшие).

## Шаг 4: Масштабировать дизайн

> Найди узкие места с учётом ограничений и устрани их.

![Imgur](http://i.imgur.com/4edXG0T.png)

**Важно: не перескакивай сразу от исходного дизайна к финальному!**

Проговори, что будешь действовать итеративно: 1) **бенчмарк / нагрузочное тестирование**, 2) **профилирование** узких мест, 3) устранение узких мест с оценкой альтернатив и компромиссов, и 4) повтор цикла. Пример такого итеративного масштабирования исходного дизайна смотри в разборе [[Задача — масштабирование до миллионов пользователей на AWS|«Масштабирование до миллионов пользователей на AWS»]].

Важно обсудить, какие узкие места могут возникнуть в исходном дизайне и как их устранять. Например: какие проблемы решает добавление **балансировщика нагрузки** с несколькими **веб-серверами**? **CDN**? **master-slave-реплики**? Какие есть альтернативы и **компромиссы** для каждого решения?

Добавим несколько компонентов, чтобы завершить дизайн и закрыть вопросы масштабируемости. Внутренние балансировщики нагрузки на схеме не показаны — чтобы не перегружать её.

*Чтобы не повторяться*, за основными тезисами, компромиссами и альтернативами обращайся к следующим [темам system design](https://github.com/donnemartin/system-design-primer#index-of-system-design-topics):

* [DNS](https://github.com/donnemartin/system-design-primer#domain-name-system)
* [CDN](https://github.com/donnemartin/system-design-primer#content-delivery-network)
* [Балансировщик нагрузки](https://github.com/donnemartin/system-design-primer#load-balancer)
* [Горизонтальное масштабирование](https://github.com/donnemartin/system-design-primer#horizontal-scaling)
* [Веб-сервер (обратный прокси)](https://github.com/donnemartin/system-design-primer#reverse-proxy-web-server)
* [API-сервер (уровень приложения)](https://github.com/donnemartin/system-design-primer#application-layer)
* [Кэш](https://github.com/donnemartin/system-design-primer#cache)
* [Реляционная СУБД (RDBMS)](https://github.com/donnemartin/system-design-primer#relational-database-management-system-rdbms)
* [Переключение при отказе (failover) SQL write master-slave](https://github.com/donnemartin/system-design-primer#fail-over)
* [Master-slave-репликация](https://github.com/donnemartin/system-design-primer#master-slave-replication)
* [Шаблоны согласованности](https://github.com/donnemartin/system-design-primer#consistency-patterns)
* [Шаблоны доступности](https://github.com/donnemartin/system-design-primer#availability-patterns)

**База для аналитики (Analytics Database)** может использовать решение для хранилищ данных вроде Amazon Redshift или Google BigQuery.

**Объектное хранилище**, например Amazon S3, спокойно справится с ограничением в 12.7 GB of new content per month.

Чтобы выдержать 40 average read requests per second (в пике больше), трафик к популярному контенту должен обслуживать **кэш в памяти**, а не база данных. **Кэш в памяти** также полезен при неравномерно распределённом трафике и всплесках нагрузки. **SQL Read Replicas** должны справляться с промахами кэша, пока реплики не перегружены репликацией записей.

4 average paste writes per second (в пике больше) — посильная нагрузка для одного **SQL Write Master-Slave**. В противном случае понадобятся дополнительные шаблоны масштабирования SQL:

* [Федерализация](https://github.com/donnemartin/system-design-primer#federation)
* [Шардирование](https://github.com/donnemartin/system-design-primer#sharding)
* [Денормализация](https://github.com/donnemartin/system-design-primer#denormalization)
* [SQL-тюнинг](https://github.com/donnemartin/system-design-primer#sql-tuning)

Стоит также рассмотреть перенос части данных в **NoSQL-базу**.

## Дополнительные темы для обсуждения

> Дополнительные темы, в которые можно углубиться — в зависимости от объёма задачи и оставшегося времени.

#### NoSQL

* [Хранилище «ключ-значение»](https://github.com/donnemartin/system-design-primer#key-value-store)
* [Документное хранилище](https://github.com/donnemartin/system-design-primer#document-store)
* [Колоночное хранилище](https://github.com/donnemartin/system-design-primer#wide-column-store)
* [Графовая база данных](https://github.com/donnemartin/system-design-primer#graph-database)
* [SQL или NoSQL](https://github.com/donnemartin/system-design-primer#sql-or-nosql)

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
* [Обратное давление (back pressure)](https://github.com/donnemartin/system-design-primer#back-pressure)
* [Микросервисы](https://github.com/donnemartin/system-design-primer#microservices)

### Коммуникации

* Обсуди компромиссы:
    * Внешние коммуникации с клиентами — [HTTP API в стиле REST](https://github.com/donnemartin/system-design-primer#representational-state-transfer-rest)
    * Внутренние коммуникации — [RPC](https://github.com/donnemartin/system-design-primer#remote-procedure-call-rpc)
* [Обнаружение сервисов (service discovery)](https://github.com/donnemartin/system-design-primer#service-discovery)

### Безопасность

Смотри [раздел про безопасность](https://github.com/donnemartin/system-design-primer#security).

### Числа про задержки

Смотри [«Задержки, которые должен знать каждый программист»](https://github.com/donnemartin/system-design-primer#latency-numbers-every-programmer-should-know).

### Не забывай

* Продолжай бенчмаркинг и мониторинг системы, чтобы устранять узкие места по мере их появления
* Масштабирование — это итеративный процесс

---

## 🧠 Своими словами

> Заполняется после того, как решишь задачу соло за 45 минут. Пока пусто.

## ❓ Самопроверка

- [ ] Как ты генерируешь короткую ссылку — MD5+Base62 от ip+timestamp, случайные данные или инкрементальный счётчик через отдельный сервис? В чём разница по коллизиям и предсказуемости?
- [ ] Почему для Pastebin разумно разделить метаданные (SQL) и содержимое пасты (объектное хранилище), а не хранить всё в одной таблице?
- [ ] Как обрабатываешь TTL и удаление истёкших паст — активным сканированием по расписанию или лениво при чтении? Какие компромиссы у каждого варианта при 10 million paste writes per month?
- [ ] Где именно ставишь кэш и что в нём хранишь, учитывая соотношение чтений к записям 10:1?
- [ ] Что будешь делать, когда одного **SQL Write Master** перестанет хватать на запись — федерализация, шардирование или переход части данных в NoSQL? По какому ключу шардировать?
- [ ] Как бы ты добавил поддержку пользовательских (custom) коротких ссылок, которая в этом разборе вынесена за рамки задачи?

## 🔗 Связано

[[Кэш]] · [[Реляционные БД (RDBMS)]] · [[SQL или NoSQL]] · [[Расчёты на салфетке]] · [[RPC и REST]] · [[Асинхронность]]
