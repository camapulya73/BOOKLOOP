# Связи сущностей и кардинальности — приложение `core`

- Reader 1 — 1 ReaderProfile: у каждого зарегистрированного читателя один профиль.
- Book N — M Genre через BookGenre: одна книга может иметь несколько жанров, один жанр может относиться к нескольким произведениям.
- Book 1 — 0..N Copy: произведение может иметь несколько физических экземпляров.
- ReaderProfile 1 — 0..N Copy: читатель может владеть несколькими экземплярами.
- Copy 1 — 0..N CopyPhoto: у экземпляра может быть несколько фотографий.
- Copy 1 — 0..N Exchange: на экземпляр могут поступать заявки на обмен.
- ReaderProfile 1 — 0..N Exchange: профиль может создавать заявки.
- Exchange 1 — 0..N ExchangeStatusLog: журнал хранит изменения статусов.
- Reader 1 — 0..N ExchangeStatusLog: читатель/модератор фиксирует изменение статуса.
- Exchange 1 — 0..1 Complaint: к заявке может быть привязана одна жалоба.
- Exchange 1 — 0..1 Review: после обмена может быть создан один отзыв.
- ReaderProfile 1 — 0..N Review как автор и отдельно как получатель.

В канонической схеме 11 моделей: Reader, ReaderProfile, Book, Genre, BookGenre, Copy,
CopyPhoto, Exchange, ExchangeStatusLog, Complaint и Review. Имена таблиц в SQLite
создаются Django автоматически с префиксом `core_`.

Связь Book↔Genre реализована как настоящая M:N: поле `Book.genres` использует
промежуточную модель `BookGenre`; в ней внешний ключ `genre` хранится в SQL-колонке
`genre` и ссылается на уникальное поле `Genre.name`.
