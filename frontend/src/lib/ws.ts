type MessageHandler = (data: unknown) => void;

export function createWSConnection(
  url: string,
  onMessage: MessageHandler,
  onStatusChange: (connected: boolean) => void,
) {
  let ws: WebSocket | null = null;
  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  let backoff = 1000;
  let shouldReconnect = true;

  function connect() {
    if (!shouldReconnect) return;

    ws = new WebSocket(url);

    ws.onopen = () => {
      backoff = 1000;
      onStatusChange(true);

      // Subscribe to all cameras by default
      ws?.send(JSON.stringify({ action: "subscribe", cameras: ["all"] }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      onStatusChange(false);
      if (shouldReconnect) {
        reconnectTimeout = setTimeout(() => {
          backoff = Math.min(backoff * 2, 30000);
          connect();
        }, backoff);
      }
    };

    ws.onerror = () => {
      ws?.close();
    };
  }

  connect();

  return {
    send: (data: unknown) => {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data));
      }
    },
    close: () => {
      shouldReconnect = false;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      ws?.close();
    },
  };
}
