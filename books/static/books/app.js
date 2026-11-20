document.addEventListener('DOMContentLoaded', () => {
    // Мобильное меню.
    const menuButton = document.querySelector('.menu-toggle');
    const navigation = document.querySelector('.nav');
    if (menuButton && navigation) {
        menuButton.addEventListener('click', () => {
            const isOpen = navigation.classList.toggle('open');
            menuButton.setAttribute('aria-expanded', String(isOpen));
            menuButton.setAttribute('aria-label', isOpen ? 'Закрыть меню' : 'Открыть меню');
        });
    }

    // Клиентская проверка обязательных полей, email, телефона и длины текста.
    document.querySelectorAll('form[data-validate-form]').forEach((form) => {
        form.addEventListener('submit', (event) => {
            let firstInvalid = null;
            form.querySelectorAll('[required]').forEach((field) => {
                field.setCustomValidity('');
                if (!field.checkValidity()) {
                    field.reportValidity();
                    firstInvalid = firstInvalid || field;
                }
            });
            form.querySelectorAll('input[type="email"]').forEach((field) => {
                field.setCustomValidity('');
                if (field.value && !field.checkValidity()) {
                    field.setCustomValidity('Введите корректный адрес электронной почты.');
                    firstInvalid = firstInvalid || field;
                }
            });
            form.querySelectorAll('input[type="tel"]').forEach((field) => {
                field.setCustomValidity('');
                if (field.value && !/^\+7\d{10}$/.test(field.value.trim())) {
                    field.setCustomValidity('Введите телефон в формате +79991234567.');
                    firstInvalid = firstInvalid || field;
                }
            });
            form.querySelectorAll('input[maxlength], textarea[maxlength]').forEach((field) => {
                field.setCustomValidity('');
                if (field.value.length > Number(field.maxLength)) {
                    field.setCustomValidity(`Максимальная длина — ${field.maxLength} символов.`);
                    firstInvalid = firstInvalid || field;
                }
            });
            form.querySelectorAll('input[minlength], textarea[minlength]').forEach((field) => {
                field.setCustomValidity('');
                if (field.value && field.value.length < Number(field.minLength)) {
                    field.setCustomValidity(`Минимальная длина — ${field.minLength} символа.`);
                    firstInvalid = firstInvalid || field;
                }
            });
            if (firstInvalid) {
                event.preventDefault();
                firstInvalid.reportValidity();
            }
        });
    });

    // Динамический элемент № 1: живой поиск каталога через собственное JSON-представление.
    const searchInput = document.querySelector('#live-book-search');
    const resultsBox = document.querySelector('#book-results');
    const searchStatus = document.querySelector('#search-status');
    if (searchInput && resultsBox && searchStatus) {
        let timer = null;
        let controller = null;
        const searchUrl = resultsBox.dataset.searchUrl;

        const makeCard = (book) => {
            const article = document.createElement('article');
            article.className = 'card';
            const link = document.createElement('a');
            link.className = 'cover';
            link.href = book.url;
            if (book.cover) {
                const image = document.createElement('img');
                image.src = book.cover;
                image.alt = `Обложка книги ${book.title}`;
                image.loading = 'lazy';
                image.width = 300;
                image.height = 420;
                link.append(image);
            } else {
                const title = document.createElement('strong');
                title.textContent = book.title;
                const author = document.createElement('small');
                author.textContent = book.author;
                link.append(title, author);
            }
            const body = document.createElement('div');
            body.className = 'cardbody';
            const condition = document.createElement('span');
            condition.className = 'tag';
            condition.textContent = book.condition;
            const heading = document.createElement('h3');
            const titleLink = document.createElement('a');
            titleLink.href = book.url;
            titleLink.textContent = book.title;
            heading.append(titleLink);
            const authorText = document.createElement('p');
            authorText.textContent = book.author;
            const city = document.createElement('small');
            city.textContent = book.city;
            body.append(condition, heading, authorText, city);
            article.append(link, body);
            return article;
        };

        const runSearch = async () => {
            if (controller) controller.abort();
            controller = new AbortController();
            const params = new URLSearchParams({ q: searchInput.value.trim() });
            searchStatus.textContent = 'Ищем книги…';
            resultsBox.setAttribute('aria-busy', 'true');
            try {
                const response = await fetch(`${searchUrl}?${params.toString()}`, {
                    headers: { 'Accept': 'application/json' },
                    signal: controller.signal,
                });
                if (!response.ok) throw new Error('Не удалось загрузить каталог.');
                const data = await response.json();
                resultsBox.replaceChildren();
                if (data.results.length) {
                    data.results.forEach((book) => resultsBox.append(makeCard(book)));
                } else {
                    const empty = document.createElement('div');
                    empty.className = 'empty';
                    const heading = document.createElement('h2');
                    heading.textContent = 'Ничего не найдено';
                    const message = document.createElement('p');
                    message.textContent = 'Попробуйте изменить поисковый запрос.';
                    empty.append(heading, message);
                    resultsBox.append(empty);
                }
                searchStatus.textContent = `Найдено: ${data.count}`;
            } catch (error) {
                if (error.name !== 'AbortError') searchStatus.textContent = error.message;
            } finally {
                resultsBox.removeAttribute('aria-busy');
            }
        };

        searchInput.addEventListener('input', () => {
            window.clearTimeout(timer);
            timer = window.setTimeout(runSearch, 250);
        });
    }

    // Динамический элемент № 2: добавление/удаление книги из избранного без перезагрузки.
    document.querySelectorAll('form[data-favorite-form]').forEach((form) => {
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            const button = form.querySelector('button[type="submit"]');
            const status = form.querySelector('[data-favorite-status]');
            const csrf = form.querySelector('[name="csrfmiddlewaretoken"]')?.value;
            button.disabled = true;
            status.textContent = 'Сохраняем…';
            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrf,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json',
                    },
                    body: new FormData(form),
                });
                const data = await response.json();
                if (!response.ok || !data.success) throw new Error(data.error || 'Не удалось обновить избранное.');
                button.textContent = data.label;
                button.setAttribute('aria-pressed', String(data.is_favorite));
                status.textContent = data.is_favorite ? 'Книга добавлена в избранное.' : 'Книга удалена из избранного.';
            } catch (error) {
                status.textContent = error.message;
            } finally {
                button.disabled = false;
            }
        });
    });
});
