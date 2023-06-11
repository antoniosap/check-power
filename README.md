ATTENZIONE:

dal 16.4.2022 col nuovo integrato home assistant,
rimane valida solo la parte check-power a 5 power meter


UTILI COMANDI:

* per docker desktop
** docker compose up -d --build
** gremlin attach check-power-app-1

* avviare su 'home assistant' con:
** docker build -t check-power .
** docker run -d --name check-power-app check-power