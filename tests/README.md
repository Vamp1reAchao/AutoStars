# Тесты

Тесты не устанавливаются через `pip install tests`. Это локальный пакет тестов проекта.

## Из корня проекта

```bat
python -m unittest discover -s tests -v
```

## Запуск отдельного теста

```bat
python tests\test_fragment_and_trace.py
python tests\test_order_parsing.py
python tests\test_config.py
python tests\test_preflight.py
python tests\test_gui_regressions.py
```

## Из каталога tests

Все тестовые файлы поддерживают прямой запуск:

```bat
cd tests
python test_fragment_and_trace.py
```

или используйте:

```bat
tests\run_tests.bat
```
