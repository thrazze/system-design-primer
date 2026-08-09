#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Разбивает README.md и solutions/*/README.md системного-дизайн-праймера
на атомарные заметки Obsidian.

Генерирует EN-заметки (оригинал, автоматически) и заглушки RU-заметок,
связывая пары двусторонними wiki-ссылками.

Запуск из корня репозитория:  python3 ru-vault/_служебное/split.py
"""
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VAULT = os.path.join(REPO, "ru-vault")

# ─────────────────────────────────────────────────────────────────────────────
# Карта разбиения README.md.
#   (заголовок-начало, заголовок-конец|None, EN-имя, RU-имя, папка, тег)
# «заголовок-конец» = None → до следующего заголовка того же уровня.
# ─────────────────────────────────────────────────────────────────────────────
README_MAP = [
    # ── Методика ────────────────────────────────────────────────────────────
    ("## Study guide", None,
     "Study guide", "Руководство по обучению", "Методика", "метод"),
    ("## How to approach a system design interview question", None,
     "How to approach a system design interview question",
     "Каркас ответа на собеседовании", "Методика", "метод"),
    ("### Back-of-the-envelope calculations", "### Source(s) and further reading",
     "Back-of-the-envelope calculations", "Расчёты на салфетке", "Методика", "метод"),

    # ── Базовые компромиссы ─────────────────────────────────────────────────
    ("## Performance vs scalability", None,
     "Performance vs scalability", "Производительность и масштабируемость",
     "Теория", "основы"),
    ("## Latency vs throughput", None,
     "Latency vs throughput", "Задержка и пропускная способность",
     "Теория", "основы"),
    ("## Availability vs consistency", None,
     "Availability vs consistency", "Доступность и согласованность (CAP)",
     "Теория", "основы"),
    ("## Consistency patterns", None,
     "Consistency patterns", "Шаблоны согласованности", "Теория", "основы"),
    ("## Availability patterns", None,
     "Availability patterns", "Шаблоны доступности", "Теория", "основы"),

    # ── Путь запроса ────────────────────────────────────────────────────────
    ("## Domain name system", None,
     "Domain name system", "Система доменных имён (DNS)", "Теория", "сеть"),
    ("## Content delivery network", None,
     "Content delivery network", "Сеть доставки контента (CDN)", "Теория", "сеть"),
    ("## Load balancer", None,
     "Load balancer", "Балансировщик нагрузки", "Теория", "сеть"),
    ("## Reverse proxy (web server)", None,
     "Reverse proxy", "Обратный прокси", "Теория", "сеть"),
    ("## Application layer", None,
     "Application layer", "Уровень приложений", "Теория", "сеть"),

    # ── Данные ──────────────────────────────────────────────────────────────
    ("## Database", "### Relational database management system (RDBMS)",
     "Database", "Базы данных", "Теория", "данные"),
    ("### Relational database management system (RDBMS)", "### NoSQL",
     "Relational database management system", "Реляционные БД (RDBMS)",
     "Теория", "данные"),
    ("### NoSQL", "### SQL or NoSQL",
     "NoSQL", "NoSQL — типы хранилищ", "Теория", "данные"),
    ("### SQL or NoSQL", "## Cache",
     "SQL or NoSQL", "SQL или NoSQL", "Теория", "данные"),

    # ── Кэш и асинхронность ─────────────────────────────────────────────────
    ("## Cache", None, "Cache", "Кэш", "Теория", "данные"),
    ("## Asynchronism", None, "Asynchronism", "Асинхронность", "Теория", "данные"),

    # ── Коммуникации ────────────────────────────────────────────────────────
    ("## Communication", "### Hypertext transfer protocol (HTTP)",
     "Communication", "Коммуникации", "Теория", "сеть"),
    ("### Hypertext transfer protocol (HTTP)", "### Transmission control protocol (TCP)",
     "HTTP", "Протокол HTTP", "Теория", "сеть"),
    ("### Transmission control protocol (TCP)", "### Remote procedure call (RPC)",
     "TCP and UDP", "TCP и UDP", "Теория", "сеть"),
    ("### Remote procedure call (RPC)", "## Security",
     "RPC and REST", "RPC и REST", "Теория", "сеть"),
    ("## Security", None, "Security", "Безопасность", "Теория", "сеть"),

    # ── Приложение ──────────────────────────────────────────────────────────
    ("### Powers of two table", "### Additional system design interview questions",
     "Numbers every programmer should know",
     "Цифры, которые надо знать наизусть", "Справочник", "справочник"),
    ("### Additional system design interview questions", "### Real world architectures",
     "Additional interview questions", "Дополнительные задачи",
     "Справочник", "справочник"),
    ("### Real world architectures", "### Company architectures",
     "Real world architectures", "Реальные архитектуры", "Справочник", "справочник"),
    ("### Company architectures", "### Company engineering blogs",
     "Company architectures", "Архитектуры компаний", "Справочник", "справочник"),
    ("### Company engineering blogs", "## Under development",
     "Company engineering blogs", "Инженерные блоги компаний",
     "Справочник", "справочник"),
]

# solutions/<dir> → (EN-имя, RU-имя)
SOLUTIONS_MAP = {
    "pastebin":    ("Design Pastebin.com", "Задача — Pastebin и bit.ly"),
    "twitter":     ("Design the Twitter timeline and search",
                    "Задача — лента и поиск Twitter"),
    "web_crawler": ("Design a web crawler", "Задача — веб-краулер"),
    "mint":        ("Design Mint.com", "Задача — Mint.com"),
    "social_graph": ("Design the data structures for a social network",
                     "Задача — структуры данных соцсети"),
    "query_cache": ("Design a key-value store for a search engine",
                    "Задача — key-value хранилище для поисковика"),
    "sales_rank":  ("Design Amazon's sales ranking by category feature",
                    "Задача — ранжирование продаж Amazon"),
    "scaling_aws": ("Design a system that scales to millions of users on AWS",
                    "Задача — масштабирование до миллионов пользователей на AWS"),
}


def slug(text):
    """GitHub-совместимый якорь из текста заголовка."""
    t = text.lower()
    t = re.sub(r"[^\w\s-]", "", t, flags=re.UNICODE)
    return re.sub(r"[\s_]+", "-", t).strip("-")


def extract(lines, start, end):
    """Вырезает блок от заголовка start до заголовка end (не включая)."""
    try:
        i = next(k for k, l in enumerate(lines) if l.strip() == start)
    except StopIteration:
        print(f"  !! не найден заголовок: {start}", file=sys.stderr)
        return None
    level = len(start) - len(start.lstrip("#"))
    if end:
        j = next((k for k in range(i + 1, len(lines)) if lines[k].strip() == end),
                 len(lines))
    else:
        j = next((k for k in range(i + 1, len(lines))
                  if re.match(r"^#{1,%d} " % level, lines[k])), len(lines))
    return "\n".join(lines[i:j]).rstrip()


def build_anchor_index(mapping):
    """anchor → EN-имя заметки, для перелинковки внутренних ссылок."""
    idx = {}
    for start, _e, en, _ru, _f, _t in mapping:
        idx[slug(start.lstrip("# ").strip())] = en
    # ссылки на разделы, которые не стали отдельными заметками
    idx.setdefault("microservices", "Application layer")
    idx.setdefault("service-discovery", "Application layer")
    idx.setdefault("message-queues", "Asynchronism")
    idx.setdefault("task-queues", "Asynchronism")
    idx.setdefault("back-pressure", "Asynchronism")
    idx.setdefault("cap-theorem", "Availability vs consistency")
    idx.setdefault("fail-over", "Availability patterns")
    idx.setdefault("replication", "Availability patterns")
    idx.setdefault("sharding", "Relational database management system")
    idx.setdefault("federation", "Relational database management system")
    idx.setdefault("denormalization", "Relational database management system")
    idx.setdefault("sql-tuning", "Relational database management system")
    idx.setdefault("key-value-store", "NoSQL")
    idx.setdefault("document-store", "NoSQL")
    idx.setdefault("wide-column-store", "NoSQL")
    idx.setdefault("graph-database", "NoSQL")
    idx.setdefault("latency-numbers-every-programmer-should-know",
                   "Numbers every programmer should know")
    idx.setdefault("powers-of-two-table", "Numbers every programmer should know")
    return idx


def relink(body, anchors, depth):
    """Якорные ссылки → wiki-ссылки; пути к картинкам → относительно заметки."""
    up = "../" * depth

    def repl(m):
        text, anchor = m.group(1), m.group(2)
        target = anchors.get(anchor)
        return f"[[{target}|{text}]]" if target else text

    body = re.sub(r"\[([^\]]+)\]\(#([a-z0-9-]+)\)", repl, body)
    body = re.sub(r"(src=\"|\]\()images/", r"\g<1>" + up + "images/", body)

    # В строках таблиц неэкранированный "|" внутри [[цель|текст]] ломает рендер
    # Obsidian: разбивает ячейку надвое. Экранируем.
    out = []
    for line in body.split("\n"):
        if line.lstrip().startswith("|"):
            line = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"[[\1\\|\2]]", line)
        out.append(line)
    return "\n".join(out)


def write_note(path, frontmatter, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fm = "---\n" + "\n".join(f"{k}: {v}" for k, v in frontmatter.items()) + "\n---\n\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(fm + body + "\n")


def main():
    src = open(os.path.join(REPO, "README.md"), encoding="utf-8").read()
    lines = src.split("\n")
    anchors = build_anchor_index(README_MAP)

    made = 0
    for start, end, en, ru, folder, tag in README_MAP:
        body = extract(lines, start, end)
        if body is None:
            continue
        body = relink(body, anchors, depth=3)

        en_path = os.path.join(VAULT, folder, "EN", f"{en}.md")
        write_note(en_path,
                   {"lang": "en", "ru": f'"[[{ru}]]"', "tags": f"[sdp/{tag}, sdp/en]",
                    "status": "исходник"},
                   f"> 🇷🇺 Перевод: [[{ru}]]\n\n" + body)

        ru_path = os.path.join(VAULT, folder, "RU", f"{ru}.md")
        if not os.path.exists(ru_path):
            write_note(ru_path,
                       {"lang": "ru", "en": f'"[[{en}]]"', "tags": f"[sdp/{tag}, sdp/ru]",
                        "status": "не переведено"},
                       f"> 🇬🇧 Оригинал: [[{en}]]\n\n# {ru}\n\n"
                       f"_Перевод ещё не сделан._\n")
        made += 1

    for d, (en, ru) in SOLUTIONS_MAP.items():
        p = os.path.join(REPO, "solutions", "system_design", d, "README.md")
        if not os.path.exists(p):
            print(f"  !! нет файла {p}", file=sys.stderr)
            continue
        # решения используют внешние imgur-ссылки, локальные пути править не нужно
        body = relink(open(p, encoding="utf-8").read().rstrip(), anchors, depth=3)

        write_note(os.path.join(VAULT, "Задачи", "EN", f"{en}.md"),
                   {"lang": "en", "ru": f'"[[{ru}]]"', "tags": "[sdp/задача, sdp/en]",
                    "status": "исходник"},
                   f"> 🇷🇺 Перевод: [[{ru}]]\n\n" + body)

        ru_path = os.path.join(VAULT, "Задачи", "RU", f"{ru}.md")
        if not os.path.exists(ru_path):
            write_note(ru_path,
                       {"lang": "ru", "en": f'"[[{en}]]"', "tags": "[sdp/задача, sdp/ru]",
                        "status": "не переведено"},
                       f"> 🇬🇧 Оригинал: [[{en}]]\n\n# {ru}\n\n_Перевод ещё не сделан._\n")
        made += 1

    print(f"Готово: {made} пар заметок в {VAULT}")


if __name__ == "__main__":
    main()
