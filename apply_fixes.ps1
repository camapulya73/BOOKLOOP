# Применяет исправления занятия 14 отдельными коммитами (один дефект = один коммит).
# Запуск: открыть PowerShell в корне проекта (там, где manage.py), на ветке с исходниками из архива BOOKLOOP_Django.zip:
#   powershell -ExecutionPolicy Bypass -File путь\к\apply_fixes.ps1
param([string]$PatchDir = (Join-Path $PSScriptRoot "patches"))
$ErrorActionPreference = "Stop"
$utf8 = New-Object System.Text.UTF8Encoding $false
$items = @(
  @{ file = "01_BUG-01.patch"; title = "BUG-01: поиск и фильтр города больше не зависят от регистра кириллицы (SQLite)"; body = "Тест-кейс TC-44, шаг 7: запрос «оруэлл» строчными возвращал 0 книг. Подменяем like() в SQLite на Unicode-вариант (core/sqlite_unicode.py)." },
  @{ file = "02_BUG-02.patch"; title = "BUG-02: список «Состояние» в каталоге сохраняет выбранное значение после поиска"; body = "Тест-кейс TC-04, шаг 5: после поиска список сбрасывался на «Любое»." },
  @{ file = "03_BUG-03.patch"; title = "BUG-03: экземпляр на модерации или отклонённый не открывается по прямой ссылке постороннему"; body = "Тест-кейс TC-47, шаг 2: гость видел карточку экземпляра со статусом «На модерации». Доступ оставлен владельцу и сотрудникам (модерация)." },
  @{ file = "04_BUG-04.patch"; title = "BUG-04: живой поиск учитывает город, жанр и состояние, как и страница каталога"; body = "Раньше API /api/books/search/ и app.js передавали и применяли только строку q. Фильтры вынесены в общую функцию _filter_copies()." },
  @{ file = "05_BUG-10.patch"; title = "BUG-10: живой поиск возвращает все найденные книги, а не первые 30"; body = "Без запроса API отвечал count=30 при 52 книгах в каталоге; счётчик «Найдено» показывал 30." },
  @{ file = "06_BUG-05.patch"; title = "BUG-05: счётчик «книг в сообществе» в профиле считает только одобренные экземпляры"; body = "Счётчик учитывал книги на модерации, а список под ним показывал только одобренные." },
  @{ file = "07_BUG-06.patch"; title = "BUG-06: владелец не может принять вторую заявку на уже занятый экземпляр"; body = "Раньше три заявки на один экземпляр можно было принять, все получали статус «Принята»." },
  @{ file = "08_BUG-07.patch"; title = "BUG-07: сообщение об ошибке email на сервере совпадает с клиентской проверкой и автотестом"; body = "Сервер выдавал «Введите правильный адрес…», JS и test_registration_form_keeps_validation_errors ждали «корректный»." },
  @{ file = "09_BUG-08.patch"; title = "BUG-08: fixtures/demo.json сохранён в UTF-8, экспорт фикстуры пишет UTF-8"; body = "loaddata падал с UnicodeDecodeError: файл был в Windows-1251, Django читает JSON как UTF-8." },
  @{ file = "10_BUG-09.patch"; title = "BUG-09: в избранное нельзя добавить собственный экземпляр и экземпляр, не прошедший модерацию"; body = "Интерфейс скрывал кнопку, но прямой POST /books/<id>/favorite/ принимался." },
  @{ file = "11_BUG-12.patch"; title = "BUG-12: кнопка мобильного меню имеет размер не меньше 44×44 px"; body = "Тест-кейс TC-48, шаг 5: размер кнопки ☰ был около 39×44 px (NFR-04). Добавлены min-width и min-height." },
  @{ file = "12_BUG-11.patch"; title = "BUG-11: основная навигация доступна без JavaScript на мобильной ширине"; body = "Тест-кейс TC-49: при ширине до 768 px меню было скрыто и открывалось только скриптом. Теперь выпадающее меню включается классом js (base.html), без скрипта ссылки видны под логотипом." }
)
foreach ($it in $items) {
  $patch = Join-Path $PatchDir $it.file
  Write-Host ("Применяю " + $it.file)
  git apply --ignore-whitespace $patch
  if ($LASTEXITCODE -ne 0) { throw ("Не удалось применить " + $it.file) }
  $files = @(git apply --numstat $patch | ForEach-Object { ($_ -split "`t")[2] })
  if ($it.file -like "*BUG-08*") {
    # fixtures/demo.json: перекодировать из Windows-1251 в UTF-8
    python -c "p='fixtures/demo.json'; d=open(p,'rb').read(); open(p,'wb').write(d.decode('cp1251').encode('utf-8'))"
    if ($LASTEXITCODE -ne 0) { throw "Не удалось перекодировать fixtures/demo.json" }
    $files += "fixtures/demo.json"
  }
  git add -- $files
  $msgFile = [System.IO.Path]::GetTempFileName()
  [System.IO.File]::WriteAllText($msgFile, $it.title + "`n`n" + $it.body + "`n", $utf8)
  git commit -F $msgFile
  Remove-Item $msgFile
}
Write-Host "Готово: создано коммитов - $($items.Count)"
git log --oneline -n $items.Count
