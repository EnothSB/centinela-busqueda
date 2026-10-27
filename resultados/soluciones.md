# Soluciones del escenario severo

Estado inicial: `web[disco=4 -- caído] app[disco=3 -- activo] bd[disco=2 -- activo] mem_app=3 bloqueo=sí`

## BFS

Costo 13, profundidad 7, 467 nodos expandidos.

1. `rotar_logs(web)` (costo 2, acumulado 2)
2. `rotar_logs(app)` (costo 2, acumulado 4)
3. `rotar_logs(bd)` (costo 2, acumulado 6)
4. `limpiar_tmp(web)` (costo 1, acumulado 7)
5. `reiniciar_nginx` (costo 1, acumulado 8)
6. `reiniciar_app` (costo 3, acumulado 11)
7. `terminar_bloqueo` (costo 2, acumulado 13)

## DFS

Costo 14, profundidad 8, 9 nodos expandidos.

1. `rotar_logs(web)` (costo 2, acumulado 2)
2. `rotar_logs(app)` (costo 2, acumulado 4)
3. `rotar_logs(bd)` (costo 2, acumulado 6)
4. `limpiar_tmp(web)` (costo 1, acumulado 7)
5. `limpiar_tmp(app)` (costo 1, acumulado 8)
6. `reiniciar_nginx` (costo 1, acumulado 9)
7. `reiniciar_app` (costo 3, acumulado 12)
8. `terminar_bloqueo` (costo 2, acumulado 14)

## UCS

Costo 12, profundidad 7, 566 nodos expandidos.

1. `limpiar_tmp(web)` (costo 1, acumulado 1)
2. `limpiar_tmp(bd)` (costo 1, acumulado 2)
3. `reiniciar_nginx` (costo 1, acumulado 3)
4. `rotar_logs(web)` (costo 2, acumulado 5)
5. `rotar_logs(app)` (costo 2, acumulado 7)
6. `terminar_bloqueo` (costo 2, acumulado 9)
7. `reiniciar_app` (costo 3, acumulado 12)

## A*(h2)

Costo 12, profundidad 7, 7 nodos expandidos.

1. `reiniciar_app` (costo 3, acumulado 3)
2. `rotar_logs(web)` (costo 2, acumulado 5)
3. `rotar_logs(app)` (costo 2, acumulado 7)
4. `terminar_bloqueo` (costo 2, acumulado 9)
5. `limpiar_tmp(web)` (costo 1, acumulado 10)
6. `limpiar_tmp(bd)` (costo 1, acumulado 11)
7. `reiniciar_nginx` (costo 1, acumulado 12)
