---
lang: ru
en: "[[TCP and UDP]]"
tags: [sdp/сеть, sdp/ru]
status: переведено
---

> 🇬🇧 Оригинал: [[TCP and UDP]] · 🗺 [[00 Карта знаний]] · 📖 [[Глоссарий]]

### Протокол управления передачей (TCP)

<p align="center">
  <img src="../../../images/JdAsdvG.jpg">
  <br/>
  <i><a href=http://www.wildbunny.co.uk/blog/2012/10/09/how-to-make-a-multi-player-game-part-1/>Источник: How to make a multiplayer game</a></i>
</p>

TCP — это ориентированный на соединение (connection-oriented) протокол поверх [IP-сети](https://en.wikipedia.org/wiki/Internet_Protocol). Соединение устанавливается и завершается с помощью [рукопожатия (handshake)](https://en.wikipedia.org/wiki/Handshaking). Все отправленные пакеты гарантированно доходят до адресата в исходном порядке и без повреждений благодаря:

* Порядковым номерам и [полям контрольной суммы](https://en.wikipedia.org/wiki/Transmission_Control_Protocol#Checksum_computation) для каждого пакета
* Пакетам [подтверждения (acknowledgement)](https://en.wikipedia.org/wiki/Acknowledgement_(data_networks)) и автоматической повторной отправке

Если отправитель не получает корректного ответа, он повторно отправляет пакеты. При нескольких таймаутах подряд соединение разрывается. TCP также реализует [управление потоком (flow control)](https://en.wikipedia.org/wiki/Flow_control_(data)) и [контроль перегрузки (congestion control)](https://en.wikipedia.org/wiki/Network_congestion#Congestion_control). Эти гарантии вносят задержки и в целом делают передачу менее эффективной, чем в UDP.

Чтобы обеспечить высокую пропускную способность, веб-серверы могут держать открытым большое число TCP-соединений, что ведёт к высокому потреблению памяти. Большое количество открытых соединений между потоками веб-сервера и, скажем, сервером [memcached](https://memcached.org/) может обходиться дорого. Помочь может [пул соединений (connection pooling)](https://en.wikipedia.org/wiki/Connection_pool), а также переход на UDP там, где это уместно.

TCP полезен для приложений, которым важна высокая надёжность, но не критично время отклика. Примеры: веб-серверы, работа с базами данных, SMTP, FTP и SSH.

Используйте TCP вместо UDP, если:

* Нужно, чтобы все данные дошли в целости
* Нужна автоматическая оптимизация под доступную пропускную способность сети

### Протокол пользовательских дейтаграмм (UDP)

<p align="center">
  <img src="../../../images/yzDrJtA.jpg">
  <br/>
  <i><a href=http://www.wildbunny.co.uk/blog/2012/10/09/how-to-make-a-multi-player-game-part-1/>Источник: How to make a multiplayer game</a></i>
</p>

UDP не устанавливает соединение (connectionless). Дейтаграммы (аналог пакетов) гарантированы только на уровне самой дейтаграммы. Они могут приходить не по порядку или вовсе не дойти. UDP не поддерживает контроль перегрузки. Без гарантий, которые есть у TCP, UDP в целом эффективнее.

UDP умеет широковещательную рассылку (broadcast) — отправку дейтаграмм всем устройствам в подсети. Это полезно, например, для [DHCP](https://en.wikipedia.org/wiki/Dynamic_Host_Configuration_Protocol): клиент ещё не получил IP-адрес, а значит TCP не может установить поток данных без адреса.

UDP менее надёжен, но хорошо подходит для сценариев реального времени: VoIP, видеочаты, стриминг, многопользовательские игры в реальном времени.

Используйте UDP вместо TCP, если:

* Нужна минимальная задержка
* Устаревшие данные хуже, чем потерянные данные
* Нужно реализовать собственную коррекцию ошибок

#### Источники и дополнительные материалы: TCP и UDP

* [Networking for game programming](https://gafferongames.com/post/udp_vs_tcp/)
* [Key differences between TCP and UDP protocols](http://www.cyberciti.biz/faq/key-differences-between-tcp-and-udp-protocols/)
* [Difference between TCP and UDP](http://stackoverflow.com/questions/5970383/difference-between-tcp-and-udp)
* [Transmission control protocol](https://en.wikipedia.org/wiki/Transmission_Control_Protocol)
* [User datagram protocol](https://en.wikipedia.org/wiki/User_Datagram_Protocol)
* [Scaling memcache at Facebook](http://www.cs.bu.edu/~jappavoo/jappavoo.github.com/451/papers/memcache-fb.pdf)

---

## 🧠 Своими словами

> Главная часть заметки — заполняется тобой, не переводом. Пока пусто.

## ❓ Самопроверка

- [ ] Почему TCP медленнее UDP и какими механизмами это обеспечивается?
- [ ] В каком сценарии предпочтительнее UDP, а не TCP? Приведи два примера.
- [ ] Что такое connection pooling и зачем он нужен при большом числе TCP-соединений?
- [ ] Почему UDP хорошо подходит для DHCP, а TCP — нет?
- [ ] Что сломается в потоковом видеозвонке, если заменить UDP на TCP?

## 🔗 Связано

[[Протокол HTTP]] · [[RPC и REST]] · [[Задержка и пропускная способность]] · [[Коммуникации]] · [[Балансировщик нагрузки]]
