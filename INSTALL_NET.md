# 📦 Установка .NET Framework для AutoStars

## 🎯 Что скачать:

### ✅ **Microsoft .NET Framework 4.8.1 Developer Pack**
- **Ссылка**: https://dotnet.microsoft.com/download/dotnet-framework/net481
- **Файл**: `ndp481-devpack-enu.exe` (~320 MB)
- **Включает**: Компилятор, библиотеки, инструменты разработки

## 🚀 Быстрая установка:

### 1️⃣ **Скачайте Developer Pack**
```
https://download.microsoft.com/download/9/6/F/96FD0525-3DDF-423D-8845-5F92F4A6883E/ndp481-devpack-enu.exe
```

### 2️⃣ **Запустите установку**
- Запустите `ndp481-devpack-enu.exe` от имени администратора
- Следуйте инструкциям установщика
- Перезагрузите компьютер после установки

### 3️⃣ **Проверьте установку**
```cmd
dir "C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8.1"
```

## 🔧 Альтернативные варианты:

### **Если нужен только Runtime:**
- **.NET Framework 4.8.1 Runtime** (~60 MB)
- Только для запуска приложений, без компиляции

### **Если есть Visual Studio:**
- Visual Studio автоматически установит нужные компоненты
- Выберите ".NET Framework 4.8.1 targeting pack"

## ⚡ После установки:

1. Запустите `build_wpf_auto.bat`
2. Скрипт автоматически найдет .NET Framework 4.8.1
3. Соберет AutoStars.exe с оптимизациями

## 🎯 Что даст Developer Pack:

- ✅ **Компилятор C#** (csc.exe)
- ✅ **WPF библиотеки** (PresentationFramework.dll)
- ✅ **Reference Assemblies** для IntelliSense
- ✅ **MSBuild поддержка**
- ✅ **Отладочные символы**

## 🔍 Проверка версии:
```cmd
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full\" /v Release
```
- **Значение 533320+** = .NET Framework 4.8.1 установлен

---
**💡 Совет**: Developer Pack - это всё что нужно для сборки AutoStars GUI!