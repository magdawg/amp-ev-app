# amp-ev-app

Run `docker-compose up --build` in the top level directory

Then open websockets with `ws://localhost:8765/ws/<charger_id>`

And start sending requests like 
```
{
    "messageType": "Async_Authorization", 
    "messageId": "3c", 
    "messageData": {
        "connectorId": "connector2", 
        "token": "admin2"
    }
}
```

See API docs at http://0.0.0.0:8765/docs and http://0.0.0.0:8000/docs
