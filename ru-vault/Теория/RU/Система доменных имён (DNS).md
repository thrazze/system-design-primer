---
lang: ru
en: "[[Domain name system]]"
tags: [sdp/сеть, sdp/ru]
status: переведено
---

> 🇬🇧 Оригинал: [[Domain name system]] · 🗺 [[00 Карта знаний]] · 📖 [[Глоссарий]]

# Система доменных имён (DNS)

<p align="center">
  <img src="../../../images/IOyLj4i.jpg">
  <br/>
  <i><a href=http://www.slideshare.net/srikrupa5/dns-security-presentation-issa>Источник: DNS security presentation</a></i>
</p>

Система доменных имён (DNS) преобразует доменное имя вроде www.example.com в IP-адрес.

DNS устроена иерархически: на верхнем уровне работает несколько авторитетных серверов. Роутер или интернет-провайдер сообщает, к каким DNS-серверам обращаться при поиске. DNS-серверы нижних уровней кэшируют соответствия имени и адреса, которые могут устареть из-за задержек распространения изменений (DNS propagation delay). Результаты DNS-запросов также кэшируют браузер или ОС — на срок, заданный [TTL (time to live)](https://en.wikipedia.org/wiki/Time_to_live).

* **NS-запись (name server)** — задаёт DNS-серверы для домена или поддомена.
* **MX-запись (mail exchange)** — задаёт почтовые серверы для приёма сообщений.
* **A-запись (address)** — сопоставляет имя с IP-адресом.
* **CNAME (canonical)** — сопоставляет имя с другим именем или `CNAME` (например, example.com → www.example.com) либо с `A`-записью.

Такие сервисы, как [CloudFlare](https://www.cloudflare.com/dns/) и [Route 53](https://aws.amazon.com/route53/), предоставляют управляемый DNS. Некоторые DNS-сервисы умеют маршрутизировать трафик разными способами:

* [Взвешенный round robin (weighted round robin)](https://www.jscape.com/blog/load-balancing-algorithms)
    * Не пускать трафик на серверы, находящиеся на обслуживании
    * Балансировать между кластерами разного размера
    * A/B-тестирование
* [На основе задержки (latency-based)](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy-latency.html)
* [На основе геолокации (geolocation-based)](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy-geo.html)

### Недостатки: DNS

* Обращение к DNS-серверу добавляет небольшую задержку, хотя описанное выше кэширование её сглаживает.
* Управление DNS-серверами может быть сложным делом — этим, как правило, занимаются [государства, интернет-провайдеры и крупные компании](http://superuser.com/questions/472695/who-controls-the-dns-servers/472729).
* DNS-сервисы не раз становились целью [DDoS-атак](http://dyn.com/blog/dyn-analysis-summary-of-friday-october-21-attack/), из-за чего пользователи не могли открыть такие сайты, как Twitter, не зная их IP-адресов.

### Источники и дополнительные материалы

* [DNS architecture](https://technet.microsoft.com/en-us/library/dd197427(v=ws.10).aspx)
* [Wikipedia](https://en.wikipedia.org/wiki/Domain_Name_System)
* [DNS articles](https://support.dnsimple.com/categories/dns/)

---

## 🧠 Своими словами

> Главная часть заметки — заполняется тобой, не переводом. Пока пусто.

## ❓ Самопроверка

- [ ] Почему TTL DNS-записи — это компромисс между скоростью распространения изменений и нагрузкой на DNS-серверы?
- [ ] Чем CNAME отличается от A-записи и почему CNAME обычно нельзя поставить на корневой домен?
- [ ] Что случится с доступностью сервиса, если атака положит его DNS-провайдера, даже если серверы приложения работают нормально?
- [ ] В чём разница между geolocation-based и latency-based маршрутизацией и когда выбрать одну, а когда другую?
- [ ] Как задержка распространения DNS влияет на план отката при смене IP-адреса продакшен-сервера?

## 🔗 Связано

[[Сеть доставки контента (CDN)]] · [[Балансировщик нагрузки]] · [[Протокол HTTP]] · [[Задержка и пропускная способность]] · [[Безопасность]]
