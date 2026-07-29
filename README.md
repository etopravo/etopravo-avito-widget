# etopravo-avito-widget

Виджет отзывов с Авито для сайта **etopravo.ru**. Своя альтернатива платному smartwidgets.ru — **0 ₽/мес**.

## Что делает

1. Раз в 6 часов идёт в публичный JSON-API Авито и забирает **все отзывы** магазина `etopravo`.
2. Генерирует статический `widget.html` в фирменной палитре сайта.
3. Публикует на GitHub Pages по URL, который ты вставляешь в Тильду через `<iframe>`.

## Локальный запуск

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/fetch_reviews.py     # data/reviews.json
.venv/bin/python scripts/render_widget.py     # web/widget.html
```

Открыть локально:

```bash
cd web && python3 -m http.server 8765
# → http://localhost:8765/widget.html
```

## Автообновление на GitHub

`.github/workflows/update.yml` — раз в 6 часов запускает fetch + render, коммитит и деплоит на GitHub Pages. Полностью бесплатно (2000 мин Actions/мес, нам нужно ~10).

---

## Как включить (для Руслана — пошагово)

### Шаг 1. Регистрация на GitHub (5 минут)

1. Перейти на <https://github.com/signup>
2. Email → пароль → username (например `kachkaevra`)
3. Подтвердить email по коду из письма
4. На вопрос «What is your role?» и подобные — жать **Skip personalization**
5. Тариф — **Free**

### Шаг 2. Создать репозиторий

1. <https://github.com/new>
2. Repository name: `etopravo-avito-widget`
3. Visibility: **Public** *(бесплатный GitHub Pages работает только для публичных репо)*
4. Ничего не отмечай («Add README», «gitignore», «license» — **не надо**, у нас уже всё готово)
5. **Create repository**

### Шаг 3. Залить код (одна команда в терминале)

Открой Terminal, вставь и запусти. Замени `<TVOI_USERNAME>` на свой (например `kachkaevra`):

```bash
cd ~/etopravo-avito-widget
git init -b main
git add .
git commit -m "initial commit"
git remote add origin https://github.com/<TVOI_USERNAME>/etopravo-avito-widget.git
git push -u origin main
```

GitHub попросит логин и **токен вместо пароля** — сгенерируй его на <https://github.com/settings/tokens?type=beta> → **Generate new token** → выбери репо `etopravo-avito-widget` → права `Contents: Read and write` → сохрани в надёжном месте, вставь в терминал вместо пароля.

### Шаг 4. Включить GitHub Pages

1. В своём репозитории: **Settings** → **Pages** (в левом меню)
2. **Source: GitHub Actions**
3. Всё, кнопка «Save» не нужна.

### Шаг 5. Первый прогон workflow

1. **Actions** → «Update reviews» → **Run workflow** → **Run workflow** (зелёная кнопка)
2. Через 1-2 минуты появится ссылка на опубликованную страницу вида:
   `https://<TVOI_USERNAME>.github.io/etopravo-avito-widget/widget.html`

### Шаг 6. Заменить iframe на Тильде

Открой блок T123 на страницах где висит виджет smartwidgets, замени на:

```html
<iframe
  src="https://<TVOI_USERNAME>.github.io/etopravo-avito-widget/widget.html"
  width="100%"
  height="600"
  frameborder="0"
  loading="lazy"
  style="border:0"
></iframe>
```

### Шаг 7. Отменить подписку на smartwidgets.ru

Оплачивать больше не надо.

---

## Что если API Авито закроется?

Fallback-план (пока не нужен): скрапить страницу `avito.ru/brands/etopravo` через headless-браузер с residential-прокси (~$3/мес). Переезд занимает 2 часа моего времени.

## Что если сломается

- `Actions` → красный крестик = что-то упало. Открой лог, скинь ошибку.
- Скорее всего это будет означать что Авито поменял поле в JSON. Правится за 15 минут.
