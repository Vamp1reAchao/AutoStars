# Testing

Run the lightweight checks:

```bash
python -m unittest discover -s tests -v
```

The repository also includes a CI workflow that runs syntax checks and the test suite.

## What is covered

- config validation
- order parsing
- TON address canonicalization
- Fragment purchase quantity handling
- trace finalization logic
- preflight startup checks

## Windows: прямой запуск

Тесты не являются пакетом PyPI, поэтому команда `pip install tests` не нужна. Каждый тест поддерживает прямой запуск из каталога `tests`, а весь набор можно запустить через `tests\run_tests.bat`.

```bat
cd tests
python test_fragment_and_trace.py
```

Для полного набора из корня проекта:

```bat
python -m unittest discover -s tests -v
```
