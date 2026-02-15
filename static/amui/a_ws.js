m_ws = {
    connectToSocket: function(canal, callback) {
        // Obtenemos la variable para escuchar el websocket
        const ws_scheme = window.location.protocol === "https:" ? "wss://" : "ws://";
        const ws_path = ws_scheme + window.location.host + '/ws/' + canal + '/';
        let socket = new WebSocket(ws_path);
    
        if (socket.readyState === WebSocket.OPEN) {
            socket.onopen();
        }
    
        // Conectamos al socket
        socket.onopen = function open() {
            log(`Conectado al socket ${canal}`);
        };
    
        // Si el socket se cierra volvemos a conectar
        socket.onclose = function close() {
            reconnectRetryQuantity--;

            if (reconnectRetryQuantity > 0) {
                // Tratamos de reconectar el socket en un tiempo determinado
                setTimeout(function () {
                    m_ws.connectToSocket(canal, callback)
                }, reconnectRetryWait);
            } else {
                // Esperamos 30 segundos para volver a intentar a conectar al socket
                setTimeout(function () {
                    reconnectRetryQuantity = 20;
                }, 30000);
            }
        };
    
        // Error del socket
        socket.onerror = function error(error) {
            console.log(error, 'ERROR:::')
            log('Error: ');
            log(error)
        };
    
        socket.onmessage = function message(event) {
            if (callback) {
                callback(JSON.parse(event.data));
            }
        };
        return socket
    }
}

