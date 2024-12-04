# Table of Languages
- [English](#English)
- [Русский](#Русский)
# English
# Tonxdao - Auto Claim Bot

🔗 **Referral Link**: [Tonxdao](https://t.me/tonxdao_bot?start=ref_288096037)

## 🌟 Features

| Feature        | Status | Description                                |
| -------------- | ------ | ------------------------------------------ |
| Auto Check-in  | On/Off | Daily login to get points and game tickets |
| Auto Do Task   | On/Off | Complete tasks                             |
| Auto Farm	  	 | On/Off | Farm points based on available energy      |


## 🧑‍🔧 How to install in Linux
#Linux
```shell
apt install -y git python3 python3-pip
git clone https://github.com/Omnividente/tonxdao.git
cd tonxdao-bot/
python3 -m pip install -r requirements.txt
```
Enter you (`query_id=... /user=...`) in file data.txt. Each new token from a new line.

To change a file in bash use the command `nano data.txt`

`ctrl+o` `enter` -  save file.

`ctrl+x` -  exit editor.


Modify the config.json file as desired.

To enable functions set `true`
To disable functions `false`

To change a config file in bash use the command `nano config.json`

## 👩‍🔧 How to install in Windows
#Windows
1. Make sure you computer was installed python and git.
   
   python site : [https://python.org](https://python.org)
   
   git site : [https://git-scm.com/](https://git-scm.com/)

2. Clone this repository
   ```shell
   git clone https://github.com/Omnividente/tonxdao.git

3. goto tonxdao-bot directory
   ```
   cd tonxdao-bot
   ```

4. install the require library
   ```
   python -m pip install -r requirements.txt
   ```

5. Edit `data.txt`, input you data token in `data.txt`, find you token in How to find. One line for one data account, if you want add you second account add in new line!

6. execute the main program 
   ```
   python bot.py
   ```


## 🌎 About Proxy

You can add your proxy list in `proxies.txt` and proxy format is like example below :

Format :

```
user:pass:host:port
```

Example :

```
user:pass:127.0.0.1:6969
```

## ⚠️ Note

- Get auth data (`query_id=... /user=...`) in the `Application` tab in DevTools.
- Auto features: Change `false` to `true` in the `config.json` file.
- Time interval: Change in settings.txt
```
interval_1=06:50-07:15
interval_2=15:45-16:10
interval_3=00:05-00:20
```




# Русский
# Tonxdao - Автоматический бот

🔗 **Реферальная ссылка**: [Tonxdao](https://t.me/tonxdao_bot?start=ref_288096037)

## 📢 Группа в Telegram

Присоединяйтесь к нашей группе в Telegram, чтобы быть в курсе событий и получать инструкции по использованию этого инструмента:

- [Канал](https://t.me/CryptoProjects_sbt)
- [Чат](https://t.me/cryptoprojectssbt)

## 🌟 Функции

| Функция | Статус | Описание |
| -------------- | ------ | ------------------------------------------ |
| Авто Check-in | Вкл./Выкл. | Ежедневный вход для получения очков и игровых билетов |
| Автоматическое выполнение задач | Вкл./Выкл. | Выполнение задач |
| Автоматический фарм | Вкл./Выкл. | Фарм очков если есть энергия |
| Временные интервалы запуска фарма


## 🧑‍🔧 Как установить в Linux
#Linux
```shell
apt install -y git python3 python3-pip
git clone https://github.com/Omnividente/tonxdao.git
cd tonxdao-bot/
python3 -m pip install -r requirements.txt --break-system-packages
```
Введите (`query_id=... /user=...`) в файл data.txt. Каждый новый токен с новой строки.



Чтобы изменить файл в bash, используйте команду `nano data.txt`

`ctrl+o` `enter` - сохранить файл.

`ctrl+x` - выйти из редактора.

Измените файл config.json по желанию.

Чтобы включить функции, установите `true`
Чтобы отключить функции, установите `false`

Чтобы изменить файл конфигурации в bash, используйте команду `nano config.json`

Добавьте временные интервалы запуска фарма по желанию.
Чтобы изменить создайте\отредактируйте файлы settings.txt
```
interval_1=06:50-07:15
interval_2=15:45-16:10
interval_3=00:05-00:20
```
## 👩‍🔧 Как установить в Windows
#Windows
1. Убедитесь, что на вашем компьютере установлены python и git.

python site : [https://python.org](https://python.org)

git site : [https://git-scm.com/](https://git-scm.com/)

2. Клонируйте этот репозиторий
```
git clone https://github.com/Omnividente/tonxdao.git
```

3. Перейдите в каталог tonxdao-bot
```
cd tonxdao-bot
```

4. Установите зависимости
```
python -m pip install -r requirements.txt
```

5. Отредактируйте `data.txt`, введите свой токен данных в `data.txt`, где найдите свой токен [query_id=... /user=..]. Одна строка для одной учетной записи данных, если вы хотите добавить вторую учетную запись, добавьте новую строку!

6. Запуск бота
```
python bot.py
```

## 🌎 О прокси

Формат:

```
http://user:pass:host:port
```

Пример:

```
user:pass:127.0.0.1:6969
```


## ⚠️ Примечание

- Получите данные аутентификации (`query_id=... /user=...`) на вкладке `Application` в DevTools.
- Автоматические функции: измените `false` на `true` в файле `config.json`.
